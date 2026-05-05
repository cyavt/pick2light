"""
Zones router — CRUD, devices in zone, zone status.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.models import Zone, Device, Warehouse

router = APIRouter()

DEFAULT_WAREHOUSE = "00000000-0000-0000-0000-000000000001"


class CreateZoneRequest(BaseModel):
    name: str
    slug: str           # "zone-a" — used in MQTT topics
    description: str = ""


class UpdateZoneRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None


@router.get("/")
async def list_zones(db: AsyncSession = Depends(get_db)):
    """List all zones with device counts."""
    result = await db.execute(
        select(Zone)
        .options(selectinload(Zone.devices))
        .order_by(Zone.name)
    )
    zones = result.scalars().all()

    return [
        {
            "id": str(z.id),
            "name": z.name,
            "slug": z.slug,
            "description": z.description,
            "total_devices": len(z.devices),
            "devices_online": sum(1 for d in z.devices if d.status == "online"),
            "devices_offline": sum(1 for d in z.devices if d.status == "offline"),
            "created_at": z.created_at.isoformat() if z.created_at else None,
        }
        for z in zones
    ]


@router.post("/", status_code=201)
async def create_zone(body: CreateZoneRequest, db: AsyncSession = Depends(get_db)):
    """Create a new zone."""
    # Check slug uniqueness
    existing = await db.execute(select(Zone).where(Zone.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Mã zone '{body.slug}' đã tồn tại")

    zone = Zone(
        warehouse_id=DEFAULT_WAREHOUSE,
        name=body.name,
        slug=body.slug,
        description=body.description,
    )
    db.add(zone)
    await db.flush()

    return {
        "id": str(zone.id),
        "name": zone.name,
        "slug": zone.slug,
        "description": zone.description,
    }


@router.put("/{zone_id}")
async def update_zone(zone_id: str, body: UpdateZoneRequest, db: AsyncSession = Depends(get_db)):
    """Update a zone."""
    result = await db.execute(select(Zone).where(Zone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone không tồn tại")

    if body.name is not None:
        zone.name = body.name
    if body.slug is not None:
        # Check uniqueness
        existing = await db.execute(select(Zone).where(Zone.slug == body.slug, Zone.id != zone_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Mã zone '{body.slug}' đã tồn tại")
        zone.slug = body.slug
    if body.description is not None:
        zone.description = body.description

    return {
        "id": str(zone.id),
        "name": zone.name,
        "slug": zone.slug,
        "description": zone.description,
    }


@router.delete("/{zone_id}")
async def delete_zone(zone_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a zone (and all its devices)."""
    result = await db.execute(
        select(Zone).options(selectinload(Zone.devices)).where(Zone.id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone không tồn tại")

    if len(zone.devices) > 0:
        raise HTTPException(status_code=400, detail=f"Zone còn {len(zone.devices)} thiết bị, không thể xoá")

    await db.delete(zone)
    return {"ok": True, "message": f"Đã xoá zone '{zone.name}'"}
