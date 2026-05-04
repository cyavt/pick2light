"""
Core API — Orders, Devices, Zones, Picking Logic
Port: 8002
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import devices_router, zones_router, orders_router, reports_router, internal_router
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="PTL Core API",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Prometheus metrics ──────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ─── Public Routers (qua Traefik) ────────────────────────────
app.include_router(devices_router, prefix="/api/devices", tags=["Devices"])
app.include_router(zones_router, prefix="/api/zones", tags=["Zones"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])

# ─── Internal Routers (chỉ gọi từ mqtt-bridge) ──────────────
app.include_router(internal_router, prefix="/internal", tags=["Internal"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "core-api"}
