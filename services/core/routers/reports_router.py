"""
Reports router — daily stats, device history.
"""

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.get("/daily")
async def daily_report():
    """Daily picking statistics."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/device/{device_id}")
async def device_history(device_id: str):
    """Activity history for a specific device."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
