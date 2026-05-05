-- =====================================================
-- Pick-to-Light System — Initial Database Schema
-- =====================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Warehouses
CREATE TABLE IF NOT EXISTS warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Zones
CREATE TABLE IF NOT EXISTS zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'supervisor', 'picker')),
    warehouse_id UUID REFERENCES warehouses(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Devices
CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_code VARCHAR(20) UNIQUE NOT NULL,
    zone_id UUID REFERENCES zones(id),
    location VARCHAR(50),
    status VARCHAR(20) DEFAULT 'offline',
    led_state VARCHAR(20) DEFAULT 'off',
    led_color VARCHAR(10) DEFAULT '#00FF00',
    config JSONB DEFAULT '{}',
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_devices_zone   ON devices(zone_id);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status) WHERE status = 'online';
CREATE INDEX IF NOT EXISTS idx_devices_led    ON devices(led_state) WHERE led_state != 'off';

-- Picking Orders
CREATE TABLE IF NOT EXISTS picking_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_ref VARCHAR(50) UNIQUE NOT NULL,
    warehouse_id UUID REFERENCES warehouses(id),
    status VARCHAR(20) DEFAULT 'pending'
        CHECK (status IN ('pending', 'active', 'completed', 'cancelled')),
    created_by UUID REFERENCES users(id),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_status    ON picking_orders(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_orders_warehouse ON picking_orders(warehouse_id);

-- Picking Tasks
CREATE TABLE IF NOT EXISTS picking_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES picking_orders(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id),
    sku VARCHAR(50),
    quantity_required INT NOT NULL,
    quantity_picked INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'waiting'
        CHECK (status IN ('waiting', 'active', 'confirmed', 'skipped')),
    confirmed_at TIMESTAMPTZ,
    confirmed_by UUID REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_order  ON picking_tasks(order_id);
CREATE INDEX IF NOT EXISTS idx_tasks_device ON picking_tasks(device_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON picking_tasks(status)
    WHERE status IN ('active', 'waiting');

-- =====================================================
-- Seed Data (optional, for development)
-- =====================================================

-- Default warehouse
INSERT INTO warehouses (id, name, address)
VALUES ('00000000-0000-0000-0000-000000000001', 'Kho Chính', 'Hà Nội, Việt Nam')
ON CONFLICT DO NOTHING;

-- Default zones (A-E)
INSERT INTO zones (id, warehouse_id, name, slug, description) VALUES
    ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'Zone A', 'zone-a', 'Khu vực A - Hàng tiêu dùng'),
    ('00000000-0000-0000-0000-000000000020', '00000000-0000-0000-0000-000000000001', 'Zone B', 'zone-b', 'Khu vực B - Điện tử'),
    ('00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0000-000000000001', 'Zone C', 'zone-c', 'Khu vực C - Thực phẩm'),
    ('00000000-0000-0000-0000-000000000040', '00000000-0000-0000-0000-000000000001', 'Zone D', 'zone-d', 'Khu vực D - Văn phòng phẩm'),
    ('00000000-0000-0000-0000-000000000050', '00000000-0000-0000-0000-000000000001', 'Zone E', 'zone-e', 'Khu vực E - Phụ kiện')
ON CONFLICT DO NOTHING;

-- Default devices (4 per zone = 20 total)
INSERT INTO devices (device_code, zone_id, location, status) VALUES
    ('PTL-A001', '00000000-0000-0000-0000-000000000010', 'A/Row1/Slot01', 'online'),
    ('PTL-A002', '00000000-0000-0000-0000-000000000010', 'A/Row1/Slot02', 'online'),
    ('PTL-A003', '00000000-0000-0000-0000-000000000010', 'A/Row1/Slot03', 'online'),
    ('PTL-A004', '00000000-0000-0000-0000-000000000010', 'A/Row1/Slot04', 'online'),
    ('PTL-B001', '00000000-0000-0000-0000-000000000020', 'B/Row1/Slot01', 'online'),
    ('PTL-B002', '00000000-0000-0000-0000-000000000020', 'B/Row1/Slot02', 'online'),
    ('PTL-B003', '00000000-0000-0000-0000-000000000020', 'B/Row1/Slot03', 'online'),
    ('PTL-B004', '00000000-0000-0000-0000-000000000020', 'B/Row1/Slot04', 'online'),
    ('PTL-C001', '00000000-0000-0000-0000-000000000030', 'C/Row1/Slot01', 'online'),
    ('PTL-C002', '00000000-0000-0000-0000-000000000030', 'C/Row1/Slot02', 'online'),
    ('PTL-C003', '00000000-0000-0000-0000-000000000030', 'C/Row1/Slot03', 'online'),
    ('PTL-C004', '00000000-0000-0000-0000-000000000030', 'C/Row1/Slot04', 'online'),
    ('PTL-D001', '00000000-0000-0000-0000-000000000040', 'D/Row1/Slot01', 'online'),
    ('PTL-D002', '00000000-0000-0000-0000-000000000040', 'D/Row1/Slot02', 'online'),
    ('PTL-D003', '00000000-0000-0000-0000-000000000040', 'D/Row1/Slot03', 'online'),
    ('PTL-D004', '00000000-0000-0000-0000-000000000040', 'D/Row1/Slot04', 'online'),
    ('PTL-E001', '00000000-0000-0000-0000-000000000050', 'E/Row1/Slot01', 'online'),
    ('PTL-E002', '00000000-0000-0000-0000-000000000050', 'E/Row1/Slot02', 'online'),
    ('PTL-E003', '00000000-0000-0000-0000-000000000050', 'E/Row1/Slot03', 'online'),
    ('PTL-E004', '00000000-0000-0000-0000-000000000050', 'E/Row1/Slot04', 'online')
ON CONFLICT DO NOTHING;

-- Default admin user (password: admin123 — change in production!)
INSERT INTO users (id, username, password_hash, role, warehouse_id)
VALUES (
    '00000000-0000-0000-0000-000000000100',
    'admin',
    '$2b$12$qhY2k1z00JwQNcnR141XXujfMVtpzhKBobwksOqbvzk3tZ.2imgJC',
    'admin',
    '00000000-0000-0000-0000-000000000001'
)
ON CONFLICT DO NOTHING;
