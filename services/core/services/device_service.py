"""
Device service — business logic for device management.
"""


class DeviceService:
    """Handles device CRUD, status updates, and LED control."""

    async def list_devices(self, db, zone_id: str = None, status: str = None):
        """List devices with optional filters."""
        # TODO: Implement
        return []

    async def get_device(self, db, device_id: str):
        """Get device details with live state from Redis."""
        # TODO: Implement
        pass

    async def create_device(self, db, device_data: dict):
        """Register a new device."""
        # TODO: Implement
        pass

    async def update_config(self, db, device_id: str, config: dict):
        """Update device configuration."""
        # TODO: Implement
        pass

    async def test_led(self, device_id: str):
        """Send test LED command via mqtt-bridge."""
        # TODO: Implement
        pass

    async def update_heartbeat(self, redis, device_id: str, timestamp: int):
        """Update device last_seen in Redis with 60s TTL."""
        # TODO: Implement
        pass


device_service = DeviceService()
