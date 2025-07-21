import json
import logging
import redis

logging.basicConfig(level=logging.INFO)
redis_client = redis.Redis(host='localhost', port=6379, db=0)


def publish_event(event_type: str, payload: dict):
    event_data = json.dumps(payload)
    stream_name = f"outbox:{event_type}"

    # Publish to Redis Stream
    redis_client.xadd(stream_name, {"data": event_data})

    logging.info(f"Published event '{event_type}' to stream '{stream_name}': {event_data}")