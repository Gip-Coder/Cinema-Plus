<!-- BADGES_START -->
![Build Passing](https://img.shields.io/badge/build-passing-brightgreen) ![Coverage 85.0%](https://img.shields.io/badge/coverage-85.0%25-brightgreen) ![Lighthouse 97%](https://img.shields.io/badge/lighthouse-97%25-blue) ![Accessibility 80%](https://img.shields.io/badge/accessibility-80%25-blueviolet) ![Security secure](https://img.shields.io/badge/security-zero_vulns-brightgreen) ![Maintainability A](https://img.shields.io/badge/maintainability-A-emerald) ![License MIT](https://img.shields.io/badge/license-MIT-yellow)
<!-- BADGES_END -->

<p align="center">
  <h1 align="center">🎬 Cinema Plus</h1>
  <p align="center">
    A Production-Grade Cinema Management & Ticket Reservation Platform
    <br />
    Built with FastAPI · Next.js 15 · MySQL 8 · SQLAlchemy · Docker
    <br /><br />
    <a href="#features">Features</a> · <a href="#architecture">Architecture</a> · <a href="#getting-started">Getting Started</a> · <a href="#docker-setup">Docker</a> · <a href="#production-deployment">Production</a>
  </p>
</p>

---

## Overview

Cinema Plus is a full-stack cinema management and ticket reservation platform designed with enterprise-grade architecture. It features a **FastAPI** backend with concurrency-safe seat reservations, database-level unique constraints, pessimistic locking (`SELECT FOR UPDATE`), a responsive **Next.js 15** frontend with modern dark UI, an interactive theatre layout designer, and full administrative tooling.

---

## Features

### Customer Experience
- 🎥 **Movie Discovery** — Browse, search, and filter movies by genre, language, and format
- 🎟️ **Interactive Seat Selection** — Real-time seat map with category-based pricing zones
- ⏱️ **Reservation Engine** — 10-minute temporary seat lock with countdown timer
- 💳 **Two-Phase Booking** — Atomic booking creation with seat reservation conversion
- 🎫 **E-Tickets** — Automated PDF ticket generation with verifiable QR codes
- ⭐ **Reviews & Ratings** — Verified user movie reviews with star ratings
- 👤 **User Profiles** — Account management, password changes, and booking history

### Admin Dashboard
- 📊 **Analytics** — Real-time revenue charts, booking trends, and occupancy rates
- 🎬 **Movie Lifecycle** — Full movie management with poster uploads and soft-deletion
- 🏛️ **Theatre & Screens** — Multi-theatre support with customizable screens
- 🪑 **Layout Designer** — Visual seat layout grid editor with row/category assignments
- 📅 **Show Scheduling** — Create and manage show times across screens with price multipliers
- 💰 **Pricing Engine** — Category pricing (Normal / Executive / Premium) with dynamic rules
- 🖼️ **Media Library** — Centralized media asset management with thumbnail generation
- 📋 **Audit Logs** — Tamper-evident action audit trail with IP address tracking
- 🔍 **System Health** — Real-time database and storage health monitoring endpoint (`/health`)

### Security Highlights
- 🔒 **Database Integrity** — Database-level unique constraint on `(show_id, seat_name)` in `booked_seats`
- 🔒 **Concurrency Control** — Row-level pessimistic locking (`SELECT FOR UPDATE`) prevents double-booking
- 🔑 **JWT Authentication** — Stateless token authentication with role-based access control
- 🛡️ **Zero Secrets in Code** — All credentials, keys, and origins driven by environment variables
- 🌐 **Strict CORS** — Environment-configured origins; wildcard-with-credentials prohibited
- 📑 **Security Headers** — `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`
- 🛡️ **Upload Safety** — Extension whitelisting, MIME verification, Pillow header analysis, UUID storage keys

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 15 Frontend                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │   Auth   │ │  Movies  │ │  Booking │ │  Admin   │ │   Layout     │ │
│  │  Pages   │ │  Pages   │ │   Flow   │ │  Panel   │ │  Designer    │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
│       └────────────┴────────────┴────────────┴──────────────┘         │
│                        API Client Layer                                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JWT Bearer)
┌───────────────────────────────────┴────────────────────────────────────┐
│                         FastAPI Backend                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Route Layer                               │  │
│  │  auth · movies · bookings · reservations · schedule · admin      │  │
│  └────────────────────────────────┬─────────────────────────────────┘  │
│  ┌────────────────────────────────┴─────────────────────────────────┐  │
│  │                       Service Layer                              │  │
│  │  Business logic · Atomic booking transactions · Event dispatcher │  │
│  └────────────────────────────────┬─────────────────────────────────┘  │
│  ┌────────────────────────────────┴─────────────────────────────────┐  │
│  │                      Repository Layer                            │  │
│  │  SQLAlchemy ORM · Query builders · Transaction staging & flush   │  │
│  └────────────────────────────────┬─────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SQLAlchemy 2.0 (PyMySQL)
                             ┌──────┴──────┐
                             │   MySQL 8   │
                             │  Database   │
                             └─────────────┘
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS |
| **Frontend State** | Zustand 5, TanStack React Query 5 |
| **Backend** | FastAPI 0.115+, Python 3.11+, Uvicorn |
| **Database** | MySQL 8.0, SQLAlchemy 2.0 ORM |
| **Migrations** | Alembic 1.13+ |
| **Authentication** | JWT (`python-jose`), `bcrypt` password hashing |
| **Ticket Engine** | ReportLab, `qrcode`, Pillow |
| **Containerization** | Docker, Docker Compose |

---

## Requirements

- **Python** 3.10+ (Python 3.11 recommended)
- **Node.js** 18+ (Node.js 20 LTS recommended)
- **MySQL** 8.0+
- **Docker & Docker Compose** (optional, for containerized deployment)

---

## Project Structure

```
cinema-plus/
├── backend/                # FastAPI Backend
│   ├── main.py             # App entry point, lifespan, security headers & middleware
│   ├── database.py         # SQLAlchemy engine, pool configuration, connectivity check
│   ├── auth/               # JWT token generation & bcrypt hashing
│   ├── core/               # App configuration & environment validation
│   ├── exceptions/         # Custom HTTP exception hierarchy
│   ├── models/             # SQLAlchemy ORM models
│   ├── repositories/       # Data access layer (staged transactions)
│   ├── routes/             # API endpoint routers
│   ├── schemas/            # Pydantic request/response validation schemas
│   ├── services/           # Business logic layer
│   └── utils/              # Cache, email, pricing engine, ticket PDF generator
├── src/                    # Next.js Frontend
│   ├── app/                # Next.js App Router pages & layouts
│   ├── components/         # Reusable UI components
│   ├── hooks/              # Custom React hooks (useAuth, useMovies, etc.)
│   ├── lib/                # API client, auth token management
│   ├── stores/             # Zustand state stores
│   └── types/              # TypeScript domain types
├── alembic/                # Database schema migrations
├── scripts/                # Database seed script & benchmarks
├── uploads/                # Local user media storage (volume-mountable)
├── Dockerfile              # Production Backend Docker image
├── Dockerfile.frontend     # Production Frontend Docker image
├── docker-compose.yml      # Complete local/staging stack with MySQL
├── Procfile                # Generic platform process file (Render/Railway)
└── requirements.txt        # Backend dependencies
```

---

## Environment Variables

### Backend (`.env`)

| Variable | Description | Default | Required in Prod |
|---|---|---|---|
| `APP_ENV` | Application environment (`development` / `production`) | `development` | Yes |
| `DB_HOST` | MySQL database host | `localhost` | Yes |
| `DB_PORT` | MySQL database port | `3306` | Yes |
| `DB_USER` | MySQL database user | `root` | Yes |
| `DB_PASSWORD` | MySQL database password | — | **Yes** |
| `DB_NAME` | MySQL database name | `MovieTicketBooking` | Yes |
| `SECRET_KEY` | JWT signing secret (min 32 chars) | — | **Yes** |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry duration | `1440` (24h) | No |
| `ADMIN_PASSWORD` | Initial admin account password | — | **Yes** |
| `ADMIN_EMAIL` | Initial admin email | `admin@cinemaplus.local` | No |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowed origins | `http://localhost:3005` | **Yes** |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:3005` | Yes |
| `RESERVATION_TIMEOUT_MINUTES`| Seat reservation lock duration | `10` | No |
| `ENABLE_DOCS` | Enable `/docs` in production | `false` | No |
| `SMTP_HOST` | SMTP server host (optional) | `smtp.gmail.com` | No |
| `SMTP_PORT` | SMTP server port | `587` | No |
| `SMTP_USER` | SMTP username | — | No |
| `SMTP_PASS` | SMTP password | — | No |
| `SMTP_FROM` | Outgoing email address | `no-reply@cinemaplus.com` | No |

### Frontend (`.env.local`)

| Variable | Description | Example |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Public backend API URL | `http://localhost:8001` or `https://api.yourdomain.com` |
| `REACT_PROFILE` | Enable React profiling in prod (slower) | `false` |

---

## Local Development Setup

### 1. Clone & Configure

```bash
git clone <repository-url>
cd Cinema_Plus

# Configure Backend environment
cp .env.example .env

# Configure Frontend environment
cp .env.local.example .env.local
```

### 2. Backend Setup

```bash
# Create and activate Python virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Initialization & Migration

Ensure MySQL is running and create the database:

```sql
CREATE DATABASE MovieTicketBooking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run Alembic migrations:

```bash
alembic upgrade head
```

Seed initial sample data (idempotent):

```bash
python scripts/seed_db.py
```

### 4. Start Backend Server

```bash
# Development mode:
uvicorn backend.main:app --reload --port 8001

# Production mode (single worker):
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 1
```

Backend is live at: [http://localhost:8001](http://localhost:8001)  
Interactive API Documentation: [http://localhost:8001/docs](http://localhost:8001/docs)

### 5. Frontend Setup

```bash
npm install
npm run dev
```

Frontend is live at: [http://localhost:3005](http://localhost:3005)

---

## Docker Setup (Recommended for Full Stack)

Run the entire application stack (MySQL 8, FastAPI backend, Next.js frontend) with a single command:

```bash
# 1. Configure environment
cp .env.example .env

# 2. Build and start containers
docker compose up --build -d

# 3. Apply migrations inside backend container
docker compose exec backend alembic upgrade head

# 4. (Optional) Seed sample data
docker compose exec backend python scripts/seed_db.py
```

### Docker Services:
- **Frontend**: [http://localhost:3005](http://localhost:3005)
- **Backend API**: [http://localhost:8001](http://localhost:8001)
- **MySQL**: Internal network `mysql:3306`

To stop:
```bash
docker compose down
```

---

## Production Deployment

### Option A: Railway (two services, one repo)

This repo deploys as **two separate Railway services** built from the same
GitHub repository — a `backend` service (using `Dockerfile`) and a
`frontend` service (using `Dockerfile.frontend`). Railway auto-detects a
file literally named `Dockerfile`, but `Dockerfile.frontend` needs to be
selected explicitly per-service (Railway has no single config file that can
unambiguously target one of two services sharing a repo root, so this is
done via service variables/settings in the dashboard rather than a committed
`railway.json`).

1. **Database**: Provision a Railway MySQL plugin (or any managed MySQL).
   Note its connection host/port/user/password/database name — Railway's
   MySQL plugin exposes these as `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`,
   `MYSQLPASSWORD`, `MYSQLDATABASE`; map them to this app's `DB_HOST`,
   `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` variables below.

2. **Backend service**:
   - Create a new Railway service from this repo. Leave the Dockerfile path
     as the default — Railway will find the root `Dockerfile` automatically.
   - Set these **runtime environment variables** (Settings → Variables):
     - `APP_ENV=production`
     - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
     - `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
     - `ADMIN_PASSWORD` (a strong password — the app refuses to boot in
       production without this set)
     - `ADMIN_EMAIL`
     - `ALLOWED_ORIGINS=https://<your-frontend-service>.up.railway.app`
     - `FRONTEND_URL=https://<your-frontend-service>.up.railway.app`
   - Do **not** set `PORT` yourself — Railway injects it automatically, and
     the Dockerfile CMD already reads `${PORT:-8001}`.
   - Set the **health check path** to `/health` (Settings → Healthcheck
     Path). `/health` requires no authentication and checks both the
     database connection and upload-directory writability.
   - **Attach a persistent Volume** (Settings → Volumes → New Volume),
     mounted at `/app/uploads`. Without this, any admin-uploaded poster is
     lost on the next redeploy/restart, since the container filesystem is
     otherwise ephemeral. This is the only storage mechanism this app uses —
     it does not integrate with S3 or any other object storage.
   - Migrations run automatically: the Dockerfile's start command is
     `alembic upgrade head && uvicorn ...`, so every deploy applies pending
     migrations before the server starts accepting traffic. No separate
     manual migration step is required.

3. **Frontend service**:
   - Create a second Railway service from the same repo.
   - Set the service variable `RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend`
     so Railway builds from the frontend Dockerfile instead of the default
     `Dockerfile`.
   - Set `NEXT_PUBLIC_API_BASE_URL=https://<your-backend-service>.up.railway.app`.
     **This must be a build-time variable, not just a runtime one** — Next.js
     inlines `NEXT_PUBLIC_*` variables into the client bundle at `next build`
     time (see `Dockerfile.frontend`'s `ARG NEXT_PUBLIC_API_BASE_URL`).
     Railway makes service variables available as Docker build args
     automatically, but if you ever change this value, you must **trigger a
     new deploy/redeploy** — restarting the existing container does nothing,
     since the value is already baked into the built static files. A stale
     value silently ships as `http://localhost:8001` if it was never set at
     build time, which fails every API call from the deployed frontend.
   - Do not set `PORT` yourself — the frontend Dockerfile CMD reads
     `${PORT:-3005}` and Railway injects `PORT` automatically.

4. **Verify**: after both services are up, confirm `GET https://<backend>/health`
   returns `{"status": "healthy", ...}`, then open the frontend URL and
   confirm movies load (see the Production Smoke Test in the final audit
   report for the full checklist).

### Option B: VPS (Ubuntu / Debian with Docker Compose)

```bash
# Clone repo on server
git clone <repo-url> /opt/cinemaplus
cd /opt/cinemaplus

# Create production .env with real credentials
cp .env.example .env
nano .env

# Start with Docker Compose
docker compose -f docker-compose.yml up -d --build

# Run database migrations
docker compose exec backend alembic upgrade head
```

---

## Media Storage

- Media files (posters, banners, generated QR codes) are stored under `uploads/media/`.
- In containerized deployments, **a persistent volume must be attached at `/app/uploads/`**.
- *Ephemeral cloud hosting without persistent disks will lose user-uploaded posters upon container restart.*

---

## SMTP Email Configuration

Email confirmations are **optional**. If `SMTP_USER` and `SMTP_PASS` are omitted, email sending is skipped gracefully without interrupting bookings.

To enable booking confirmation emails with PDF attachments:
```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_specific_password
SMTP_FROM=no-reply@cinemaplus.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
```

---

## Admin Setup

The initial administrator account is automatically bootstrapped on first startup using:
- **Username**: `admin`
- **Password**: Set via `ADMIN_PASSWORD` environment variable
- **Email**: Set via `ADMIN_EMAIL` environment variable

*In production (`APP_ENV=production`), the application will refuse to start if `ADMIN_PASSWORD` is missing or insecure.*

---

## Testing

```bash
# Backend unit & integration tests
pytest backend/tests -v

# Frontend TypeScript type verification
npm run typecheck

# Frontend unit tests
npm run test:unit

# Next.js production build verification
npm run build
```

---

## Known Production Limitations

1. **In-Memory Cache & Single Worker**: The current cache (`backend/utils/cache.py`) is an in-memory dictionary. Backend containers should run with `--workers 1`. For horizontal multi-worker scaling, replace `InMemoryCache` with a Redis backend.
2. **Local Media Storage**: Uploaded posters require a persistent volume mount. For multi-server or serverless architectures, configure S3/Cloudinary.
3. **Database Driver**: SQLAlchemy connects to MySQL using `pymysql`. Ensure MySQL connection pooling (`pool_size=10, max_overflow=20`) is tuned for your server's RAM.

---

## License

This project is licensed under the MIT License.
