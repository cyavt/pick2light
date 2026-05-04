"""
Pydantic schemas for Core API request/response models.
"""

from pydantic import BaseModel


# ─── Orders ──────────────────────────────────────────────────
class OrderItemIn(BaseModel):
    """Single item in an order — from ERP."""
    device_code: str
    quantity: int
    sku: str | None = None


class CreateOrderRequest(BaseModel):
    """Create a new picking order (from ERP or manual)."""
    order_ref: str
    warehouse_id: str | None = None
    items: list[OrderItemIn]


class ActivateOrderRequest(BaseModel):
    """Activate an order by scanning its barcode."""
    order_ref: str


# ─── Tasks ───────────────────────────────────────────────────
class TaskOut(BaseModel):
    id: str
    device_code: str
    sku: str | None
    quantity_required: int
    quantity_picked: int
    status: str

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: str
    order_ref: str
    status: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    tasks: list[TaskOut] = []
    progress: dict | None = None  # {done, total, percent}


# ─── Confirm ─────────────────────────────────────────────────
class ConfirmTaskRequest(BaseModel):
    """From mqtt-bridge when device button is pressed."""
    device_code: str
