import logging
from contextlib import contextmanager

import redis
from redis.exceptions import ResponseError
import time

from app.db.session import SessionLocal
from app.models.external_identifier import ExternalIdentifier
from app.config import settings

STREAM = "outbox:ExternalIdentifierCreated"
GROUP = "external_identifier_reader"
CONSUMER_NAME = "rolodex-data-product-consumer"

logging.basicConfig(level=logging.INFO)

# Use synchronous client
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    db=int(settings.REDIS_DB)
)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def consume_external_identifiers():
    try:
        redis_client.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
        logging.info(f"Consumer group '{GROUP}' created on stream '{STREAM}'")
    except ResponseError as e:
        if 'BUSYGROUP' in str(e):
            logging.info(f"Consumer group '{GROUP}' already exists")
        else:
            logging.warning(f"Error creating consumer group: {e}")

    logging.info("Starting external identifier consumer...")

    while True:
        logging.info("Checking for new external identifier events...")
        try:
            entries = redis_client.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM: '>'},
                count=10,
                block=5000
            )
        except ResponseError as e:
            if 'NOGROUP' in str(e):
                logging.warning(f"Consumer group '{GROUP}' missing, recreating...")
                try:
                    redis_client.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
                except ResponseError:
                    pass
                continue
            else:
                logging.error(f"Error reading from stream: {e}")
                time.sleep(1)
                continue

        if not entries:
            time.sleep(0.1)
            continue

        for stream_name, events in entries:
            for event_id, event_data in events:
                try:
                    payload = {k.decode(): v.decode() for k, v in event_data.items()}
                    party_id = int(payload["party_id"])
                    system_name = payload["system_name"]
                    external_id = payload["external_id"]

                    with get_db() as db:
                        external_identifier = (
                            db.query(ExternalIdentifier)
                            .filter_by(party_id=party_id, system_name=system_name)
                            .one_or_none()
                        )

                        if external_identifier:
                            external_identifier.external_id = external_id
                            logging.info(f"Updated external identifier for party_id={party_id}, system={system_name}")
                        else:
                            external_identifier = ExternalIdentifier(
                                party_id=party_id,
                                system_name=system_name,
                                external_id=external_id
                            )
                            db.add(external_identifier)
                            logging.info(f"Created new external identifier for party_id={party_id}, system={system_name}")

                        db.commit()

                    redis_client.xack(STREAM, GROUP, event_id)

                except Exception as e:
                    logging.error(f"Error processing external identifier event {event_id}: {e}")