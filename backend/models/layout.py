from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime


class TheatreLayout(Base):
    """Represents a complete seating layout for a screen.

    A screen can have multiple layout versions (drafts and published).
    Only one layout may be published at a time; that version drives
    reservations and customer seat selection.

    status: 'draft' | 'published'  (mirrors is_published for API clarity)
    version: monotonically increasing per screen when new versions are created
    """
    __tablename__ = "theatre_layouts"

    id = Column(Integer, primary_key=True, index=True)
    theatre_id = Column(Integer, ForeignKey("theatres.id"), index=True, nullable=False)
    screen_id = Column(Integer, ForeignKey("screens.id"), index=True, nullable=False)
    layout_name = Column(String(100), nullable=False, default="Default Layout")
    layout_type = Column(String(50), nullable=False, default="STANDARD")  # STANDARD, IMAX, VIP, RECLINER, CUSTOM
    total_seats = Column(Integer, nullable=False, default=0)
    rows = Column(Integer, nullable=False, default=0)
    cols = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft, published
    version = Column(Integer, nullable=False, default=1, index=True)
    is_published = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    theatre = relationship("Theatre")
    screen = relationship("Screen")
    seats = relationship("SeatDefinition", back_populates="layout", cascade="all, delete-orphan", lazy="selectin")


class SeatDefinition(Base):
    """Defines a single seat within a theatre layout.

    Each seat has:
    - A unique seat_code within the layout (e.g., 'A1', 'B12')
    - Grid coordinates (position_x, position_y) for visual placement
    - A category for pricing (Normal / Executive / Premium)
    - A seat_type for special handling (standard / wheelchair / couple / blocked)

    is_wheelchair, is_couple, is_blocked are derived from seat_type for API
    compatibility; seat_type remains the canonical stored value.
    """
    __tablename__ = "seat_definitions"

    id = Column(Integer, primary_key=True, index=True)
    layout_id = Column(Integer, ForeignKey("theatre_layouts.id", ondelete="CASCADE"), index=True, nullable=False)
    seat_code = Column(String(10), nullable=False, index=True)  # e.g., "A1", "B12"
    row_label = Column(String(5), nullable=False)   # e.g., "A", "B", "AA"
    seat_number = Column(Integer, nullable=False)    # e.g., 1, 2, 12
    seat_type = Column(String(20), nullable=False, default="standard")  # standard, wheelchair, couple, blocked
    category = Column(String(20), nullable=False, default="Normal")     # Normal, Executive, Premium
    position_x = Column(Integer, nullable=False)  # Column position in grid (0-indexed)
    position_y = Column(Integer, nullable=False)  # Row position in grid (0-indexed, 0 = closest to screen)
    is_active = Column(Boolean, default=True)

    # Relationships
    layout = relationship("TheatreLayout", back_populates="seats")

    __table_args__ = (
        UniqueConstraint('layout_id', 'seat_code', name='uq_layout_seat_code'),
        UniqueConstraint('layout_id', 'position_x', 'position_y', name='uq_layout_position'),
    )

    @property
    def is_wheelchair(self) -> bool:
        return self.seat_type == "wheelchair"

    @property
    def is_couple(self) -> bool:
        return self.seat_type == "couple"

    @property
    def is_blocked(self) -> bool:
        return self.seat_type == "blocked"
