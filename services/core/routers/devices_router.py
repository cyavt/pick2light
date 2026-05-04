"""
Devices router — CRUD, list, test LED.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.models import Device, Zone

router = APIRouter()


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
