"""
Internal router — called only by mqtt-bridge, not exposed via Traefik.
Handles task confirmation and device heartbeat.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.models import PickingTask, PickingOrder, Device
from models.schemas import ConfirmTaskRequest

router = APIRouter()


@router.post("/tasks/confirm")
async def confirm_task(body: ConfirmTaskRequest, db: AsyncSession = Depends(get_db)):
    """
    Confirm a picking task (button pressed on device).
    1. Find active task on this device
    2. Update task status → confirmed
    3. Turn off device LED
    4. If all tasks done → auto-complete order
    Returns: { ok, task_id, order_progress, order_completed }
    """
    # Find device
    result = await db.execute(select(Device).where(Device.device_code == body.device_code))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail=f"Thiết bị '{body.device_code}' không tồn tại")

    # Find active task on this device
    result = await db.execute(
        select(PickingTask)
        .where(PickingTask.device_id == device.id, PickingTask.status == "active")
    )
    task = result.scalar_one_or_none()
    if not task:
        return {"ok": False, "message": f"Không có task active trên '{body.device_code}'"}

    # Confirm task
    task.status = "confirmed"
    task.quantity_picked = task.quantity_required
    task.confirmed_at = datetime.utcnow()

    # Turn off LED
    device.led_state = "off"

    # Check order progress
    result = await db.execute(
        select(PickingTask).where(PickingTask.order_id == task.order_id)
    )
    all_tasks = result.scalars().all()
    done = sum(1 for t in all_tasks if t.status == "confirmed")
    total = len(all_tasks)
    order_completed = done == total

    # Auto-complete order if all done
    if order_completed:
        result = await db.execute(
            select(PickingOrder).where(PickingOrder.id == task.order_id)
        )
        order = result.scalar_one_or_none()
        if order:
            order.status = "completed"
            order.completed_at = datetime.utcnow()

    return {
        "ok": True,
        "task_id": str(task.id),
        "order_id": str(task.order_id),
        "order_progress": {"done": done, "total": total, "percent": round(done / total * 100) if total else 0},
        "order_completed": order_completed,
    }


@router.post("/devices/heartbeat")
async def device_heartbeat(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Update device online status.
    Called by mqtt-bridge when receiving heartbeat from ESP32.
    """
    device_code = data.get("device_code")
    if not device_code:
        raise HTTPException(status_code=400, detail="Missing device_code")

    result = await db.execute(select(Device).where(Device.device_code == device_code))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_code}' not found")

    device.status = "online"
    device.last_seen = datetime.utcnow()

    return {"ok": True}
