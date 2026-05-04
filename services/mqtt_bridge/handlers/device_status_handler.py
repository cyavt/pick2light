"""
Handler for device status messages (heartbeat, online/offline).
Updates device state in Redis with TTL.
"""

import json

import redis.asyncio as redis

from config import settings


async def handle_device_status(topic: str, payload: dict):
    """
    Handle device status/heartbeat messages.
    Update last_seen in Redis with 60s TTL.
    """
    device_id = payload.get("device_id", "")

    if payload.get("event") == "heartbeat":
        r = redis.from_url(settings.REDIS_URL)
        try:
            await r.setex(
                f"device:state:{device_id}",
                60,  # TTL 60 seconds
                json.dumps({
                    "status": "online",
                    "ts": payload.get("timestamp"),
                }),
            )
        finally:
            await r.aclose()
