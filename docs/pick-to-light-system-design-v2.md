# 🏭 Pick-to-Light System Design v2

> **Hệ thống quản lý 1000 thiết bị real-time — Production Ready**

---

## Mục lục

1. [Tổng quan hệ thống](#1-tổng-quan-hệ-thống)
2. [Kiến trúc tổng thể](#2-kiến-trúc-tổng-thể)
3. [Phân chia Multi-Service](#3-phân-chia-multi-service)
4. [Edge Layer — Traefik + Authelia](#4-edge-layer--traefik--authelia)
5. [Application Services](#5-application-services)
6. [Data Layer](#6-data-layer)
7. [Observability Layer](#7-observability-layer)
8. [Docker Compose — Full Stack](#8-docker-compose--full-stack)
9. [Cấu trúc thư mục dự án](#9-cấu-trúc-thư-mục-dự-án)
10. [Luồng hoạt động chính](#10-luồng-hoạt-động-chính)
11. [Bảo mật](#11-bảo-mật)
12. [Lộ trình scale](#12-lộ-trình-scale)

---

## 1. Tổng quan hệ thống

Pick-to-Light (PTL) là hệ thống hỗ trợ nhặt hàng trong kho, gồm **1000 thiết bị LED + nút nhấn** gắn tại từng vị trí kho. Hệ thống điều khiển đèn theo đơn hàng, nhận xác nhận từ picker và cập nhật trạng thái **real-time** lên dashboard.

### 1.1. Yêu cầu kỹ thuật cốt lõi

| Tiêu chí                | Yêu cầu                                 |
| ------------------------ | ---------------------------------------- |
| Độ trễ điều khiển đèn    | < 200ms                                  |
| Thiết bị đồng thời       | 1000 nodes                               |
| Cập nhật dashboard       | Real-time qua WebSocket                  |
| Khả năng mở rộng         | Đa kho, đa zone                          |
| Tích hợp bên ngoài       | WMS / ERP qua REST API / Webhook         |
| Bảo mật truy cập         | SSO + 2FA qua Authelia                   |
| Quan sát hệ thống        | Prometheus + Grafana + Loki              |

---

## 2. Kiến trúc tổng thể

### 2.1. Sơ đồ kiến trúc

```mermaid
---
config:
  theme: mc
  layout: elk
---
flowchart TB
    %% =========================
    %% Client Layer
    %% =========================
    subgraph CLIENT["Client Layer"]
        Browser["Browser"]
        Mobile["Mobile"]
    end

    %% =========================
    %% Edge Layer
    %% =========================
    subgraph EDGE["Edge Layer"]
        Traefik["Traefik<br>:80 / :443 / :8080<br>Reverse Proxy · SSL · Rate Limit"]
        Authelia["Authelia<br>:9091<br>SSO + 2FA"]
    end

    %% =========================
    %% Application Layer
    %% =========================
    subgraph APP["Application Layer"]
        AuthSvc["auth-service<br>:8001"]
        CoreAPI["core-api<br>:8002"]
        WsSvc["ws-service<br>:8003"]
        MqttBridge["mqtt-bridge<br>:8004"]
    end

    %% =========================
    %% Data Layer
    %% =========================
    subgraph DATA["Data Layer"]
        EMQX["EMQX Broker<br>:1883 / :8083"]
        Redis["Redis<br>:6379<br>Cache + JWT Blacklist"]
        Postgres["PostgreSQL<br>:5432"]
    end

    %% =========================
    %% Device Layer
    %% =========================
    subgraph DEVICE["Device Layer"]
        ESP32["1000 × ESP32<br>LED + Button"]
    end

    %% =========================
    %% Observability Layer
    %% =========================
    subgraph OBS["Observability Layer"]
        Prometheus["Prometheus<br>:9090"]
        Grafana["Grafana<br>:3001"]
        Loki["Loki<br>:3100"]
        Promtail["Promtail"]
    end

    %% =========================
    %% Connections
    %% =========================
    Browser -- "HTTPS / WSS" --> Traefik
    Mobile -- "HTTPS / WSS" --> Traefik

    Traefik -- "/auth/*" --> Authelia
    Traefik -- "/auth/*" --> AuthSvc
    Traefik -- "/api/*" --> CoreAPI
    Traefik -- "/ws/*" --> WsSvc

    CoreAPI --> Postgres
    CoreAPI --> Redis
    AuthSvc --> Postgres
    AuthSvc --> Redis
    MqttBridge <--> EMQX
    MqttBridge -->|"HTTP internal"| CoreAPI
    MqttBridge -->|"HTTP internal"| WsSvc
    MqttBridge --> Redis
    WsSvc --> Redis

    EMQX <--> ESP32

    Promtail --> Loki
    Prometheus --> Grafana
    Loki --> Grafana

    %% =========================
    %% Styling
    %% =========================
    classDef client stroke:#818cf8,fill:#eef2ff;
    classDef edge stroke:#2dd4bf,fill:#f0fdfa;
    classDef app stroke:#a78bfa,fill:#f5f3ff;
    classDef data stroke:#facc15,fill:#fefce8;
    classDef device stroke:#4ade80,fill:#f0fdf4;
    classDef obs stroke:#fb923c,fill:#fff7ed;

    class Browser,Mobile client;
    class Traefik,Authelia edge;
    class AuthSvc,CoreAPI,WsSvc,MqttBridge app;
    class EMQX,Redis,Postgres data;
    class ESP32 device;
    class Prometheus,Grafana,Loki,Promtail obs;
```

### 2.2. Luồng dữ liệu tổng quan

```mermaid
---
config:
  theme: mc
  layout: elk
---
flowchart LR
    %% Nodes
    A["Supervisor<br>tạo đơn hàng"] -->|REST API| B["core-api"]
    B -->|HTTP internal| C["mqtt-bridge"]
    C -->|MQTT| D["ESP32<br>Bật LED"]
    D -->|MQTT event| C
    C -->|HTTP internal| B
    B -->|SQL| G["PostgreSQL"]
    C -->|HTTP internal| E["ws-service"]
    E -->|WebSocket| F["Vue.js Dashboard"]

    %% Styling
    classDef user stroke:#818cf8,fill:#eef2ff;
    classDef app stroke:#a78bfa,fill:#f5f3ff;
    classDef device stroke:#4ade80,fill:#f0fdf4;
    classDef ui stroke:#2dd4bf,fill:#f0fdfa;
    classDef db stroke:#facc15,fill:#fefce8;

    class A user;
    class B,C,E app;
    class D device;
    class F ui;
    class G db;
```

---

## 3. Phân chia Multi-Service

### 3.1. Bảng tổng hợp tất cả service

| Service          | Image / Tech    | Port(s)              | Trách nhiệm                                  |
| ---------------- | --------------- | -------------------- | --------------------------------------------- |
| **traefik**      | Traefik v3      | 80 / 443 / 8080      | Edge proxy, SSL, routing, rate limit          |
| **authelia**     | Authelia 4      | 9091                 | SSO, 2FA, session management                  |
| **auth-service** | FastAPI         | 8001                 | JWT, user, role, permission                   |
| **core-api**     | FastAPI         | 8002                 | Orders, devices, picking logic                |
| **ws-service**   | FastAPI         | 8003                 | WebSocket, real-time push                     |
| **mqtt-bridge**  | FastAPI         | 8004                 | MQTT subscribe/publish bridge                 |
| **emqx**         | EMQX 5.6        | 1883 / 8083 / 18083  | MQTT broker, 1000 kết nối                     |
| **postgres**     | PostgreSQL 16   | 5432                 | Database chính                                |
| **redis**        | Redis 7         | 6379                 | Cache device state, JWT blacklist             |
| **prometheus**   | Prometheus      | 9090                 | Thu thập metrics                              |
| **grafana**      | Grafana 10.4    | 3001                 | Dashboard metrics + logs                      |
| **loki**         | Loki 2.9        | 3100                 | Log aggregation                               |
| **promtail**     | Promtail 2.9    | —                    | Thu thập logs từ container                    |
| **frontend**     | Vue.js + Nginx  | 3000                 | SPA dashboard vận hành                        |

---

## 4. Edge Layer — Traefik + Authelia

### 4.1. Traefik

Traefik thay thế Nginx làm API Gateway, **tự động phát hiện service** trong Docker và cấp **SSL tự động** qua Let's Encrypt.

**Tính năng chính:**

- ✅ Automatic SSL từ Let's Encrypt
- ✅ Route theo path prefix (`/api`, `/ws`, `/auth`, `/grafana`)
- ✅ Rate limiting middleware
- ✅ Load balancing khi scale service lên nhiều replica
- ✅ Dashboard quản trị tại `traefik.yourdomain.com`

**Cấu hình `traefik/traefik.yml`:**

```yaml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@yourdomain.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

api:
  dashboard: true

providers:
  docker:
    exposedByDefault: false
  file:
    directory: /traefik/dynamic
```

**Dynamic config `traefik/dynamic/middlewares.yml`:**

```yaml
http:
  middlewares:
    authelia:
      forwardAuth:
        address: "http://authelia:9091/api/verify?rd=https://auth.yourdomain.com"
        trustForwardHeader: true
        authResponseHeaders:
          - Remote-User
          - Remote-Groups
          - Remote-Name
          - Remote-Email

    rate-limit:
      rateLimit:
        average: 100
        burst: 50

    cors:
      headers:
        accessControlAllowMethods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        accessControlAllowOriginList: ["https://yourdomain.com"]
        accessControlAllowHeaders: ["Content-Type", "Authorization"]
```

---

### 4.2. Authelia

Authelia đứng trước toàn bộ hệ thống, **xác thực người dùng trước khi cho truy cập**. Hỗ trợ **2FA** (TOTP — Google Authenticator) và **SSO** cho nhiều service.

#### Sơ đồ xác thực

```mermaid
sequenceDiagram
    actor User
    participant Traefik
    participant Authelia
    participant App as Protected Service

    User->>Traefik: Request /grafana
    Traefik->>Authelia: Forward Auth check
    alt Chưa đăng nhập
        Authelia-->>User: Redirect → Login page
        User->>Authelia: Username + Password + 2FA
        Authelia-->>User: Set session cookie
        User->>Traefik: Retry request (có cookie)
        Traefik->>Authelia: Forward Auth check
    end
    Authelia-->>Traefik: 200 OK + Headers
    Traefik->>App: Proxy request
    App-->>User: Response
```

#### Phân quyền truy cập theo role

```yaml
# authelia/configuration.yml (phần access_control)
access_control:
  default_policy: deny

  rules:
    # Grafana — chỉ IT/DevOps được truy cập
    - domain: grafana.yourdomain.com
      policy: two_factor
      groups: ["devops", "admin"]

    # Traefik dashboard — chỉ admin
    - domain: traefik.yourdomain.com
      policy: two_factor
      groups: ["admin"]

    # EMQX dashboard — chỉ admin
    - domain: emqx.yourdomain.com
      policy: two_factor
      groups: ["admin"]

    # Vue.js app — bypass Authelia, dùng JWT của auth-service
    - domain: app.yourdomain.com
      policy: bypass

    # API — bypass Authelia, dùng JWT của auth-service
    - domain: api.yourdomain.com
      policy: bypass
```

> **📝 Lưu ý:** Authelia chỉ bảo vệ **dashboard nội bộ** (Grafana, Traefik, EMQX) — những giao diện kỹ thuật dành cho IT. Vue.js app và API **bypass** Authelia, sử dụng JWT của `auth-service` để tránh xác thực 2 lần.

---

## 5. Application Services

### 5.1. Auth Service (`auth-service` — port 8001)

**Trách nhiệm:** Quản lý JWT, user, role, permission cho Vue.js app và API.

#### Endpoints

| Method | Endpoint             | Mô tả                                            | Quyền       |
| ------ | -------------------- | ------------------------------------------------- | ----------- |
| POST   | `/auth/login`        | Trả về `access_token` (15 phút) + `refresh_token` (7 ngày) | Public       |
| POST   | `/auth/refresh`      | Làm mới `access_token`                             | Authenticated |
| POST   | `/auth/logout`       | Blacklist token trong Redis                       | Authenticated |
| GET    | `/auth/me`           | Thông tin user hiện tại                           | Authenticated |
| GET    | `/auth/users`        | Danh sách user                                    | Admin only   |
| POST   | `/auth/users`        | Tạo user mới                                     | Admin only   |
| PUT    | `/auth/users/{id}`   | Cập nhật user                                     | Admin only   |

#### Data Model

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str]
    role: Mapped[str]               # admin | supervisor | picker
    warehouse_id: Mapped[UUID]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

---

### 5.2. Core API (`core-api` — port 8002)

**Trách nhiệm:** Business logic chính — đơn hàng, thiết bị, zone, picking.

#### Endpoints

##### Devices

| Method | Endpoint                     | Mô tả                                    |
| ------ | ---------------------------- | ----------------------------------------- |
| GET    | `/devices`                   | Danh sách thiết bị (filter: zone, status) |
| GET    | `/devices/{id}`              | Chi tiết thiết bị + trạng thái live (Redis) |
| POST   | `/devices`                   | Thêm thiết bị mới                        |
| PUT    | `/devices/{id}/config`       | Cập nhật cấu hình (brightness, color...) |
| DELETE | `/devices/{id}`              | Xóa thiết bị                             |
| POST   | `/devices/{id}/test-led`     | Test đèn thủ công                        |
| GET    | `/devices/offline`           | Danh sách thiết bị offline               |

##### Zones

| Method | Endpoint                | Mô tả                              |
| ------ | ----------------------- | ----------------------------------- |
| GET    | `/zones`                | Danh sách zone                     |
| POST   | `/zones`                | Tạo zone mới                      |
| GET    | `/zones/{id}/devices`   | Thiết bị trong zone               |
| GET    | `/zones/{id}/status`    | Trạng thái zone (từ Redis)        |

##### Orders

| Method | Endpoint                  | Mô tả                                |
| ------ | ------------------------- | ------------------------------------- |
| POST   | `/orders`                 | Tạo đơn picking                     |
| GET    | `/orders/{id}`            | Chi tiết đơn + danh sách task        |
| POST   | `/orders/{id}/start`      | Bắt đầu đơn → bật đèn tất cả vị trí |
| POST   | `/orders/{id}/cancel`     | Hủy đơn → tắt đèn                   |
| GET    | `/orders/{id}/progress`   | Tiến độ: `{done, total, percent}`    |
| GET    | `/orders/active`          | Danh sách đơn đang chạy             |

##### Internal (chỉ gọi từ mqtt-bridge, không expose qua Traefik)

| Method | Endpoint                         | Mô tả                                              |
| ------ | -------------------------------- | --------------------------------------------------- |
| POST   | `/internal/tasks/confirm`        | Xác nhận task → tính progress → tự đóng đơn nếu xong |
| POST   | `/internal/devices/heartbeat`    | Cập nhật trạng thái online thiết bị                 |

##### Reports

| Method | Endpoint                  | Mô tả                           |
| ------ | ------------------------- | -------------------------------- |
| GET    | `/reports/daily`          | Thống kê theo ngày              |
| GET    | `/reports/device/{id}`    | Lịch sử hoạt động thiết bị     |

#### Data Models

```python
class Device(Base):
    __tablename__ = "devices"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    device_code: Mapped[str] = mapped_column(String(20), unique=True)
    zone_id: Mapped[UUID] = mapped_column(ForeignKey("zones.id"))
    location: Mapped[str]               # "A/Row2/Slot05"
    status: Mapped[str] = mapped_column(default="offline")
    led_state: Mapped[str] = mapped_column(default="off")
    led_color: Mapped[str] = mapped_column(default="#00FF00")
    config: Mapped[dict] = mapped_column(JSONB, default={})
    last_seen: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class PickingOrder(Base):
    __tablename__ = "picking_orders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_ref: Mapped[str] = mapped_column(String(50), unique=True)
    warehouse_id: Mapped[UUID] = mapped_column(ForeignKey("warehouses.id"))
    status: Mapped[str] = mapped_column(default="pending")
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=func.now())


class PickingTask(Base):
    __tablename__ = "picking_tasks"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("picking_orders.id"))
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id"))
    quantity_required: Mapped[int]
    quantity_picked: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="waiting")
    confirmed_at: Mapped[datetime | None]
    confirmed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
```

---

### 5.3. MQTT Bridge (`mqtt-bridge` — port 8004)

**Trách nhiệm:** Cầu nối MQTT ↔ hệ thống. Chỉ chuyển tiếp message, **không chứa business logic** — mọi xử lý nghiệp vụ đều gọi `core-api`.

#### MQTT Topic Structure

```mermaid
---
config:
  theme: mc
  layout: elk
---
graph LR
    %% =========================
    %% Server → Device
    %% =========================
    subgraph Server_to_Device["Server → Device"]
        CMD1["ptl/device/{zone_id}/{device_id}/cmd"]
        CMD2["ptl/zone/{zone_id}/cmd"]
    end

    %% =========================
    %% Device → Server
    %% =========================
    subgraph Device_to_Server["Device → Server"]
        EVT["ptl/device/{zone_id}/{device_id}/event"]
        STS["ptl/device/{zone_id}/{device_id}/status"]
    end

    %% =========================
    %% Connections
    %% =========================
    Server["mqtt-bridge"] --> CMD1
    Server --> CMD2
    CMD1 --> ESP["ESP32 Device"]
    CMD2 --> ESP

    ESP --> EVT
    ESP --> STS
    EVT --> Server
    STS --> Server

    %% Styling
    classDef app stroke:#a78bfa,fill:#f5f3ff;
    classDef topic stroke:#2dd4bf,fill:#f0fdfa;
    classDef device stroke:#4ade80,fill:#f0fdf4;

    class Server app;
    class CMD1,CMD2,EVT,STS topic;
    class ESP device;
```

| Hướng            | Topic                                        | Mô tả                        |
| ---------------- | -------------------------------------------- | ----------------------------- |
| Server → Device  | `ptl/device/{zone_id}/{device_id}/cmd`       | Bật/tắt đèn, cấu hình       |
| Server → Device  | `ptl/zone/{zone_id}/cmd`                     | Broadcast toàn bộ zone       |
| Device → Server  | `ptl/device/{zone_id}/{device_id}/event`     | Nút nhấn, sensor             |
| Device → Server  | `ptl/device/{zone_id}/{device_id}/status`    | Heartbeat, online/offline    |

#### Payload mẫu

**Điều khiển đèn (cmd):**

```json
{
  "action": "led_on",
  "color": "#00FF00",
  "brightness": 80,
  "blink": false,
  "quantity": 3,
  "task_id": "uuid-task-123"
}
```

**Xác nhận nút nhấn (event):**

```json
{
  "event": "button_pressed",
  "device_id": "A2-05",
  "task_id": "uuid-task-123",
  "timestamp": 1714000000
}
```

#### Luồng xử lý event

```python
CORE_API_URL = "http://core-api:8002"
WS_SERVICE_URL = "http://ws-service:8003"

async def handle_device_event(msg: MQTTMessage):
    payload = json.loads(msg.payload)

    if payload["event"] == "button_pressed":
        # 1. Gọi core-api xử lý business logic (ghi DB, tính progress)
        async with httpx.AsyncClient() as client:
            result = await client.post(f"{CORE_API_URL}/internal/tasks/confirm", json={
                "task_id": payload["task_id"],
                "device_id": payload["device_id"]
            })
            data = result.json()

        # 2. Tắt đèn
        await mqtt_client.publish(
            f"ptl/device/{zone}/{device_id}/cmd",
            {"action": "led_off"}
        )

        # 3. Push dashboard qua ws-service
        async with httpx.AsyncClient() as client:
            await client.post(f"{WS_SERVICE_URL}/internal/broadcast", json=data)

    elif payload["event"] == "heartbeat":
        # Cập nhật last_seen trong Redis (TTL 60s)
        await redis.setex(
            f"device:state:{payload['device_id']}",
            60,
            json.dumps({"status": "online", "ts": payload["timestamp"]})
        )
```

#### core-api xử lý internal request

```python
# core-api/routers/internal.py
@router.post("/internal/tasks/confirm")
async def confirm_task(data: dict, db: AsyncSession = Depends(get_db)):
    # 1. Cập nhật task
    task = await task_repo.confirm(db, data["task_id"])

    # 2. Tính progress đơn hàng
    progress = await order_repo.get_progress(db, task.order_id)

    # 3. Nếu tất cả task xong → tự đóng đơn
    if progress["done"] == progress["total"]:
        await order_repo.complete(db, task.order_id)

    return {
        "type": "task_confirmed",
        "device_id": data["device_id"],
        "order_id": str(task.order_id),
        "order_progress": progress,
        "order_completed": progress["done"] == progress["total"]
    }
```

---

### 5.4. WebSocket Service (`ws-service` — port 8003)

**Trách nhiệm:** Quản lý WebSocket connection, push real-time lên Vue.js dashboard.

#### Endpoints

| Protocol | Endpoint                  | Mô tả                                 |
| -------- | ------------------------- | -------------------------------------- |
| WS       | `/ws/dashboard`           | Dashboard tổng quan (tất cả thiết bị) |
| WS       | `/ws/zone/{zone_id}`      | Theo dõi 1 zone                       |
| WS       | `/ws/order/{order_id}`    | Tiến độ 1 đơn hàng                   |

#### Message format → Client

```json
{
  "type": "device_update",
  "data": {
    "device_id": "A2-05",
    "led_state": "off",
    "task_status": "confirmed",
    "order_progress": { "done": 15, "total": 30 }
  }
}
```

#### Giao tiếp với mqtt-bridge qua HTTP internal

`mqtt-bridge` gọi trực tiếp `ws-service` qua HTTP nội bộ (cùng Docker network), không qua Redis Pub/Sub.

```mermaid
---
config:
  theme: mc
  layout: elk
---
flowchart LR
    %% Nodes & Connections
    MB["mqtt-bridge"] -->|HTTP POST /internal/broadcast| WS["ws-service"]
    WS -->|push| CA["Client A"]
    WS -->|push| CB["Client B"]
    WS -->|push| CC["Client C"]

    %% Styling
    classDef app stroke:#a78bfa,fill:#f5f3ff;
    classDef client stroke:#818cf8,fill:#eef2ff;

    class MB,WS app;
    class CA,CB,CC client;
```

> **📝 Lưu ý:** Với < 100 user giám sát, 1 instance `ws-service` dư sức giữ hàng nghìn WebSocket connection. Khi cần scale lên nhiều instance, có thể thêm Redis Pub/Sub làm broadcast bus.

---

## 6. Data Layer

### 6.1. PostgreSQL — Kết nối trực tiếp

Với quy mô MVP (3 service, 1 replica mỗi service, ~9 connections), kết nối trực tiếp PostgreSQL là đủ. Không cần PgBouncer.

```python
# Tất cả service kết nối trực tiếp PostgreSQL
DATABASE_URL = "postgresql+asyncpg://ptl:secret@postgres:5432/ptl_db"

# Config pool nhỏ gọn
engine = create_async_engine(
    DATABASE_URL,
    pool_size=3,       # chỉ giữ 3 connection
    max_overflow=2,    # tối đa thêm 2 khi bận
)
```

> **📝 Khi nào cần PgBouncer?** Khi scale lên 4+ replica mỗi service (≥ 100 connections), thêm PgBouncer vào giữa — chỉ cần đổi connection string từ `postgres:5432` sang `pgbouncer:5432`.

---

### 6.2. PostgreSQL Schema

#### ER Diagram

```mermaid
erDiagram
    WAREHOUSES {
        uuid id PK
        varchar name
        text address
        timestamptz created_at
    }

    ZONES {
        uuid id PK
        uuid warehouse_id FK
        varchar name
        text description
        timestamptz created_at
    }

    USERS {
        uuid id PK
        varchar username UK
        text password_hash
        varchar role "admin | supervisor | picker"
        uuid warehouse_id FK
        boolean is_active
        timestamptz created_at
    }

    DEVICES {
        uuid id PK
        varchar device_code UK
        uuid zone_id FK
        varchar location
        varchar status "online | offline"
        varchar led_state "on | off | blink"
        varchar led_color
        jsonb config
        timestamptz last_seen
        timestamptz created_at
    }

    PICKING_ORDERS {
        uuid id PK
        varchar order_ref UK
        uuid warehouse_id FK
        varchar status "pending | active | completed | cancelled"
        uuid created_by FK
        timestamptz started_at
        timestamptz completed_at
        timestamptz created_at
    }

    PICKING_TASKS {
        uuid id PK
        uuid order_id FK
        uuid device_id FK
        int quantity_required
        int quantity_picked
        varchar status "waiting | active | confirmed | skipped"
        timestamptz confirmed_at
        uuid confirmed_by FK
    }

    WAREHOUSES ||--o{ ZONES : "has"
    WAREHOUSES ||--o{ USERS : "belongs to"
    WAREHOUSES ||--o{ PICKING_ORDERS : "belongs to"
    ZONES ||--o{ DEVICES : "contains"
    USERS ||--o{ PICKING_ORDERS : "creates"
    USERS ||--o{ PICKING_TASKS : "confirms"
    PICKING_ORDERS ||--o{ PICKING_TASKS : "has"
    DEVICES ||--o{ PICKING_TASKS : "assigned to"
```

#### SQL Schema

```sql
-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Warehouses
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Zones
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    warehouse_id UUID REFERENCES warehouses(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'supervisor', 'picker')),
    warehouse_id UUID REFERENCES warehouses(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Devices
CREATE TABLE devices (
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

CREATE INDEX idx_devices_zone   ON devices(zone_id);
CREATE INDEX idx_devices_status ON devices(status) WHERE status = 'online';
CREATE INDEX idx_devices_led    ON devices(led_state) WHERE led_state != 'off';

-- Picking Orders
CREATE TABLE picking_orders (
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

CREATE INDEX idx_orders_status    ON picking_orders(status) WHERE status = 'active';
CREATE INDEX idx_orders_warehouse ON picking_orders(warehouse_id);

-- Picking Tasks
CREATE TABLE picking_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES picking_orders(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id),
    quantity_required INT NOT NULL,
    quantity_picked INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'waiting'
        CHECK (status IN ('waiting', 'active', 'confirmed', 'skipped')),
    confirmed_at TIMESTAMPTZ,
    confirmed_by UUID REFERENCES users(id)
);

CREATE INDEX idx_tasks_order  ON picking_tasks(order_id);
CREATE INDEX idx_tasks_device ON picking_tasks(device_id);
CREATE INDEX idx_tasks_status ON picking_tasks(status)
    WHERE status IN ('active', 'waiting');
```

---

### 6.3. Alembic — DB Migration

Alembic quản lý toàn bộ thay đổi schema theo version, **rollback được** khi có lỗi.

#### Cấu trúc thư mục

```
services/core/
├── alembic/
│   ├── env.py
│   ├── versions/
│   │   ├── 0001_initial_schema.py
│   │   ├── 0002_add_device_config.py
│   │   └── 0003_add_picking_tasks_index.py
│   └── script.py.mako
└── alembic.ini
```

#### Cấu hình `alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://ptl:secret@postgres:5432/ptl_db
```

#### Lệnh thường dùng

```bash
# Tạo migration mới sau khi thay đổi model
alembic revision --autogenerate -m "add_device_firmware_version"

# Apply migration lên DB
alembic upgrade head

# Rollback 1 bước
alembic downgrade -1

# Xem lịch sử migration
alembic history

# Xem trạng thái hiện tại
alembic current
```

#### Migration mẫu

```python
# alembic/versions/0002_add_device_firmware_version.py
def upgrade():
    op.add_column("devices",
        sa.Column("firmware_version", sa.String(20), nullable=True)
    )

def downgrade():
    op.drop_column("devices", "firmware_version")
```

---

### 6.4. Redis — Cấu trúc key

| Key Pattern                      | Value                                          | TTL               | Mô tả                               |
| -------------------------------- | ---------------------------------------------- | ------------------ | ------------------------------------ |
| `device:state:{device_id}`       | JSON `{status, led_state, last_seen, task_id}` | 60s                | Live state thiết bị (tự xóa nếu offline) |
| `device:task:{device_id}`        | `task_id`                                      | Theo đơn hàng     | Active task của thiết bị            |
| `order:active:{order_id}`        | JSON `{total, done, zone_ids[]}`               | Theo đơn hàng     | Trạng thái đơn đang chạy           |
| `auth:blacklist:{jti}`           | `"1"`                                          | Hết hạn token      | JWT blacklist (token đã logout)     |

---

## 7. Observability Layer

### 7.1. Prometheus — Thu thập Metrics

#### Targets cần scrape

| Target       | Endpoint                            | Metrics chính                                   |
| ------------ | ----------------------------------- | ----------------------------------------------- |
| auth-service | `:8001/metrics`                     | Request rate, latency, error rate               |
| core-api     | `:8002/metrics`                     | Request rate, latency, DB query time            |
| ws-service   | `:8003/metrics`                     | WebSocket connections, message rate             |
| mqtt-bridge  | `:8004/metrics`                     | MQTT message rate, processing time              |
| EMQX         | `:18083/api/v5/prometheus/stats`    | Connections, subscriptions, message rate         |
| PostgreSQL   | `pg-exporter:9187`                  | Query time, connections, table size             |
| Redis        | `redis-exporter:9121`               | Memory, commands/s, keyspace                    |
| Node         | `node-exporter:9100`                | CPU, RAM, disk, network                         |

#### Cấu hình `prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "ptl-services"
    static_configs:
      - targets:
          - "auth-service:8001"
          - "core-api:8002"
          - "ws-service:8003"
          - "mqtt-bridge:8004"

  - job_name: "emqx"
    static_configs:
      - targets: ["emqx:18083"]
    metrics_path: /api/v5/prometheus/stats
    basic_auth:
      username: admin
      password: ${EMQX_PASSWORD}

  - job_name: "postgres"
    static_configs:
      - targets: ["pg-exporter:9187"]

  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

rule_files:
  - "/etc/prometheus/alerts/*.yml"
```

#### Alert rules mẫu (`prometheus/alerts/ptl.yml`)

```yaml
groups:
  - name: ptl-alerts
    rules:
      - alert: DevicesOfflineHigh
        expr: (count(ptl_device_status{status="offline"}) / 1000) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Hơn 10% thiết bị offline ({{ $value | humanizePercentage }})"

      - alert: MQTTBrokerDown
        expr: up{job="emqx"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "EMQX broker không phản hồi"

      - alert: APIHighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API latency p95 > 500ms"

```

---

### 7.2. Loki — Log Aggregation

Loki gom logs từ tất cả container, **không index nội dung log** (khác ELK) nên nhẹ hơn nhiều. Truy vấn log qua Grafana bằng LogQL.

#### Kiến trúc Log Pipeline

```mermaid
---
config:
  theme: mc
  layout: elk
---
flowchart LR
    %% Log sources
    C1["Container 1"] --> P["Promtail"]
    C2["Container 2"] --> P
    C3["Container N"] --> P

    %% Pipeline
    P -->|push| L["Loki :3100"]
    L --> G["Grafana<br>LogQL queries"]

    %% Styling
    classDef container stroke:#818cf8,fill:#eef2ff;
    classDef agent stroke:#fb923c,fill:#fff7ed;
    classDef storage stroke:#facc15,fill:#fefce8;
    classDef ui stroke:#2dd4bf,fill:#f0fdfa;

    class C1,C2,C3 container;
    class P agent;
    class L storage;
    class G ui;
```

#### Cấu hình Promtail (`promtail/config.yml`)

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker-containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ["__meta_docker_container_name"]
        target_label: container
      - source_labels: ["__meta_docker_container_label_com_docker_compose_service"]
        target_label: service
    pipeline_stages:
      - json:
          expressions:
            level: level
            msg: message
      - labels:
          level:
```

#### LogQL query mẫu (trong Grafana)

```logql
# Lỗi trong 1 giờ qua
{service="core-api"} |= "ERROR" | json | line_format "{{.msg}}"

# Tất cả button_pressed events
{service="mqtt-bridge"} |= "button_pressed" | json

# Slow query PostgreSQL
{service="core-api"} | json | response_time > 500
```

---

### 7.3. Grafana — Dashboard

#### Các dashboard cần tạo

| Dashboard                      | Panel chính                                                            |
| ------------------------------ | ---------------------------------------------------------------------- |
| **1. System Overview**         | Thiết bị online/offline (gauge), MQTT rate, API latency p95, WS connections |
| **2. Device Health Map**       | Grid 1000 ô (màu theo trạng thái), filter zone, click xem log        |
| **3. Picking Performance**     | Đơn hoàn thành/giờ, thời gian trung bình/đơn, top zone throughput    |
| **4. Infrastructure**          | CPU/RAM, PG connections & slow queries, Redis memory                  |

#### Grafana Alerting — Notification channels

```yaml
contactPoints:
  - name: ops-team
    receivers:
      - type: email
        settings:
          addresses: ops@yourcompany.com
      - type: slack
        settings:
          url: ${SLACK_WEBHOOK_URL}
          channel: "#ptl-alerts"
```

---

## 8. Docker Compose — Full Stack

```yaml
version: "3.9"

networks:
  ptl-net:
    driver: bridge
  monitoring-net:
    driver: bridge

volumes:
  pg_data:
  redis_data:
  emqx_data:
  prometheus_data:
  grafana_data:
  loki_data:
  traefik_certs:

services:

  # ─── EDGE LAYER ─────────────────────────────────────────────

  traefik:
    image: traefik:v3.0
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/traefik.yml:ro
      - ./traefik/dynamic:/traefik/dynamic:ro
      - traefik_certs:/letsencrypt
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.yourdomain.com`)"
      - "traefik.http.routers.traefik.middlewares=authelia@file"
    restart: unless-stopped

  authelia:
    image: authelia/authelia:4
    volumes:
      - ./authelia:/config
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.authelia.rule=Host(`auth.yourdomain.com`)"
    restart: unless-stopped

  # ─── APPLICATION LAYER ─────────────────────────────────────

  auth-service:
    build: ./services/auth
    environment:
      DATABASE_URL: postgresql+asyncpg://ptl:${DB_PASSWORD}@postgres:5432/ptl_db
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auth-api.rule=Host(`api.yourdomain.com`) && PathPrefix(`/auth`)"
    depends_on: [postgres, redis]
    restart: unless-stopped

  core-api:
    build: ./services/core
    environment:
      DATABASE_URL: postgresql+asyncpg://ptl:${DB_PASSWORD}@postgres:5432/ptl_db
      REDIS_URL: redis://redis:6379
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.core-api.rule=Host(`api.yourdomain.com`) && PathPrefix(`/api`)"
      - "traefik.http.middlewares.rate-limit.ratelimit.average=100"
    depends_on: [postgres, redis]
    restart: unless-stopped

  ws-service:
    build: ./services/websocket
    environment:
      REDIS_URL: redis://redis:6379
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ws.rule=Host(`api.yourdomain.com`) && PathPrefix(`/ws`)"
    depends_on: [redis]
    restart: unless-stopped

  mqtt-bridge:
    build: ./services/mqtt_bridge
    environment:
      MQTT_BROKER: emqx
      MQTT_PORT: 1883
      REDIS_URL: redis://redis:6379
      CORE_API_URL: http://core-api:8002
      WS_SERVICE_URL: http://ws-service:8003
    networks: [ptl-net]
    depends_on: [emqx, redis, core-api]
    restart: unless-stopped

  # ─── MQTT BROKER ───────────────────────────────────────────

  emqx:
    image: emqx/emqx:5.6
    ports:
      - "1883:1883"
      - "8083:8083"
    environment:
      EMQX_DASHBOARD__DEFAULT_PASSWORD: ${EMQX_PASSWORD}
    volumes:
      - emqx_data:/opt/emqx/data
      - ./emqx/acl.conf:/opt/emqx/etc/acl.conf
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.emqx.rule=Host(`emqx.yourdomain.com`)"
      - "traefik.http.routers.emqx.middlewares=authelia@file"
      - "traefik.http.services.emqx.loadbalancer.server.port=18083"
    restart: unless-stopped

  # ─── DATA LAYER ────────────────────────────────────────────

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ptl_db
      POSTGRES_USER: ptl
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    command: >
      postgres
      -c max_connections=100
      -c shared_buffers=256MB
      -c effective_cache_size=512MB
      -c log_min_duration_statement=200
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks: [ptl-net]
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks: [ptl-net]
    restart: unless-stopped

  # ─── FRONTEND ──────────────────────────────────────────────

  frontend:
    build: ./frontend
    environment:
      VITE_API_URL: https://api.yourdomain.com
      VITE_WS_URL: wss://api.yourdomain.com/ws
    networks: [ptl-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`app.yourdomain.com`)"
    restart: unless-stopped

  # ─── OBSERVABILITY LAYER ───────────────────────────────────

  prometheus:
    image: prom/prometheus:v2.51
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=30d"
      - "--web.enable-lifecycle"
    volumes:
      - ./prometheus:/etc/prometheus:ro
      - prometheus_data:/prometheus
    networks: [ptl-net, monitoring-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.yourdomain.com`)"
      - "traefik.http.routers.prometheus.middlewares=authelia@file"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.4
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_SERVER_DOMAIN: grafana.yourdomain.com
      GF_SERVER_ROOT_URL: https://grafana.yourdomain.com
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    networks: [ptl-net, monitoring-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.yourdomain.com`)"
      - "traefik.http.routers.grafana.middlewares=authelia@file"
    depends_on: [prometheus, loki]
    restart: unless-stopped

  loki:
    image: grafana/loki:2.9
    command: -config.file=/etc/loki/config.yml
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml:ro
      - loki_data:/loki
    networks: [ptl-net, monitoring-net]
    restart: unless-stopped

  promtail:
    image: grafana/promtail:2.9
    command: -config.file=/etc/promtail/config.yml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail/config.yml:/etc/promtail/config.yml:ro
    networks: [monitoring-net]
    restart: unless-stopped

  # ─── EXPORTERS cho Prometheus ──────────────────────────────

  pg-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15
    environment:
      DATA_SOURCE_NAME: "postgresql://ptl:${DB_PASSWORD}@postgres:5432/ptl_db?sslmode=disable"
    networks: [ptl-net, monitoring-net]
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:v1.58
    environment:
      REDIS_ADDR: redis://redis:6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
    networks: [ptl-net, monitoring-net]
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:v1.7
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    networks: [monitoring-net]
    restart: unless-stopped
```

---

## 9. Cấu trúc thư mục dự án

```
ptl-system/
├── .env                              # Tất cả secrets (không commit git)
├── docker-compose.yml
│
├── traefik/
│   ├── traefik.yml                   # Static config
│   └── dynamic/
│       └── middlewares.yml           # Authelia, rate-limit, cors
│
├── authelia/
│   ├── configuration.yml             # Access control rules
│   ├── users_database.yml            # Local users (hoặc LDAP)
│   └── notification.yml              # Email config cho 2FA
│
├── services/
│   ├── auth/                         # auth-service
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── alembic/                  # Migrations cho bảng users
│   │   ├── models/
│   │   ├── routers/
│   │   └── requirements.txt
│   ├── core/                         # core-api
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── alembic/                  # Migrations chính
│   │   │   └── versions/
│   │   │       ├── 0001_initial.py
│   │   │       └── 0002_add_indexes.py
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   └── requirements.txt
│   ├── websocket/                    # ws-service
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── mqtt_bridge/                  # mqtt-bridge
│       ├── Dockerfile
│       ├── main.py
│       ├── handlers/
│       └── requirements.txt
│
├── frontend/                         # Vue.js SPA
│   ├── Dockerfile
│   ├── vite.config.js
│   └── src/
│       ├── views/
│       ├── components/
│       ├── composables/
│       └── stores/
│
├── emqx/
│   └── acl.conf                      # MQTT access control
│
├── prometheus/
│   ├── prometheus.yml
│   └── alerts/
│       └── ptl.yml
│
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   └── dashboards/
│   └── dashboards/
│       ├── system-overview.json
│       ├── device-health.json
│       └── infrastructure.json
│
├── loki/
│   └── config.yml
│
└── promtail/
    └── config.yml
```

---

## 10. Luồng hoạt động chính

### 10.1. Bật đèn khi bắt đầu đơn hàng

```mermaid
sequenceDiagram
    autonumber
    actor Supervisor
    participant Traefik
    participant CoreAPI as core-api
    participant Postgres as PostgreSQL
    participant MqttBridge as mqtt-bridge
    participant EMQX
    participant ESP32 as ESP32 Device
    participant WsSvc as ws-service
    participant Dashboard as Vue.js Dashboard

    Supervisor->>Traefik: POST /api/orders/{id}/start
    Traefik->>CoreAPI: Forward request
    CoreAPI->>Postgres: Cập nhật order status = active
    CoreAPI->>CoreAPI: Tính danh sách device cần bật
    CoreAPI->>MqttBridge: HTTP POST /internal/send-commands
    MqttBridge->>EMQX: Publish ptl/device/{zone}/{id}/cmd
    EMQX->>ESP32: Deliver MQTT message
    ESP32->>ESP32: Bật LED

    MqttBridge->>WsSvc: HTTP POST /internal/broadcast
    WsSvc->>Dashboard: Push WebSocket update
    Dashboard->>Dashboard: Cập nhật màu ô trên grid
```

### 10.2. Picker nhấn nút xác nhận

```mermaid
sequenceDiagram
    autonumber
    participant ESP32 as ESP32 Device
    participant EMQX
    participant MqttBridge as mqtt-bridge
    participant CoreAPI as core-api
    participant Postgres as PostgreSQL
    participant WsSvc as ws-service
    participant Dashboard as Vue.js Dashboard

    ESP32->>EMQX: Publish ptl/device/{zone}/{id}/event
    EMQX->>MqttBridge: Deliver event message
    MqttBridge->>CoreAPI: POST /internal/tasks/confirm
    CoreAPI->>Postgres: UPDATE task → confirmed
    CoreAPI->>CoreAPI: Tính progress + kiểm tra đơn hoàn thành
    CoreAPI-->>MqttBridge: Response {progress, order_completed}

    MqttBridge->>EMQX: Publish lệnh tắt đèn
    EMQX->>ESP32: LED off

    MqttBridge->>WsSvc: HTTP POST /internal/broadcast
    WsSvc->>Dashboard: Push WebSocket update
    Dashboard->>Dashboard: Cập nhật tiến độ đơn hàng

    Note over CoreAPI,Postgres: Nếu tất cả task xong → core-api tự động close đơn hàng
```

### 10.3. Ví dụ chi tiết: Payload từng bước

#### Bước 1 — Supervisor tạo đơn hàng

```http
POST /api/orders
```
```json
{
  "order_ref": "ORD-2026-0001",
  "warehouse_id": "uuid-wh-01",
  "tasks": [
    { "device_code": "A2-05", "quantity": 3 },
    { "device_code": "A2-08", "quantity": 1 }
  ]
}
```
```json
// Response 201 — chỉ ghi DB, chưa bật đèn
{ "id": "uuid-order-001", "status": "pending", "tasks_count": 2 }
```

#### Bước 2 — Supervisor bấm "Bắt đầu"

```http
POST /api/orders/uuid-order-001/start
```
→ `core-api` gọi `mqtt-bridge`:
```json
// POST http://mqtt-bridge:8004/internal/send-commands
{
  "commands": [
    { "zone_id": "zone-A", "device_id": "A2-05", "action": "led_on", "color": "#00FF00", "quantity": 3, "task_id": "uuid-task-01" },
    { "zone_id": "zone-A", "device_id": "A2-08", "action": "led_on", "color": "#00FF00", "quantity": 1, "task_id": "uuid-task-02" }
  ]
}
```

#### Bước 3 — mqtt-bridge gửi MQTT đến ESP32

```
Topic: ptl/device/zone-A/A2-05/cmd
```
```json
{ "action": "led_on", "color": "#00FF00", "brightness": 80, "quantity": 3, "task_id": "uuid-task-01" }
```
→ ESP32 bật LED xanh, hiển thị số 3.

#### Bước 4 — mqtt-bridge thông báo dashboard

```json
// POST http://ws-service:8003/internal/broadcast
{
  "type": "order_started",
  "order_id": "uuid-order-001",
  "devices": [
    { "device_id": "A2-05", "led_state": "on", "color": "#00FF00" },
    { "device_id": "A2-08", "led_state": "on", "color": "#00FF00" }
  ]
}
```
→ Dashboard: 2 ô sáng xanh trên grid.

#### Bước 5 — Picker nhấn nút tại A2-05

```
Topic: ptl/device/zone-A/A2-05/event
```
```json
{ "event": "button_pressed", "device_id": "A2-05", "task_id": "uuid-task-01", "timestamp": 1714000000 }
```

#### Bước 6 — mqtt-bridge gọi core-api xử lý

```json
// POST http://core-api:8002/internal/tasks/confirm
{ "task_id": "uuid-task-01", "device_id": "A2-05" }
```
```json
// Response từ core-api
{
  "type": "task_confirmed",
  "device_id": "A2-05",
  "order_id": "uuid-order-001",
  "order_progress": { "done": 1, "total": 2 },
  "order_completed": false
}
```

#### Bước 7 — Tắt đèn + push dashboard

```
Topic: ptl/device/zone-A/A2-05/cmd
```
```json
{ "action": "led_off" }
```
```json
// POST http://ws-service:8003/internal/broadcast
{
  "type": "task_confirmed",
  "device_id": "A2-05",
  "order_progress": { "done": 1, "total": 2 },
  "order_completed": false
}
```
→ Dashboard: A2-05 chuyển sang ✅, tiến độ 50%.

#### Bước 8 — Picker nhấn nút A2-08 (tương tự bước 5-7)

```json
// Response từ core-api
{
  "type": "task_confirmed",
  "device_id": "A2-08",
  "order_progress": { "done": 2, "total": 2 },
  "order_completed": true
}
```
→ Dashboard: A2-08 ✅, tiến độ 100%, đơn hàng tự động đóng. 🎉

---

## 11. Bảo mật

```mermaid
---
config:
  theme: mc
  layout: elk
---
graph TB
    %% =========================
    %% Security Layers
    %% =========================
    subgraph Security["🔒 Security Layers"]
        direction TB
        L1["🌐 Edge Layer<br>Traefik HTTPS/WSS bắt buộc<br>HTTP → HTTPS redirect"]
        L2["🔐 Dashboard nội bộ<br>Authelia 2FA<br>Grafana, Traefik, EMQX"]
        L3["🎫 API Authentication<br>JWT access token 15 phút<br>Refresh token 7 ngày"]
        L4["📡 MQTT Security<br>EMQX ACL — mỗi thiết bị<br>chỉ pub/sub đúng topic"]
        L5["💾 Data Layer<br>PostgreSQL: không expose ngoài Docker<br>Redis: password + không expose port"]
        L6["🔑 Secrets Management<br>File .env — không hardcode<br>Không commit vào git"]
        L7["⚡ Rate Limiting<br>Traefik middleware<br>100 req/s per IP"]
    end

    %% Flow
    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7

    %% Styling
    classDef edge stroke:#2dd4bf,fill:#f0fdfa;
    classDef auth stroke:#a78bfa,fill:#f5f3ff;
    classDef api stroke:#818cf8,fill:#eef2ff;
    classDef mqtt stroke:#4ade80,fill:#f0fdf4;
    classDef data stroke:#facc15,fill:#fefce8;
    classDef secrets stroke:#fb923c,fill:#fff7ed;
    classDef rate stroke:#f472b6,fill:#fdf2f8;

    class L1 edge;
    class L2 auth;
    class L3 api;
    class L4 mqtt;
    class L5 data;
    class L6 secrets;
    class L7 rate;
```

| Layer            | Biện pháp                                                  |
| ---------------- | ----------------------------------------------------------- |
| **Edge**         | Traefik HTTPS/WSS bắt buộc, HTTP redirect sang HTTPS      |
| **Dashboard**    | Authelia 2FA (Grafana, Traefik, EMQX)                     |
| **API**          | JWT access token 15 phút + refresh token 7 ngày           |
| **MQTT**         | EMQX ACL — mỗi thiết bị chỉ pub/sub đúng topic của nó    |
| **Database**     | PostgreSQL không expose ra ngoài Docker network            |
| **Redis**        | Password + không expose port ra ngoài                      |
| **Secrets**      | Tất cả trong file `.env`, không hardcode trong code        |
| **Rate Limit**   | Traefik middleware giới hạn 100 req/s per IP               |

---

## 12. Lộ trình scale

```mermaid
---
config:
  theme: mc
  layout: elk
---
graph LR
    %% Scaling Roadmap
    MVP["🟢 MVP<br>< 100 users<br>Docker Compose<br>1 server<br>Kết nối PG trực tiếp"]
    S1["🟡 Scale 1<br>< 500 users<br>+ PgBouncer<br>+ Redis Pub/Sub<br>2–3 replica"]
    S2["🟠 Scale 2<br>< 5,000 users<br>+ Celery worker<br>+ PG read replica"]
    S3["🔴 Scale 3<br>Không giới hạn<br>Kubernetes<br>EMQX cluster<br>PostgreSQL HA"]

    MVP --> S1 --> S2 --> S3

    %% Styling
    classDef mvp stroke:#22c55e,fill:#f0fdf4;
    classDef s1 stroke:#eab308,fill:#fefce8;
    classDef s2 stroke:#f97316,fill:#fff7ed;
    classDef s3 stroke:#ef4444,fill:#fef2f2;

    class MVP mvp;
    class S1 s1;
    class S2 s2;
    class S3 s3;
```

| Giai đoạn    | Quy mô                | Thay đổi                                                      |
| ------------ | ---------------------- | -------------------------------------------------------------- |
| **MVP**      | < 100 users            | Docker Compose, 1 server, kết nối PG trực tiếp, HTTP internal  |
| **Scale 1**  | < 500 users            | + PgBouncer, + Redis Pub/Sub, 2–3 replica mỗi service           |
| **Scale 2**  | < 5,000 users          | + Celery worker, + PostgreSQL read replica                     |
| **Scale 3**  | Không giới hạn          | Kubernetes, EMQX cluster, PostgreSQL HA                        |

---

<div align="center">

**Pick-to-Light System Design v2.0**

*Stack: Traefik · Authelia · EMQX · FastAPI · Alembic · PostgreSQL · Redis · Vue.js · Prometheus · Grafana · Loki · Docker*

</div>
