"""
MQTT Bridge — MQTT ↔ System bridge
Port: 8004

Subscribes to device events/status, forwards to core-api and ws-service.
Publishes commands to devices via EMQX.
"""

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from handlers.device_event_handler import handle_device_event
from handlers.device_status_handler import handle_device_status

# MQTT client will be initialized on startup
mqtt_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to MQTT broker and subscribe
    global mqtt_task
    mqtt_task = asyncio.create_task(mqtt_listener())
    yield
    # Shutdown
    if mqtt_task:
        mqtt_task.cancel()


app = FastAPI(
    title="PTL MQTT Bridge",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


async def mqtt_listener():
    """
    Main MQTT listener loop.
    Subscribes to all device event and status topics.
    """
    import aiomqtt

    while True:
        try:
            async with aiomqtt.Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
            ) as client:
                # Subscribe to all device events and status
                await client.subscribe("ptl/device/+/+/event")
                await client.subscribe("ptl/device/+/+/status")

                async for message in client.messages:
                    topic = str(message.topic)
                    payload = json.loads(message.payload)

                    if "/event" in topic:
                        await handle_device_event(topic, payload)
                    elif "/status" in topic:
                        await handle_device_status(topic, payload)

        except Exception as e:
            print(f"MQTT connection error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)


# ─── Internal HTTP Endpoints (called by core-api) ────────────

@app.post("/internal/send-commands")
async def send_commands(data: dict):
    """
    Receive LED commands from core-api and publish to MQTT.
    data: { commands: [{ zone_id, device_id, action, color, quantity, task_id }] }
    """
    import aiomqtt

    async with aiomqtt.Client(
        hostname=settings.MQTT_BROKER,
        port=settings.MQTT_PORT,
    ) as client:
        for cmd in data.get("commands", []):
            topic = f"ptl/device/{cmd['zone_id']}/{cmd['device_id']}/cmd"
            payload = json.dumps({
                "action": cmd.get("action", "led_on"),
                "color": cmd.get("color", "#00FF00"),
                "brightness": cmd.get("brightness", 80),
                "quantity": cmd.get("quantity", 0),
                "task_id": cmd.get("task_id", ""),
            })
            await client.publish(topic, payload)

    return {"status": "ok", "commands_sent": len(data.get("commands", []))}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "mqtt-bridge"}
