# ── Stage 1: Build dependencies ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies required to build Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime system libraries only (not build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd --gid 1001 cinemaplus \
    && useradd --uid 1001 --gid cinemaplus --shell /bin/bash --create-home cinemaplus

# Copy application source
COPY --chown=cinemaplus:cinemaplus backend/ ./backend/
COPY --chown=cinemaplus:cinemaplus alembic/ ./alembic/
COPY --chown=cinemaplus:cinemaplus alembic.ini .
COPY --chown=cinemaplus:cinemaplus scripts/ ./scripts/

# Create upload directory structure with correct ownership
# IMPORTANT: In production, mount a persistent volume at /app/uploads/
RUN mkdir -p uploads/posters uploads/banners uploads/defaults \
    uploads/media/original uploads/media/medium uploads/media/thumbnails \
    && chown -R cinemaplus:cinemaplus uploads/

USER cinemaplus

# Expose the application port
EXPOSE 8001

# Production startup command:
# - Single worker (required while InMemoryCache is process-local)
# - No --reload (development only)
# - Binds to 0.0.0.0 so the container port is reachable
# - PORT env var allows deployment platforms to override the port
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 1"]
