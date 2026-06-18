from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.repositories.booking_repository import BookingRepository
from backend.repositories.movie_repository import MovieRepository
from backend.repositories.user_repository import UserRepository
from backend.exceptions.booking_exceptions import BookingNotFoundException
from backend.models.models import Movie, Booking, User, BookedSeat
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
            "occupancy_percentage": round(occupancy, 1)
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
