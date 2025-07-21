import json
import logging
import redis

from app.config import settings

logging.basicConfig(level=logging.INFO)

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    db=int(settings.REDIS_DB)
)

def publish_event(event_type: str, payload: dict):
    event_data = json.dumps(payload)
    stream_name = f"outbox:{event_type}"

    # Publish to Redis Stream
    redis_client.xadd(stream_name, {"data": event_data})

    logging.info(f"Published event '{event_type}' to stream '{stream_name}': {event_data}")