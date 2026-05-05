"""
Handler for device events (button_pressed, etc.)
Forwards to core-api for business logic, then pushes to ws-service.
"""

import json
import logging

import httpx

from config import settings

log = logging.getLogger("mqtt-bridge")


async def handle_device_event(topic: str, payload: dict):
    """
    Handle device event messages.

    Flow:
    1. Gọi core-api /internal/tasks/confirm
    2. Tắt đèn qua MQTT
    3. Push dashboard qua ws-service
    """
    if payload.get("event") != "button_pressed":
        log.debug(f"Ignoring event: {payload.get('event')}")
        return

    device_id = payload.get("device_id", "")
    task_id = payload.get("task_id", "")
    log.info(f"Button pressed: device={device_id}, task={task_id}")

    # Extract device_id from topic
    # Topic format: ptl/device/{device_id}/event
    parts = topic.split("/")
    topic_device_id = parts[2]

    try:
        # 1. Call core-api to confirm task (business logic)
        async with httpx.AsyncClient(timeout=5) as client:
            result = await client.post(
                f"{settings.CORE_API_URL}/internal/tasks/confirm",
                json={
                    "device_code": device_id,  # Schema expects device_code
                },
            )
            data = result.json()
            log.info(f"Core-api confirm result: {data}")

        if not data.get("ok"):
            log.warning(f"Task confirm failed: {data}")
            return

        # 2. Turn off LED via MQTT
        import aiomqtt

        async with aiomqtt.Client(
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            username=settings.MQTT_USERNAME or None,
            password=settings.MQTT_PASSWORD or None,
        ) as mqtt_client:
            off_topic = f"ptl/device/{topic_device_id}/cmd"
            await mqtt_client.publish(
                off_topic,
                json.dumps({"action": "led_off"}),
            )
            log.info(f"LED off → {off_topic}")

        # 3. Push to dashboard via ws-service
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{settings.WS_SERVICE_URL}/internal/broadcast",
                json=data,
            )
            log.info("Dashboard notified")

    except Exception as e:
        log.error(f"Error handling button_pressed: {e}")
