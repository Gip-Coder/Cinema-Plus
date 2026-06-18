from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.repositories.layout_repository import LayoutRepository
from backend.exceptions.base import NotFoundException, BadRequestException, ConflictException
from backend.models.layout import TheatreLayout, SeatDefinition
from backend.models.theatre import Screen
from backend.models.models import User
from backend.schemas.layout import LayoutSaveRequest, LayoutBulkSeatUpdate, SeatDefinitionInput
from backend.utils.layout_generator import (
    generate_layout, validate_layout, compute_layout_stats, get_all_templates, SeatData
)
from backend.utils.cache import cache
from backend.utils.audit_logger import log_action


class LayoutService:
    """Business logic for theatre layout management."""

    def __init__(self, db: Session):
        self.layout_repo = LayoutRepository(db)
        self.db = db

    # ─── Preview (no persistence) ────────────────────────────────────

    async def generate_preview(
        self, total_seats: int, template: str = "STANDARD", custom_cols: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a layout preview without saving to DB."""
        layout_data = generate_layout(
            total_seats=total_seats,
            template=template,
            custom_cols=custom_cols,
        )
        return layout_data.to_dict()

    # ─── Persistence ─────────────────────────────────────────────────

    async def save_layout(
        self,
        request: LayoutSaveRequest,
        current_user: User,
        client_ip: str,
    ) -> TheatreLayout:
        """Save a layout to the database (as draft)."""
        # Verify screen exists
        screen = self.db.query(Screen).filter(Screen.id == request.screen_id).first()
        if not screen:
            raise NotFoundException("Screen not found")

        # Validate seats
        seats_dicts = [s.model_dump() for s in request.seats]
        is_valid, errors = validate_layout(seats_dicts)
        if not is_valid:
            raise BadRequestException(f"Layout validation failed: {'; '.join(errors)}")

        active_seats = [s for s in request.seats if s.is_active]

        # Create layout record
        layout = TheatreLayout(
            theatre_id=screen.theatre_id,
            screen_id=request.screen_id,
            layout_name=request.layout_name,
            layout_type=request.layout_type,
            total_seats=len(active_seats),
            rows=request.rows,
            cols=request.cols,
            is_published=False,
        )
        layout = self.layout_repo.create_layout(layout)

        # Create seat definitions
        seat_models = []
        for s in request.seats:
            seat_models.append(SeatDefinition(
                layout_id=layout.id,
                seat_code=s.seat_code,
                row_label=s.row_label,
                seat_number=s.seat_number,
                seat_type=s.seat_type,
                category=s.category,
                position_x=s.position_x,
                position_y=s.position_y,
                is_active=s.is_active,
            ))
        self.layout_repo.bulk_create_seats(seat_models)

        # Refresh to load seats relationship
        self.db.refresh(layout)

        log_action(
            self.db, current_user.id, "layout", layout.id, "create",
            new_value={"screen_id": request.screen_id, "total_seats": len(active_seats), "template": request.layout_type},
            ip_address=client_ip,
        )
        cache.invalidate("layout:*")
        return layout

    async def publish_layout(
        self, layout_id: int, current_user: User, client_ip: str
    ) -> TheatreLayout:
        """Publish a layout, unpublishing any other layout for the same screen."""
        layout = self.layout_repo.get_layout_by_id(layout_id)
        if not layout:
            raise NotFoundException("Layout not found")

        # Unpublish all other layouts for this screen
        self.layout_repo.unpublish_all_for_screen(layout.screen_id)

        # Publish this one
        layout.is_published = True
        layout = self.layout_repo.save_layout(layout)

        # Also update the screen's total_seats to match
        screen = self.db.query(Screen).filter(Screen.id == layout.screen_id).first()
        if screen:
            screen.total_seats = layout.total_seats
            self.db.add(screen)
            self.db.commit()

        log_action(
            self.db, current_user.id, "layout", layout_id, "publish",
            new_value={"screen_id": layout.screen_id, "total_seats": layout.total_seats},
            ip_address=client_ip,
        )
        cache.invalidate("layout:*")
        cache.invalidate("movie:*")
        return layout

    # ─── Retrieval ───────────────────────────────────────────────────

    async def get_layout_by_id(self, layout_id: int) -> TheatreLayout:
        layout = self.layout_repo.get_layout_by_id(layout_id)
        if not layout:
            raise NotFoundException("Layout not found")
        return layout

    async def get_layout_for_screen(self, screen_id: int) -> Optional[TheatreLayout]:
        """Get the published layout for a screen. Returns None if no published layout."""
        cache_key = f"layout:screen:{screen_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        layout = self.layout_repo.get_published_layout_for_screen(screen_id)
        if layout:
            cache.set(cache_key, layout, ttl=60)
        return layout

    async def get_all_layouts_for_screen(self, screen_id: int) -> List[TheatreLayout]:
        return self.layout_repo.get_layouts_for_screen(screen_id)

    # ─── Seat Updates ────────────────────────────────────────────────

    async def update_layout_seats(
        self,
        layout_id: int,
        update: LayoutBulkSeatUpdate,
        current_user: User,
        client_ip: str,
    ) -> TheatreLayout:
        """Replace all seats in a layout with the provided set."""
        layout = self.layout_repo.get_layout_by_id(layout_id)
        if not layout:
            raise NotFoundException("Layout not found")

        # Validate new seats
        seats_dicts = [s.model_dump() for s in update.seats]
        is_valid, errors = validate_layout(seats_dicts)
        if not is_valid:
            raise BadRequestException(f"Layout validation failed: {'; '.join(errors)}")

        # Delete old seats and create new ones
        self.layout_repo.delete_seats_for_layout(layout_id)

        seat_models = []
        active_count = 0
        for s in update.seats:
            seat_models.append(SeatDefinition(
                layout_id=layout_id,
                seat_code=s.seat_code,
                row_label=s.row_label,
                seat_number=s.seat_number,
                seat_type=s.seat_type,
                category=s.category,
                position_x=s.position_x,
                position_y=s.position_y,
                is_active=s.is_active,
            ))
            if s.is_active:
                active_count += 1

        self.layout_repo.bulk_create_seats(seat_models)

        # Update layout metadata
        layout.total_seats = active_count
        layout.rows = update.rows
        layout.cols = update.cols
        layout = self.layout_repo.save_layout(layout)

        self.db.refresh(layout)

        log_action(
            self.db, current_user.id, "layout", layout_id, "update_seats",
            new_value={"total_seats": active_count},
            ip_address=client_ip,
        )
        cache.invalidate("layout:*")
        return layout

    # ─── Delete ──────────────────────────────────────────────────────

    async def delete_layout(
        self, layout_id: int, current_user: User, client_ip: str
    ) -> None:
        layout = self.layout_repo.get_layout_by_id(layout_id)
        if not layout:
            raise NotFoundException("Layout not found")
        if layout.is_published:
            raise BadRequestException("Cannot delete a published layout. Unpublish it first or publish another layout.")

        log_action(
            self.db, current_user.id, "layout", layout_id, "delete",
            old_value={"screen_id": layout.screen_id, "total_seats": layout.total_seats},
            ip_address=client_ip,
        )
        self.layout_repo.delete_layout(layout)
        cache.invalidate("layout:*")

    # ─── Statistics ──────────────────────────────────────────────────

    async def get_layout_stats(self, layout_id: int) -> Dict[str, int]:
        """Compute live statistics for a layout."""
        layout = self.layout_repo.get_layout_by_id(layout_id)
        if not layout:
            raise NotFoundException("Layout not found")

        seats_data = []
        for s in layout.seats:
            seats_data.append(SeatData(
                seat_code=s.seat_code,
                row_label=s.row_label,
                seat_number=s.seat_number,
                seat_type=s.seat_type,
                category=s.category,
                position_x=s.position_x,
                position_y=s.position_y,
                is_active=s.is_active,
            ))
        return compute_layout_stats(seats_data)

    # ─── Templates ───────────────────────────────────────────────────

    async def get_templates(self) -> List[Dict[str, Any]]:
        return get_all_templates()
