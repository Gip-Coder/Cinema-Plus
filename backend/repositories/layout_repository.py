from sqlalchemy.orm import Session
from typing import List, Optional
from backend.models.layout import TheatreLayout, SeatDefinition


class LayoutRepository:
    """Data access layer for TheatreLayout and SeatDefinition."""

    def __init__(self, db: Session):
        self.db = db

    # ─── TheatreLayout CRUD ───────────────────────────────────────────

    def get_layout_by_id(self, layout_id: int) -> Optional[TheatreLayout]:
        return self.db.query(TheatreLayout).filter(
            TheatreLayout.id == layout_id
        ).first()

    def get_published_layout_for_screen(self, screen_id: int) -> Optional[TheatreLayout]:
        """Get the currently published layout for a screen."""
        return self.db.query(TheatreLayout).filter(
            TheatreLayout.screen_id == screen_id,
            TheatreLayout.is_published == True,
        ).first()

    def get_layouts_for_screen(self, screen_id: int) -> List[TheatreLayout]:
        """Get all layouts (drafts + published) for a screen."""
        return self.db.query(TheatreLayout).filter(
            TheatreLayout.screen_id == screen_id
        ).order_by(TheatreLayout.updated_at.desc()).all()

    def create_layout(self, layout: TheatreLayout) -> TheatreLayout:
        self.db.add(layout)
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def save_layout(self, layout: TheatreLayout) -> TheatreLayout:
        self.db.add(layout)
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def delete_layout(self, layout: TheatreLayout) -> None:
        self.db.delete(layout)
        self.db.commit()

    def unpublish_all_for_screen(self, screen_id: int) -> None:
        """Mark all layouts for a screen as unpublished."""
        self.db.query(TheatreLayout).filter(
            TheatreLayout.screen_id == screen_id,
            TheatreLayout.is_published == True,
        ).update({"is_published": False}, synchronize_session=False)
        self.db.commit()

    # ─── SeatDefinition CRUD ──────────────────────────────────────────

    def get_seats_for_layout(self, layout_id: int) -> List[SeatDefinition]:
        return self.db.query(SeatDefinition).filter(
            SeatDefinition.layout_id == layout_id
        ).order_by(SeatDefinition.position_y, SeatDefinition.position_x).all()

    def bulk_create_seats(self, seats: List[SeatDefinition]) -> List[SeatDefinition]:
        """Create multiple seat definitions in bulk."""
        self.db.add_all(seats)
        self.db.commit()
        for s in seats:
            self.db.refresh(s)
        return seats

    def delete_seats_for_layout(self, layout_id: int) -> int:
        """Delete all seat definitions for a layout."""
        deleted = self.db.query(SeatDefinition).filter(
            SeatDefinition.layout_id == layout_id
        ).delete(synchronize_session=False)
        self.db.commit()
        return deleted

    def get_seat_by_code(self, layout_id: int, seat_code: str) -> Optional[SeatDefinition]:
        return self.db.query(SeatDefinition).filter(
            SeatDefinition.layout_id == layout_id,
            SeatDefinition.seat_code == seat_code,
        ).first()
