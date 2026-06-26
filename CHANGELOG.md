# Changelog

All notable changes to Cinema Plus are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0-beta] — 2026-06-26

### Phase 3.6 — Repository Consolidation & GitHub Preparation

#### Changed
- Archived legacy NiceGUI frontend to `legacy/nicegui/`
- Reorganized project structure with `docs/`, `scripts/`, `.github/`
- Updated `.gitignore` with comprehensive Python/Node.js/Next.js rules
- Updated `requirements.txt` — removed NiceGUI and httpx dependencies
- Consolidated documentation into `docs/` directory

#### Added
- `FEATURE_PARITY_REPORT.md` — Full migration verification report
- `CHANGELOG.md` — Project version history
- `LICENSE` — MIT License
- `ARCHITECTURE.md` — System architecture documentation
- `DEVELOPMENT.md` — Local development guide
- `CONTRIBUTING.md` — Contribution guidelines
- `ROADMAP.md` — Future development plans
- `CODE_OF_CONDUCT.md` — Community code of conduct
- `SECURITY.md` — Security policy
- `.github/ISSUE_TEMPLATE/` — Bug report and feature request templates
- `.github/PULL_REQUEST_TEMPLATE.md` — PR template

#### Removed
- `rawcode.py` — Original CLI prototype (dead code)
- `scratch/` — Temporary test scripts
- `frontend/` — NiceGUI frontend (archived to `legacy/nicegui/`)
- `tsconfig.tsbuildinfo` — Build artifact
- All `__pycache__` directories
- Unused `AdminBooking` TypeScript import

---

## [0.9.0] — 2026-06-25

### Phase 3.5 — Complete Next.js Migration

#### Added
- Full Next.js 15 frontend with App Router
- 25 pages covering all user and admin functionality
- TypeScript API client with standardized response envelope unwrapping
- Zustand authentication state management
- TanStack React Query for server state
- Tailwind CSS dark-themed responsive UI
- Admin layout designer page with interactive seat editing
- Global search component
- Booking stepper navigation component
- Auth middleware for route protection
- Analytics dashboard with CSV export
- Audit log viewer
- System health monitoring page

#### Changed
- Frontend technology from NiceGUI (Python) to Next.js (TypeScript)
- API client from httpx to fetch-based TypeScript client

---

## [0.8.0] — 2026-06-22

### Phase 3 — Reservation Engine

#### Added
- Two-phase commit reservation system
- `ReservationGroup` and `SeatReservation` database models
- Pessimistic locking via `SELECT FOR UPDATE` for concurrency safety
- 10-minute reservation timeout with automatic expiration
- Reservation lifecycle management (create, confirm, cancel, expire)
- Event dispatcher for reservation state transitions
- Checkout countdown timer
- Show occupancy statistics for admin
- Seat status API with real-time availability
- Reservation metrics tracking

#### Changed
- Booking flow from direct booking to reservation-based checkout

---

## [0.7.0] — 2026-06-20

### Phase 2.5 — Theatre Layout System

#### Added
- Interactive theatre layout designer
- Layout generator engine with 5 templates (Standard, IMAX, VIP, Recliner, Custom)
- `TheatreLayout` and `SeatDefinition` database models
- Layout versioning and publishing system
- Seat type state machine (Standard, Blocked, Wheelchair, Couple)
- Category-based pricing zones (Normal, Executive, Premium)
- Layout validation with error reporting
- Layout statistics API
- Alembic migrations for layout tables

---

## [0.6.0] — 2026-06-19

### Phase 2 — Architecture Cleanup

#### Added
- Service layer pattern (business logic separated from routes)
- Repository layer pattern (data access abstraction)
- Custom exception hierarchy (`CinemaPlusException` base)
- Audit logging system with action tracking
- Request logging middleware with X-Request-ID, latency, and query count headers
- GZip compression middleware
- Media asset management (upload, process, delete)
- Pricing engine with seat category rules
- Email service integration
- Event dispatcher system
- Cache utility module

#### Changed
- Refactored monolithic routes into service/repository architecture
- Standardized error responses across all endpoints
- Improved validation with Pydantic schema validators

---

## [0.5.0] — 2026-06-17

### Phase 1 — Platform Stabilization

#### Added
- FastAPI backend with REST API
- MySQL database with SQLAlchemy ORM
- JWT authentication with role-based access control
- Movie CRUD with soft delete and poster management
- Booking system with seat selection
- Theatre and screen management
- Show scheduling
- PDF e-ticket generation with QR codes
- Admin dashboard with statistics
- Review and rating system
- Database seeding script
- Health check endpoint
- API documentation via Swagger UI
- Alembic migration setup
- Static file serving for uploads
