"""
Orders router — create, activate (barcode scan), cancel, progress, list.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.models import PickingOrder, PickingTask, Device
from models.schemas import CreateOrderRequest, ActivateOrderRequest, OrderOut, TaskOut

router = APIRouter()

DEFAULT_WAREHOUSE = "00000000-0000-0000-0000-000000000001"


# ─── Helpers ─────────────────────────────────────────────────
def _order_to_dict(order: PickingOrder) -> dict:
    tasks = [
        TaskOut(
            id=str(t.id),
            device_code=t.device.device_code if t.device else "?",
            sku=t.sku,
            quantity_required=t.quantity_required,
            quantity_picked=t.quantity_picked,
            status=t.status,
        )
        for t in order.tasks
    ]
    done = sum(1 for t in tasks if t.status == "confirmed")
    total = len(tasks)
    return OrderOut(
        id=str(order.id),
        order_ref=order.order_ref,
        status=order.status,
        created_at=order.created_at.isoformat() if order.created_at else "",
        started_at=order.started_at.isoformat() if order.started_at else None,
        completed_at=order.completed_at.isoformat() if order.completed_at else None,
        tasks=tasks,
        progress={"done": done, "total": total, "percent": round(done / total * 100) if total else 0},
    ).model_dump()


async def _load_order(db: AsyncSession, order_id: str) -> PickingOrder:
    """Load order with tasks + device relationship."""
    result = await db.execute(
        select(PickingOrder)
        .options(selectinload(PickingOrder.tasks).selectinload(PickingTask.device))
        .where(PickingOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại")
    return order


# ─── POST /api/orders — ERP tạo đơn hàng ────────────────────
@router.post("/", status_code=201)
async def create_order(body: CreateOrderRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new picking order from ERP.
    Request body: { order_ref, items: [{ device_code, quantity, sku? }] }
    """
    # Check duplicate
    existing = await db.execute(
        select(PickingOrder).where(PickingOrder.order_ref == body.order_ref)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Đơn hàng '{body.order_ref}' đã tồn tại")

    # Resolve device_codes → device_ids
    device_codes = [item.device_code for item in body.items]
    result = await db.execute(select(Device).where(Device.device_code.in_(device_codes)))
    devices = {d.device_code: d for d in result.scalars().all()}

    not_found = [code for code in device_codes if code not in devices]
    if not_found:
        raise HTTPException(status_code=400, detail=f"Thiết bị không tồn tại: {', '.join(not_found)}")

    # Create order
    order = PickingOrder(
        order_ref=body.order_ref,
        warehouse_id=body.warehouse_id or DEFAULT_WAREHOUSE,
        status="pending",
    )
    db.add(order)
    await db.flush()

    # Create tasks
    for item in body.items:
        device = devices[item.device_code]
        task = PickingTask(
            order_id=order.id,
            device_id=device.id,
            sku=item.sku,
            quantity_required=item.quantity,
            status="waiting",
        )
        db.add(task)

    await db.flush()

    # Reload with relationships
    order = await _load_order(db, str(order.id))
    return _order_to_dict(order)


# ─── POST /api/orders/activate — Quét barcode kích hoạt ─────
@router.post("/activate")
async def activate_order(body: ActivateOrderRequest, db: AsyncSession = Depends(get_db)):
    """
    Activate an order by scanning its barcode (order_ref).
    Only 1 active order at a time.
    All tasks → active, devices → led_state = 'on'.
    """
    # Check if another order is already active
    active_check = await db.execute(
        select(PickingOrder).where(PickingOrder.status == "active")
    )
    active_order = active_check.scalar_one_or_none()
    if active_order:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Đang có đơn hàng '{active_order.order_ref}' đang chạy. Hoàn thành hoặc huỷ đơn trước khi kích hoạt đơn mới.",
                "active_order_ref": active_order.order_ref,
                "active_order_id": str(active_order.id),
            }
        )

    result = await db.execute(
        select(PickingOrder)
        .options(selectinload(PickingOrder.tasks).selectinload(PickingTask.device))
        .where(PickingOrder.order_ref == body.order_ref)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đơn hàng '{body.order_ref}'")

    if order.status == "active":
        raise HTTPException(status_code=400, detail="Đơn hàng đã được kích hoạt")
    if order.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Đơn hàng đã {order.status}")

    # Activate order
    order.status = "active"
    order.started_at = datetime.utcnow()

    # Activate all tasks + turn on LEDs
    activated_devices = []
    for task in order.tasks:
        if task.status == "waiting":
            task.status = "active"
        if task.device:
            task.device.led_state = "on"
            activated_devices.append(task.device.device_code)

    # TODO: Send MQTT commands to physical devices via mqtt-bridge
    # for code in activated_devices:
    #     await httpx.post(f"{settings.MQTT_BRIDGE_URL}/publish", json={...})

    order = await _load_order(db, str(order.id))
    return {
        **_order_to_dict(order),
        "activated_devices": activated_devices,
        "message": f"Đã kích hoạt {len(activated_devices)} thiết bị",
    }


# ─── GET /api/orders/active — Danh sách đơn đang xử lý ─────
@router.get("/active")
async def list_active_orders(db: AsyncSession = Depends(get_db)):
    """List all active + pending orders."""
    result = await db.execute(
        select(PickingOrder)
        .options(selectinload(PickingOrder.tasks).selectinload(PickingTask.device))
        .where(PickingOrder.status.in_(["pending", "active"]))
        .order_by(PickingOrder.created_at.desc())
    )
    orders = result.scalars().all()
    return [_order_to_dict(o) for o in orders]


# ─── GET /api/orders — All orders ────────────────────────────
@router.get("/")
async def list_orders(db: AsyncSession = Depends(get_db)):
    """List all orders (paginated in future)."""
    result = await db.execute(
        select(PickingOrder)
        .options(selectinload(PickingOrder.tasks).selectinload(PickingTask.device))
        .order_by(PickingOrder.created_at.desc())
        .limit(50)
    )
    orders = result.scalars().all()
    return [_order_to_dict(o) for o in orders]


# ─── GET /api/orders/{order_id} — Chi tiết đơn ──────────────
@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Get order details + task list."""
    order = await _load_order(db, order_id)
    return _order_to_dict(order)


# ─── POST /api/orders/{order_id}/cancel — Huỷ đơn ───────────
@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel order → turn off all LEDs."""
    order = await _load_order(db, order_id)

    if order.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Đơn hàng đã {order.status}")

    order.status = "cancelled"
    for task in order.tasks:
        if task.status in ("waiting", "active"):
            task.status = "skipped"
        if task.device:
            task.device.led_state = "off"

    return {"ok": True, "message": "Đã huỷ đơn hàng"}


# ─── GET /api/orders/{order_id}/progress ─────────────────────
@router.get("/{order_id}/progress")
async def get_order_progress(order_id: str, db: AsyncSession = Depends(get_db)):
    """Get order progress: {done, total, percent}."""
    order = await _load_order(db, order_id)
    done = sum(1 for t in order.tasks if t.status == "confirmed")
    total = len(order.tasks)
    return {
        "done": done,
        "total": total,
        "percent": round(done / total * 100) if total else 0,
    }
