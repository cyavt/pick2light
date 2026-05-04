"""
WebSocket Service — Real-time push to Vue.js dashboard
Port: 8003
"""

import json
from contextlib import asynccontextmanager
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="PTL WebSocket Service",
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ─── Connection Manager ─────────────────────────────────────

class ConnectionManager:
    """Manages WebSocket connections by channel."""

    def __init__(self):
        # channel → set of websocket connections
        self.channels: Dict[str, Set[WebSocket]] = {
            "dashboard": set(),
        }

    async def connect(self, websocket: WebSocket, channel: str = "dashboard"):
        await websocket.accept()
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "dashboard"):
        if channel in self.channels:
            self.channels[channel].discard(websocket)

    async def broadcast(self, channel: str, message: dict):
        """Send message to all connections in a channel."""
        if channel not in self.channels:
            return
        disconnected = []
        for ws in self.channels[channel]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.channels[channel].discard(ws)

    async def broadcast_all(self, message: dict):
        """Send message to all channels."""
        for channel in self.channels:
            await self.broadcast(channel, message)


manager = ConnectionManager()


# ─── WebSocket Endpoints ─────────────────────────────────────

@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """Dashboard — all device updates."""
    await manager.connect(websocket, "dashboard")
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, "dashboard")


@app.websocket("/ws/zone/{zone_id}")
async def ws_zone(websocket: WebSocket, zone_id: str):
    """Track a specific zone."""
    channel = f"zone:{zone_id}"
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@app.websocket("/ws/order/{order_id}")
async def ws_order(websocket: WebSocket, order_id: str):
    """Track a specific order progress."""
    channel = f"order:{order_id}"
    await manager.connect(websocket, channel)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


# ─── Internal HTTP Endpoint (called by mqtt-bridge) ──────────

@app.post("/internal/broadcast")
async def internal_broadcast(data: dict):
    """
    Receive update from mqtt-bridge and broadcast to connected clients.
    mqtt-bridge calls this via HTTP internal (same Docker network).
    """
    # Broadcast to dashboard channel
    await manager.broadcast("dashboard", data)

    # Broadcast to specific zone/order channels if applicable
    if "zone_id" in data:
        await manager.broadcast(f"zone:{data['zone_id']}", data)
    if "order_id" in data:
        await manager.broadcast(f"order:{data['order_id']}", data)

    return {"status": "ok", "message": "Broadcast sent"}


@app.get("/health")
async def health():
    total_connections = sum(len(conns) for conns in manager.channels.values())
    return {
        "status": "ok",
        "service": "ws-service",
        "active_connections": total_connections,
    }
