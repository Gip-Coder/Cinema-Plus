# Cinema Plus — System Architecture

## Overview

Cinema Plus follows a decoupled client-server architecture with a **Next.js** frontend communicating over REST with a **FastAPI** backend, backed by a **MySQL** relational database managed through **SQLAlchemy ORM** and **Alembic** migrations.

---

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                               │
│                                                                   │
│   Next.js 15 (App Router)                                        │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│   │  App Pages   │  │  Components │  │  State Management       │  │
│   │  (25 routes) │  │  (UI/Booking│  │  Zustand + React Query  │  │
│   └──────┬───────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│          └─────────────────┴─────────────────────┘                │
│                         API Client                                │
│             src/lib/api/ (fetch + envelope unwrap)                │
└──────────────────────────────┬────────────────────────────────────┘
                               │  HTTP/REST (JSON)
                               │  Port 8001
┌──────────────────────────────┴────────────────────────────────────┐
│                        SERVER LAYER                               │
│                                                                   │
│   FastAPI + Uvicorn                                              │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │                   MIDDLEWARE STACK                        │    │
│   │  CORS · GZip · Request Logging (ID, Latency, Queries)  │    │
│   └─────────────────────────┬───────────────────────────────┘    │
│                             │                                     │
│   ┌─────────────────────────┴───────────────────────────────┐    │
│   │                    ROUTE LAYER                           │    │
│   │  auth · movies · bookings · reservations · schedule     │    │
│   │  admin · layouts · reviews · tickets                    │    │
│   └─────────────────────────┬───────────────────────────────┘    │
│                             │                                     │
│   ┌─────────────────────────┴───────────────────────────────┐    │
│   │                   SERVICE LAYER                          │    │
│   │  Business logic · Validation · Event dispatching        │    │
│   │  Pricing engine · Media processing · Ticket generation  │    │
│   └─────────────────────────┬───────────────────────────────┘    │
│                             │                                     │
│   ┌─────────────────────────┴───────────────────────────────┐    │
│   │                 REPOSITORY LAYER                         │    │
│   │  SQLAlchemy ORM queries · Transactions · FOR UPDATE     │    │
│   └─────────────────────────┬───────────────────────────────┘    │
└──────────────────────────────┬────────────────────────────────────┘
                               │  SQLAlchemy
                    ┌──────────┴──────────┐
                    │       MySQL 8       │
                    │  ┌───────────────┐  │
                    │  │ users         │  │
                    │  │ movies        │  │
                    │  │ theatres      │  │
                    │  │ screens       │  │
                    │  │ shows         │  │
                    │  │ bookings      │  │
                    │  │ booked_seats  │  │
                    │  │ reservations  │  │
                    │  │ seat_defs     │  │
                    │  │ layouts       │  │
                    │  │ reviews       │  │
                    │  │ audit_logs    │  │
                    │  │ media_assets  │  │
                    │  │ pricing       │  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

---

## Layer Responsibilities

### Frontend (Next.js)
- **App Router Pages**: Server-rendered pages with client-side interactivity
- **API Client**: Centralized fetch wrapper with token injection and response envelope unwrapping
- **Auth State**: Zustand store with JWT token persistence
- **Server State**: TanStack React Query for caching, refetching, and optimistic updates

### Backend (FastAPI)
- **Routes**: HTTP endpoint definitions, request parsing, and response formatting
- **Services**: Core business logic, validation rules, and cross-cutting concerns
- **Repositories**: Database queries abstracted from business logic
- **Utils**: Shared utilities (caching, email, pricing calculations, ticket PDF generation)

### Database (MySQL)
- **Schema managed by Alembic** — all changes tracked as versioned migrations
- **Pessimistic locking** for reservation concurrency control
- **Soft deletes** for movies (recoverable)
- **Audit trail** via `audit_logs` table

---

## Authentication Flow

```
Client                    Backend                   Database
  │                         │                         │
  │  POST /api/auth/login   │                         │
  │  {username, password}   │                         │
  │────────────────────────>│                         │
  │                         │  verify credentials     │
  │                         │────────────────────────>│
  │                         │<────────────────────────│
  │                         │  generate JWT token     │
  │  {access_token}         │                         │
  │<────────────────────────│                         │
  │                         │                         │
  │  GET /api/auth/me       │                         │
  │  Authorization: Bearer  │                         │
  │────────────────────────>│                         │
  │                         │  decode & verify JWT    │
  │  {user profile}         │  check role/permissions │
  │<────────────────────────│                         │
```

---

## Reservation Concurrency Model

See [RESERVATION_ARCHITECTURE.md](RESERVATION_ARCHITECTURE.md) for the full two-phase commit design with pessimistic locking.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Decoupled frontend/backend** | Independent deployment, technology flexibility |
| **Service/Repository pattern** | Testability, separation of concerns |
| **Pessimistic locking** | Strongest guarantee against double-booking |
| **JWT over sessions** | Stateless, scalable authentication |
| **Alembic migrations** | Reproducible, version-controlled schema changes |
| **Response envelope** | Consistent API contract for frontend consumption |
| **Soft deletes** | Data recovery, audit compliance |
