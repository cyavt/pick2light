"""
Handler for device events (button_pressed, etc.)
Forwards to core-api for business logic, then pushes to ws-service.
"""

import json

import httpx

from config import settings


async def handle_device_event(topic: str, payload: dict):
    """
    Handle device event messages.

    Flow:
    1. Gọi core-api /internal/tasks/confirm
    2. Tắt đèn qua MQTT
    3. Push dashboard qua ws-service
    """
    if payload.get("event") == "button_pressed":
        # 1. Call core-api to confirm task (business logic)
        async with httpx.AsyncClient() as client:
            result = await client.post(
                f"{settings.CORE_API_URL}/internal/tasks/confirm",
                json={
                    "task_id": payload.get("task_id"),
                    "device_id": payload.get("device_id"),
                },
            )
            data = result.json()

        # 2. Turn off LED via MQTT
        # Extract zone_id and device_id from topic
        # Topic format: ptl/device/{zone_id}/{device_id}/event
        parts = topic.split("/")
        zone_id = parts[2]
        device_id = parts[3]

        import aiomqtt

        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
        ) as mqtt_client:
            await mqtt_client.publish(
                f"ptl/device/{zone_id}/{device_id}/cmd",
                json.dumps({"action": "led_off"}),
            )

        # 3. Push to dashboard via ws-service
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.WS_SERVICE_URL}/internal/broadcast",
                json=data,
            )
