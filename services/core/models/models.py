"""
Data models for core-api.
"""

from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    zones = relationship("Zone", back_populates="warehouse", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # "zone-a" — used in MQTT topics
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    warehouse = relationship("Warehouse", back_populates="zones")
    devices = relationship("Device", back_populates="zone", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    device_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    zone_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("zones.id"))
    location: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "A/Row2/Slot05"
    status: Mapped[str] = mapped_column(String(20), default="offline")  # online | offline
    led_state: Mapped[str] = mapped_column(String(20), default="off")  # on | off | blink
    led_color: Mapped[str] = mapped_column(String(10), default="#00FF00")
    config: Mapped[dict] = mapped_column(JSONB, default={})
    last_seen: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    zone = relationship("Zone", back_populates="devices")


class PickingOrder(Base):
    __tablename__ = "picking_orders"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_ref: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | active | completed | cancelled
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    tasks = relationship("PickingTask", back_populates="order", cascade="all, delete-orphan")


class PickingTask(Base):
    __tablename__ = "picking_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("picking_orders.id", ondelete="CASCADE"))
    device_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("devices.id"))
    sku: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_picked: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting | active | confirmed | skipped
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    confirmed_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Relationships
    order = relationship("PickingOrder", back_populates="tasks")
    device = relationship("Device")
