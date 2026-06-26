# Cinema Plus — Development Guide

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Backend runtime |
| Node.js | 18+ | Frontend runtime |
| MySQL | 8.0+ | Database |
| npm | 9+ | Package management |
| Git | 2.30+ | Version control |

---

## Local Development Setup

### 1. Clone and Configure

```bash
git clone https://github.com/your-username/cinema-plus.git
cd cinema-plus

# Copy environment files
cp .env.example .env
cp .env.local.example .env.local
```

Edit `.env` with your MySQL credentials:
```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=MovieTicketBooking
SECRET_KEY=your-dev-secret-key
```

### 2. Database

```sql
CREATE DATABASE MovieTicketBooking;
```

### 3. Backend

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed sample data
python scripts/seed_db.py

# Start backend server
uvicorn backend.main:app --reload --port 8001
```

**Backend runs at**: http://localhost:8001  
**API docs at**: http://localhost:8001/docs

### 4. Frontend

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

**Frontend runs at**: http://localhost:3000

---

## Development Commands

### Backend

| Command | Description |
|---------|-------------|
| `uvicorn backend.main:app --reload --port 8001` | Start with auto-reload |
| `alembic upgrade head` | Apply all migrations |
| `alembic revision --autogenerate -m "description"` | Generate new migration |
| `alembic downgrade -1` | Rollback last migration |
| `python scripts/seed_db.py` | Seed database |

### Frontend

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server (port 3000) |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run typecheck` | TypeScript type checking |

---

## Project Conventions

### Backend

- **Routes**: Define HTTP endpoints only — no business logic
- **Services**: All business logic lives here
- **Repositories**: Database queries only — no business logic
- **Models**: SQLAlchemy table definitions
- **Schemas**: Pydantic validation models

### Frontend

- **Pages**: `src/app/` — Next.js App Router convention
- **Components**: `src/components/` — Reusable UI components
- **API calls**: `src/lib/api/` — Centralized API client functions
- **Types**: `src/types/` — Shared TypeScript interfaces
- **State**: `src/stores/` — Zustand stores

### Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Python files | snake_case | `movie_service.py` |
| Python classes | PascalCase | `MovieService` |
| TypeScript files | kebab-case | `seat-map.tsx` |
| TypeScript types | PascalCase | `AdminStats` |
| API routes | kebab-case | `/api/auth/change-password` |
| Database tables | snake_case | `reservation_groups` |

---

## Environment Variables

### Backend (`.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | — | MySQL host |
| `DB_USER` | Yes | — | MySQL username |
| `DB_PASSWORD` | Yes | — | MySQL password |
| `DB_NAME` | Yes | — | Database name |
| `SECRET_KEY` | Yes | — | JWT signing key |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Token TTL |
| `SMTP_HOST` | No | — | Email server |
| `SMTP_PORT` | No | `587` | Email port |
| `SMTP_USER` | No | — | Email username |
| `SMTP_PASS` | No | — | Email password |

### Frontend (`.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | Yes | — | Backend API URL |
