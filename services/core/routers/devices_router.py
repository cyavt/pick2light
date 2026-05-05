"""
Devices router — CRUD, list, test LED.
"""

import logging

import httpx
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import get_db
from models.models import Device, Zone, PickingTask

router = APIRouter()
log = logging.getLogger("devices")


class CreateDeviceRequest(BaseModel):
    device_code: str
    location: str = ""


class UpdateDeviceRequest(BaseModel):
    device_code: str | None = None
    location: str | None = None




@router.get("/")
async def list_devices(zone_id: str = None, status_filter: str = None, db: AsyncSession = Depends(get_db)):
    """List all devices with optional filters (zone, status)."""
    query = select(Device).options(selectinload(Device.zone))

    if zone_id:
        query = query.where(Device.zone_id == zone_id)
    if status_filter:
        query = query.where(Device.status == status_filter)

    query = query.order_by(Device.device_code)
    result = await db.execute(query)
    devices = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "device_code": d.device_code,
            "zone": d.zone.name if d.zone else None,
            "zone_id": str(d.zone_id) if d.zone_id else None,
            "location": d.location,
            "status": d.status,
            "led_state": d.led_state,
            "led_color": d.led_color,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ]


@router.get("/offline")
async def list_offline_devices(db: AsyncSession = Depends(get_db)):
    """List all offline devices."""
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.zone))
        .where(Device.status == "offline")
        .order_by(Device.device_code)
    )
    devices = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "device_code": d.device_code,
            "zone": d.zone.name if d.zone else None,
            "location": d.location,
        }
        for d in devices
    ]


@router.get("/{device_id}")
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    """Get device details."""
    result = await db.execute(
        select(Device).options(selectinload(Device.zone)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")
    return {
        "id": str(device.id),
        "device_code": device.device_code,
        "zone": device.zone.name if device.zone else None,
        "location": device.location,
        "status": device.status,
        "led_state": device.led_state,
        "led_color": device.led_color,
        "config": device.config,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
    }


@router.post("/", status_code=201)
async def create_device(body: CreateDeviceRequest, db: AsyncSession = Depends(get_db)):
    """Create a new device."""
    # Check unique device_code
    existing = await db.execute(select(Device).where(Device.device_code == body.device_code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Mã thiết bị '{body.device_code}' đã tồn tại")

    device = Device(
        device_code=body.device_code,
        location=body.location,
        status="offline",
    )
    db.add(device)
    await db.flush()

    return {
        "id": str(device.id),
        "device_code": device.device_code,
        "location": device.location,
        "status": device.status,
    }


@router.put("/{device_id}")
async def update_device(device_id: str, body: UpdateDeviceRequest, db: AsyncSession = Depends(get_db)):
    """Update a device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")

    if body.device_code is not None and body.device_code != device.device_code:
        existing = await db.execute(select(Device).where(Device.device_code == body.device_code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Mã thiết bị '{body.device_code}' đã tồn tại")
        device.device_code = body.device_code

    if body.location is not None:
        device.location = body.location

    return {
        "id": str(device.id),
        "device_code": device.device_code,
        "location": device.location,
        "status": device.status,
    }


@router.delete("/{device_id}")
async def delete_device(device_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a device (only if no active tasks)."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")

    # Check active tasks
    active_tasks = await db.execute(
        select(PickingTask).where(
            PickingTask.device_id == device.id,
            PickingTask.status.in_(["waiting", "active"]),
        )
    )
    if active_tasks.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Thiết bị đang có task hoạt động, không thể xoá")

    await db.delete(device)
    return {"ok": True, "message": f"Đã xoá thiết bị '{device.device_code}'"}


@router.post("/{device_id}/test-led")
async def test_led(device_id: str, body: dict = None, db: AsyncSession = Depends(get_db)):
    """
    Send test LED command to a device.
    Optional body: { color: "#FF0000", duration: 3 }
    Sends led_on then led_off after duration seconds.
    """
    result = await db.execute(
        select(Device).options(selectinload(Device.zone)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Thiết bị không tồn tại")

    color = (body or {}).get("color", "#00FF00")
    duration = (body or {}).get("duration", 3)

    # Send led_on command
    commands = [
        {
            "device_id": device.device_code,
            "action": "led_on",
            "color": color,
            "quantity": 0,
            "task_id": "test",
        }
    ]

    try:
        import asyncio
        async with httpx.AsyncClient(timeout=5) as client:
            # LED ON
            await client.post(
                f"{settings.MQTT_BRIDGE_URL}/internal/send-commands",
                json={"commands": commands},
            )
            log.info(f"Test LED ON → {device.device_code}")

            # Wait
            await asyncio.sleep(duration)

            # LED OFF
            commands[0]["action"] = "led_off"
            await client.post(
                f"{settings.MQTT_BRIDGE_URL}/internal/send-commands",
                json={"commands": commands},
            )
            log.info(f"Test LED OFF → {device.device_code}")

    except Exception as e:
        log.error(f"Test LED failed: {e}")
        raise HTTPException(status_code=500, detail=f"Gửi lệnh test thất bại: {e}")

    return {"ok": True, "message": f"Test LED {device.device_code} — {color} ({duration}s)"}
