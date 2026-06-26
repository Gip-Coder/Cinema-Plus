<p align="center">
  <h1 align="center">🎬 Cinema Plus</h1>
  <p align="center">
    A Production-Grade Cinema Management & Reservation Platform
    <br />
    Built with FastAPI · Next.js · MySQL · SQLAlchemy
    <br /><br />
    <a href="#features">Features</a> · <a href="#architecture">Architecture</a> · <a href="#getting-started">Getting Started</a> · <a href="#roadmap">Roadmap</a>
  </p>
</p>

---

## Overview

Cinema Plus is a full-stack cinema management and ticket reservation platform designed with production-grade architecture. It features a FastAPI backend with concurrency-safe seat reservations, a responsive Next.js frontend with a modern dark UI, an interactive theatre layout designer, and comprehensive admin tooling.

---

## Features

### Customer Experience
- 🎥 **Movie Discovery** — Browse, search, and filter movies by genre, language, and format
- 🎟️ **Interactive Seat Selection** — Real-time seat map with category-based pricing zones
- ⏱️ **Reservation System** — 10-minute temporary seat lock with countdown timer
- 💳 **Checkout & Confirmation** — Two-phase commit booking with reservation-to-booking conversion
- 🎫 **E-Tickets** — PDF ticket generation with QR codes
- ⭐ **Reviews & Ratings** — User movie reviews with rating system
- 👤 **User Profiles** — Account management with booking history

### Admin Dashboard
- 📊 **Analytics** — Revenue charts, booking trends, and occupancy statistics
- 🎬 **Movie CRUD** — Full movie lifecycle management with poster uploads
- 🏛️ **Theatre & Screen Management** — Multi-theatre support with screen configuration
- 🪑 **Layout Designer** — Interactive drag-and-drop theatre seating layout editor
- 📅 **Show Scheduling** — Create and manage show times across screens
- 💰 **Pricing Engine** — Category-based pricing with dynamic rules and multipliers
- 🖼️ **Media Library** — Centralized media asset management
- 📋 **Audit Logs** — Complete action audit trail
- 🔍 **System Health** — Real-time database and storage health monitoring

### Technical Highlights
- 🔒 **Concurrency Control** — Pessimistic locking (SELECT FOR UPDATE) for seat reservations
- 🔑 **JWT Authentication** — Role-based access control (Admin, Theatre Manager, Staff, Customer)
- 📡 **RESTful API** — Standardized response envelope with request ID tracking
- 🗄️ **Database Migrations** — Alembic-managed schema versioning
- 🎨 **Responsive UI** — Dark-themed, mobile-first Next.js interface with Tailwind CSS

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Next.js Frontend                        │
│  ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐ │
│  │ Auth │ │ Movies │ │ Booking│ │ Admin  │ │ Layout      │ │
│  │Pages │ │ Pages  │ │ Flow   │ │ Panel  │ │ Designer    │ │
│  └──┬───┘ └───┬────┘ └───┬────┘ └───┬────┘ └─────┬───────┘ │
│     └─────────┴──────────┴──────────┴─────────────┘         │
│                    API Client Layer                           │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP / REST
┌──────────────────────────┴───────────────────────────────────┐
│                     FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    Route Layer                          │  │
│  │  auth · movies · bookings · reservations · schedule    │  │
│  │  admin · layouts · reviews · tickets                   │  │
│  └────────────────────┬───────────────────────────────────┘  │
│  ┌────────────────────┴───────────────────────────────────┐  │
│  │                   Service Layer                         │  │
│  │  Business logic · Validation · Event dispatching       │  │
│  └────────────────────┬───────────────────────────────────┘  │
│  ┌────────────────────┴───────────────────────────────────┐  │
│  │                 Repository Layer                        │  │
│  │  SQLAlchemy ORM · Query builders · Transactions        │  │
│  └────────────────────┬───────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │ SQLAlchemy
                    ┌──────┴──────┐
                    │    MySQL    │
                    │  Database   │
                    └─────────────┘
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS |
| **State Management** | Zustand, TanStack React Query |
| **Backend** | FastAPI, Python, Uvicorn |
| **Database** | MySQL, SQLAlchemy ORM |
| **Migrations** | Alembic |
| **Authentication** | JWT (python-jose), Passlib (bcrypt) |
| **Ticket Generation** | ReportLab, qrcode, Pillow |
| **Linting** | ESLint, TypeScript strict mode |

---

## Project Structure

```
cinema-plus/
├── backend/                # FastAPI Backend
│   ├── main.py             # Application entry point & middleware
│   ├── database.py         # SQLAlchemy engine & session config
│   ├── auth/               # JWT security & password hashing
│   ├── core/               # App configuration
│   ├── exceptions/         # Custom exception hierarchy
│   ├── models/             # SQLAlchemy ORM models
│   ├── repositories/       # Data access layer
│   ├── routes/             # API endpoint routers
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic layer
│   ├── storage/            # File storage abstraction
│   └── utils/              # Utilities (cache, email, pricing, tickets)
├── src/                    # Next.js Frontend
│   ├── app/                # App Router pages & layouts
│   ├── components/         # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # API client, auth tokens, utilities
│   ├── stores/             # Zustand state stores
│   ├── types/              # TypeScript type definitions
│   └── middleware.ts       # Auth middleware
├── docs/                   # Project documentation
├── scripts/                # Database seeding & utilities
├── alembic/                # Database migration files
├── uploads/                # User-uploaded media assets
├── legacy/                 # Archived legacy NiceGUI frontend
└── .github/                # Issue & PR templates
```

---

## Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **MySQL** 8.0+
- **npm** or **pnpm**

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/cinema-plus.git
cd cinema-plus
```

### 2. Database Setup

```sql
CREATE DATABASE MovieTicketBooking;
```

### 3. Environment Variables

```bash
cp .env.example .env
cp .env.local.example .env.local
```

Edit `.env` with your MySQL credentials and JWT secret.

### 4. Backend Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 5. Database Migration & Seeding

```bash
# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_db.py
```

**Default accounts:**
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Customer | `testuser` | `password123` |

### 6. Start the Backend

```bash
uvicorn backend.main:app --reload --port 8001
```

API documentation: [http://localhost:8001/docs](http://localhost:8001/docs)

### 7. Frontend Setup

```bash
npm install
npm run dev
```

Frontend: [http://localhost:3000](http://localhost:3000)

---

## Completed Milestones

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Platform Stabilization — CRUD, validation, error handling, health monitoring | ✅ Complete |
| **Phase 2** | Architecture Cleanup — Service/repository pattern, exception hierarchy, audit logging | ✅ Complete |
| **Phase 3** | Reservation Engine — Concurrency control, two-phase booking, event system | ✅ Complete |
| **Phase 3.5** | Next.js Migration — Complete frontend rewrite from NiceGUI to Next.js | ✅ Complete |
| **Phase 3.6** | Repository Consolidation — Cleanup, documentation, GitHub preparation | ✅ Complete |

---

## Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for detailed upcoming features.

**Next planned phases:**
- **Phase 4** — Payment Integration & Production Hardening
- **Phase 5** — Real-time Features (WebSocket seat updates)
- **Phase 6** — Mobile Optimization & PWA
- **Phase 7** — Multi-tenant Theatre Network

---

## Documentation

| Document | Description |
|----------|-------------|
| [API Contract](docs/API_CONTRACT.md) | Complete REST API specification |
| [Architecture](docs/ARCHITECTURE.md) | System architecture overview |
| [Reservation Architecture](docs/RESERVATION_ARCHITECTURE.md) | Concurrency control design |
| [Theatre Layout Architecture](docs/THEATRE_LAYOUT_ARCHITECTURE.md) | Layout designer system design |
| [Development Guide](docs/DEVELOPMENT.md) | Local development setup |
| [Contributing](CONTRIBUTING.md) | Contribution guidelines |
| [Changelog](CHANGELOG.md) | Version history |

---

## Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) before submitting a pull request.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
