# 🏭 Pick-to-Light System

> Hệ thống quản lý 1000 thiết bị real-time — Production Ready

---

## 🚀 Quick Start (Development)

### 1. Yêu cầu

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Docker Compose](https://docs.docker.com/compose/) (v2+)

### 2. Khởi chạy

```bash
# Clone và vào thư mục dự án
cd Pick-to-light

# Khởi chạy toàn bộ (lần đầu sẽ build, mất ~2-3 phút)
docker compose -f docker-compose.dev.yml up -d

# Xem trạng thái
docker compose -f docker-compose.dev.yml ps
```

### 3. Truy cập

| Service              | Port  | URL                                 | Mô tả                            |
| -------------------- | ----- | ----------------------------------- | --------------------------------- |
| **Frontend**         | 3000  | http://localhost:3000               | Vue.js Dashboard — proxy `/api` → :8002, `/auth` → :8001, `/ws` → :8003 |
| **Core API**         | 8002  | http://localhost:8002/docs          | Swagger UI — Business API         |
| **Auth API**         | 8001  | http://localhost:8001/docs          | Swagger UI — Auth API             |
| **WS Service**       | 8003  | ws://localhost:8003/ws/dashboard    | WebSocket real-time               |
| **MQTT Bridge**      | 8004  | http://localhost:8004/docs          | Swagger UI — MQTT Bridge          |
| **EMQX Dashboard**   | 18083 | http://localhost:18083              | MQTT Broker UI (admin/admin123)   |
| **EMQX MQTT**        | 1883  | mqtt://localhost:1883               | MQTT broker endpoint              |
| **EMQX MQTT-WS**     | 8083  | ws://localhost:8083/mqtt            | MQTT over WebSocket               |
| **PostgreSQL**       | 5432  | localhost:5432                      | DB (ptl / devpass123 / ptl_db)    |
| **Redis**            | 6379  | localhost:6379                      | Cache (no password in dev)        |

### 4. Xem logs

```bash
# Tất cả services
docker compose -f docker-compose.dev.yml logs -f

# Chỉ 1 service
docker compose -f docker-compose.dev.yml logs -f core-api

# Nhiều service
docker compose -f docker-compose.dev.yml logs -f core-api mqtt-bridge ws-service
```

### 5. Hot Reload

Tất cả Python services đều chạy với `--reload`. Chỉ cần **sửa code → save → tự động reload**.

Frontend chạy Vite dev server, cũng **hot-reload** tự động.

### 6. Dừng / Xóa

```bash
# Dừng (giữ data)
docker compose -f docker-compose.dev.yml down

# Dừng + xóa data (reset toàn bộ database)
docker compose -f docker-compose.dev.yml down -v
```

---

## 🔧 Lệnh hữu ích

```bash
# Rebuild sau khi thêm dependency mới vào requirements.txt
docker compose -f docker-compose.dev.yml up -d --build core-api

# Restart 1 service
docker compose -f docker-compose.dev.yml restart mqtt-bridge

# Vào shell container
docker compose -f docker-compose.dev.yml exec core-api bash

# Chạy Alembic migration
docker compose -f docker-compose.dev.yml exec core-api alembic upgrade head

# Tạo migration mới
docker compose -f docker-compose.dev.yml exec core-api alembic revision --autogenerate -m "add_new_field"
```

---

## 🏗️ Production

```bash
# Copy env template
cp .env.example .env
# Sửa .env với giá trị production thực tế

# Khởi chạy full stack (Traefik + Authelia + Monitoring)
docker compose up -d
```

---

## 📁 Cấu trúc dự án

```
Pick-to-light/
├── docker-compose.yml          # Production (full stack)
├── docker-compose.dev.yml      # Development (simplified)
├── .env.example                # Template secrets
│
├── services/
│   ├── auth/                   # auth-service    :8001
│   ├── core/                   # core-api        :8002
│   ├── websocket/              # ws-service      :8003
│   └── mqtt_bridge/            # mqtt-bridge     :8004
│
├── frontend/                   # Vue.js SPA      :3000
├── traefik/                    # Edge proxy config
├── authelia/                   # SSO + 2FA config
├── emqx/                       # MQTT ACL
├── postgres/                   # DB init script
├── monitoring/                 # Prometheus, Grafana, Loki, Promtail
└── docs/                       # System design + Solution proposal
```
