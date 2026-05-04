"""
Order service — business logic for picking orders.
"""


class OrderService:
    """Handles order creation, starting, cancellation, and progress tracking."""

    async def create_order(self, db, order_data: dict):
        """Create a new picking order with tasks."""
        # TODO: Implement
        pass

    async def start_order(self, db, order_id: str):
        """
        Start an order:
        1. Update status → active
        2. Collect device list for LED commands
        3. Call mqtt-bridge to send commands
        """
        # TODO: Implement
        pass

    async def cancel_order(self, db, order_id: str):
        """Cancel an order and turn off all LEDs."""
        # TODO: Implement
        pass

    async def get_progress(self, db, order_id: str) -> dict:
        """Get order progress: {done, total, percent}."""
        # TODO: Implement
        return {"done": 0, "total": 0, "percent": 0}

    async def confirm_task(self, db, task_id: str):
        """
        Confirm a task:
        1. Update task → confirmed
        2. Calculate progress
        3. Auto-complete order if all done
        """
        # TODO: Implement
        pass


order_service = OrderService()
