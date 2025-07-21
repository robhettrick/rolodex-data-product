import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from threading import Thread

import yaml
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse

from app.db.session import SessionLocal, engine, Base
from app.models.outbox_event import OutboxEvent
from app.routes import auth
from app.services.event_publisher import publish_event


from app.api.v1.endpoints import (
    parties,
    persons,
    organisations,
    addresses,
    party_addresses,
    party_relationships,
    external_identifiers
)

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start external identifier consumer thread
    def run_consumer():
        import asyncio
        from app.services.external_identifier_consumer import consume_external_identifiers
        asyncio.run(consume_external_identifiers())
    Thread(target=run_consumer, daemon=True).start()
    logging.info("Started external identifier consumer thread")

    stop_event = asyncio.Event()

    async def process_outbox():
        while not stop_event.is_set():
            await asyncio.sleep(5)
            logging.info("Checking outbox for new events...")
            db = SessionLocal()
            try:
                unprocessed_events = (
                    db.query(OutboxEvent)
                    .filter(OutboxEvent.processed_at.is_(None))
                    .order_by(OutboxEvent.created_at)
                    .all()
                )

                for event in unprocessed_events:
                    publish_event(event.event_type, event.payload)
                    event.processed_at = datetime.utcnow()
                    db.commit()

            except Exception as e:
                logging.error(f"Error processing outbox: {e}")
            finally:
                db.close()

    task = asyncio.create_task(process_outbox())
    yield
    stop_event.set()
    await task

app = FastAPI(
    title="Rolodex Data Product API",
    lifespan=lifespan,
    description="API for Rolodex Data Product prototype",
    version="0.3.0"
)

# Add auth route
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# Include API endpoints
app.include_router(parties.router, prefix="/parties", tags=["Parties"])
app.include_router(persons.router, prefix="/persons", tags=["Persons"])
app.include_router(organisations.router, prefix="/organisations", tags=["Organisations"])
app.include_router(addresses.router, prefix="/addresses", tags=["Addresses"])
app.include_router(party_addresses.router, prefix="/party-addresses", tags=["Party Addresses"])
app.include_router(party_relationships.router, prefix="/party-relationships", tags=["Party Relationships"])
app.include_router(external_identifiers.router, prefix="/external-identifiers", tags=["External Identifiers"])

@app.get("/openapi.yaml", include_in_schema=False)
async def openapi_yaml():
    """
    Serve the OpenAPI schema in YAML format.
    """
    # Generate the base OpenAPI schema as a Python dict
    openapi_dict = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    # Dump to YAML
    openapi_yaml = yaml.safe_dump(openapi_dict, sort_keys=False)
    # Return as plain text with the correct media type
    return PlainTextResponse(openapi_yaml, media_type="application/x-yaml")