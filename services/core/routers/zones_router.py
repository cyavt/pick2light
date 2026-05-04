"""
Zones router — CRUD, devices in zone, zone status.
"""

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/")
async def list_zones():
    """List all zones."""
    # TODO: Implement
    return []


@router.post("/")
async def create_zone():
    """Create a new zone."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{zone_id}/devices")
async def list_zone_devices(zone_id: str):
    """List all devices in a zone."""
    # TODO: Implement
    return []


@router.get("/{zone_id}/status")
async def get_zone_status(zone_id: str):
    """Get zone status from Redis."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
