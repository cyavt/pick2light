"""
Auth Service — JWT, User, Role, Permission
Port: 8001
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import auth_router, users_router
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev only, use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="PTL Auth Service",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Prometheus metrics ──────────────────────────────────────
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ─── Routers ─────────────────────────────────────────────────
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/auth/users", tags=["Users"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "auth-service"}
