from sqlalchemy.orm import Session
from sqlalchemy import func, desc
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
        import time
        from backend.utils.cache import cache
        
        # Test db connection speed
        start_time = time.time()
        try:
            self.db.execute(func.select(1))
            db_status = "healthy"
            db_latency_ms = round((time.time() - start_time) * 1000, 2)
        except Exception:
            db_status = "unhealthy"
            db_latency_ms = 0.0

        # Test cache/redis connection
        try:
            cache.set("healthcheck", "ok", ttl=5)
            val = cache.get("healthcheck")
            cache_status = "healthy" if val == "ok" else "unhealthy"
        except Exception:
            cache_status = "unhealthy"

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
        
        return {
            "status": "healthy" if db_status == "healthy" and cache_status == "healthy" else "degraded",
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms
            },
            "cache": {
                "status": cache_status
            },
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
