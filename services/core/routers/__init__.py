from routers.devices_router import router as devices_router
from routers.zones_router import router as zones_router
from routers.orders_router import router as orders_router
from routers.reports_router import router as reports_router
from routers.internal_router import router as internal_router

__all__ = [
    "devices_router",
    "zones_router",
    "orders_router",
    "reports_router",
    "internal_router",
]
