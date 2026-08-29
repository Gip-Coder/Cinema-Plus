from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from backend.repositories.booking_repository import BookingRepository
from backend.repositories.movie_repository import MovieRepository
from backend.repositories.user_repository import UserRepository
from backend.exceptions.booking_exceptions import BookingNotFoundException
from backend.models.models import Movie, Booking, User, BookedSeat, AuditLog
from backend.utils.cache import cache
from typing import List, Dict

class AdminService:
    def __init__(self, db: Session):
        self.booking_repo = BookingRepository(db)
        self.movie_repo = MovieRepository(db)
        self.user_repo = UserRepository(db)
        self.db = db

    async def get_admin_stats(self) -> Dict:
        cache_key = "admin:stats"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        total_movies = self.db.query(func.count(Movie.id)).scalar() or 0
        total_bookings = self.db.query(func.count(Booking.id)).filter(Booking.status == 'confirmed').scalar() or 0
        total_revenue = self.db.query(func.sum(Booking.total_amount)).filter(Booking.status == 'confirmed').scalar() or 0.0
        total_users = self.user_repo.get_user_count()

        from datetime import date
        today_revenue = self.db.query(func.sum(Booking.total_amount)).filter(
            Booking.status == 'confirmed',
            func.date(Booking.booking_date) == date.today()
        ).scalar() or 0.0

        from backend.models.reservation import ReservationGroup
        active_reservations = self.db.query(func.count(ReservationGroup.id)).filter(
            ReservationGroup.status == "active"
        ).scalar() or 0

        # Most booked movie
        most_booked = self.db.query(
            Movie.title, func.count(Booking.id).label('booking_count')
        ).join(Booking).filter(Booking.status == 'confirmed').group_by(Movie.id).order_by(desc('booking_count')).first()
        most_booked_title = most_booked.title if most_booked else "N/A"

        # Occupancy percentage (220 capacity)
        total_booked_seats = self.db.query(func.count(BookedSeat.id)).scalar() or 0
        capacity = total_movies * 220
        occupancy = (total_booked_seats / capacity * 100) if capacity > 0 else 0.0

        stats_data = {
            "total_movies": total_movies,
            "total_bookings": total_bookings,
            "total_revenue": total_revenue,
            "total_users": total_users,
            "most_booked_movie": most_booked_title,
            "occupancy_percentage": round(occupancy, 1),
            "today_revenue": float(today_revenue),
            "active_reservations": active_reservations
        }
        cache.set(cache_key, stats_data, ttl=10)
        return stats_data

    async def get_revenue_chart(self) -> Dict:
        cache_key = "admin:revenue_chart"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        results = self.db.query(
            func.date(Booking.booking_date).label('date'),
            func.sum(Booking.total_amount).label('revenue')
        ).filter(Booking.status == 'confirmed').group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date)).all()

        dates = [str(r.date) for r in results]
        revenues = [float(r.revenue) for r in results]
        chart_data = {"dates": dates, "revenues": revenues}
        cache.set(cache_key, chart_data, ttl=30)
        return chart_data

    async def get_booking_trends(self) -> Dict:
        cache_key = "admin:booking_trends"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        results = self.db.query(
            func.date(Booking.booking_date).label('date'),
            func.count(Booking.id).label('count')
        ).filter(Booking.status == 'confirmed').group_by(func.date(Booking.booking_date)).order_by(func.date(Booking.booking_date)).all()

        dates = [str(r.date) for r in results]
        counts = [r.count for r in results]
        trends_data = {"dates": dates, "counts": counts}
        cache.set(cache_key, trends_data, ttl=30)
        return trends_data

    async def get_all_bookings(self, skip: int = 0, limit: int = 100) -> List[Booking]:
        return self.booking_repo.get_all_bookings(skip, limit)

    async def cancel_booking(self, booking_id: int) -> None:
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        booking.status = "cancelled"
        self.booking_repo.delete_booked_seats_by_booking_id(booking_id)
        self.booking_repo.commit()
        cache.invalidate("admin:*")

    async def delete_booking(self, booking_id: int) -> None:
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        self.booking_repo.delete(booking)
        cache.invalidate("admin:*")

    async def get_audit_logs(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        from backend.repositories.audit_repository import AuditLogRepository
        repo = AuditLogRepository(self.db)
        return repo.get_all(skip, limit)

    async def get_system_health(self) -> Dict:
        import os
        import time
        from backend.core.config import settings
        from backend.utils.cache import cache

        # Test db connection speed.
        # NOTE: this previously called `self.db.execute(func.select(1))`,
        # which is NOT a SELECT statement — `func` (sqlalchemy.func) builds a
        # call to a SQL *function* literally named "select", which doesn't
        # exist on any engine (MySQL or otherwise). That always raised an
        # exception, which is why this always reported "unhealthy" with
        # 0ms latency regardless of the real database's health — the actual
        # production /health endpoint (backend/main.py) always used the
        # correct `text("SELECT 1")` and was never affected.
        start_time = time.time()
        try:
            self.db.execute(text("SELECT 1"))
            db_status = "healthy"
            db_latency_ms = round((time.time() - start_time) * 1000, 2)
        except Exception:
            db_status = "unhealthy"
            db_latency_ms = 0.0

        # Real database engine, so the dashboard reflects whatever this
        # deployment actually runs (MySQL in production, SQLite in tests)
        # instead of a hardcoded, possibly stale label.
        try:
            db_engine_name = self.db.get_bind().dialect.name
        except Exception:
            db_engine_name = "unknown"

        # Test cache/redis connection
        try:
            cache.set("healthcheck", "ok", ttl=5)
            val = cache.get("healthcheck")
            cache_status = "healthy" if val == "ok" else "unhealthy"
        except Exception:
            cache_status = "unhealthy"

        # Real storage check: an actual write+delete against the configured
        # uploads directory, same technique as backend/main.py's /health
        # endpoint. This does NOT confirm the path is backed by a Railway
        # persistent Volume (nothing in-process can observe that) — it only
        # confirms the directory is currently writable.
        try:
            os.makedirs("uploads", exist_ok=True)
            test_file = os.path.join("uploads", ".admin_health_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            storage_status = "healthy"
        except Exception:
            storage_status = "unhealthy"

        # The seat-reservation double-booking guard is a permanent DB-level
        # constraint (see alembic migration f3a1c9b8d2e4 and
        # backend/models/booking.py's uq_booked_seats_show_seat), not a
        # toggleable runtime service — there is no separate "engine" process
        # to poll, so this reports the real, static configuration instead of
        # a fabricated live status.
        reservation_info = {
            "mechanism": "database_unique_constraint",
            "hold_minutes": settings.RESERVATION_TIMEOUT_MINUTES,
        }

        # There is no scheduler/worker infrastructure in this codebase at all
        # (no APScheduler/Celery/cron/periodic asyncio task) — confirmed by
        # source inspection, not assumed. Each of these previously showed a
        # fabricated ACTIVE/IDLE badge with a fake "last run" timestamp.
        scheduler_tasks = {
            "reservation_expiry_cleanup": {
                "status": "on_demand",
                "detail": (
                    "Not a scheduled job. Runs inline, synchronously, at the "
                    "start of every new reservation request "
                    "(ReservationService.cleanup_expired_reservations) — "
                    "only sweeps expired holds when someone happens to "
                    "reserve a seat afterward, not on a timer."
                ),
            },
            "daily_revenue_compiler": {
                "status": "not_configured",
                "detail": (
                    "No background job exists. Revenue/booking-trend "
                    "analytics are computed on demand per request, with a "
                    "short-lived in-memory cache (see AdminService.get_admin_stats)."
                ),
            },
            "media_thumbnail_optimizer": {
                "status": "not_configured",
                "detail": (
                    "No background job exists. Thumbnails are generated "
                    "synchronously at upload time "
                    "(backend/utils/media_processor.py), not by a scheduled sweep."
                ),
            },
        }

        # System resources (graceful check for psutil)
        cpu_usage = 0.0
        mem_percent = 0.0
        mem_used_gb = 0.0
        mem_total_gb = 0.0
        disk_usage_percent = 0.0
        disk_free_gb = 0.0
        
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            mem_percent = memory.percent
            mem_used_gb = round(memory.used / (1024**3), 2)
            mem_total_gb = round(memory.total / (1024**3), 2)
            
            # Simple check for cross-platform disk usage
            import os
            if os.name == 'nt':
                # Windows
                disk = psutil.disk_usage('C:\\')
            else:
                disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            disk_free_gb = round(disk.free / (1024**3), 2)
        except Exception:
            pass
        
        overall_healthy = db_status == "healthy" and cache_status == "healthy" and storage_status == "healthy"
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms,
                "engine": db_engine_name,
            },
            "cache": {
                "status": cache_status,
                # This is backend/utils/cache.py's InMemoryCache — a plain
                # process-local dict, not Redis. Only correct for a
                # single-worker deployment (see Dockerfile: --workers 1).
                "scope": "process-local (single worker only)",
            },
            "storage": {
                "status": storage_status,
                "path": "uploads/",
                "note": (
                    "Write test against the local filesystem only. Whether "
                    "this path is backed by a persistent Railway Volume "
                    "cannot be determined from inside the application — "
                    "confirm the Volume mount in the Railway service settings."
                ),
            },
            "reservation": reservation_info,
            "scheduler_tasks": scheduler_tasks,
            "system": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": mem_percent,
                "memory_used_gb": mem_used_gb,
                "memory_total_gb": mem_total_gb,
                "disk_usage_percent": disk_usage_percent,
                "disk_free_gb": disk_free_gb
            },
            "uptime_seconds": round(time.time() - start_time, 2)
        }
