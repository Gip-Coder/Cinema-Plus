from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Request Schemas ──────────────────────────────────────────────────

class LayoutGenerateRequest(BaseModel):
    """Request to generate a preview layout (not saved to DB)."""
    total_seats: int = Field(..., ge=1, le=2000, description="Target number of bookable seats")
    template: str = Field(default="STANDARD", description="Template: STANDARD, IMAX, VIP, RECLINER, CUSTOM")
    custom_cols: Optional[int] = Field(default=None, ge=4, le=30, description="Override columns (CUSTOM only)")


class SeatDefinitionInput(BaseModel):
    """A single seat definition for save/update operations."""
    seat_code: str = Field(..., max_length=10)
    row_label: str = Field(..., max_length=5)
    seat_number: int = Field(..., ge=1)
    seat_type: str = Field(default="standard", description="standard, wheelchair, couple, blocked")
    category: str = Field(default="Normal", description="Normal, Executive, Premium")
    position_x: int = Field(..., ge=0)
    position_y: int = Field(..., ge=0)
    is_active: bool = True


class LayoutSaveRequest(BaseModel):
    """Request to save a layout to the database."""
    screen_id: int
    layout_name: str = Field(default="Default Layout", max_length=100)
    layout_type: str = Field(default="STANDARD", description="STANDARD, IMAX, VIP, RECLINER, CUSTOM")
    seats: List[SeatDefinitionInput]
    rows: int = Field(..., ge=1)
    cols: int = Field(..., ge=1)


class LayoutBulkSeatUpdate(BaseModel):
    """Bulk update seats in an existing layout."""
    seats: List[SeatDefinitionInput]
    rows: int = Field(..., ge=1)
    cols: int = Field(..., ge=1)


# ─── Response Schemas ─────────────────────────────────────────────────

class SeatDefinitionResponse(BaseModel):
    """Response for a single seat definition."""
    id: int
    seat_code: str
    row_label: str
    seat_number: int
    seat_type: str
    category: str
    position_x: int
    position_y: int
    is_active: bool

    class Config:
        from_attributes = True


class TheatreLayoutResponse(BaseModel):
    """Response for a complete theatre layout."""
    id: int
    theatre_id: int
    screen_id: int
    layout_name: str
    layout_type: str
    total_seats: int
    rows: int
    cols: int
    is_published: bool
    seats: List[SeatDefinitionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LayoutPreviewResponse(BaseModel):
    """Response for a generated (unsaved) layout preview."""
    seats: List[Dict[str, Any]]
    rows: int
    cols: int
    total_seats: int
    template: str
    stats: Dict[str, int]


class LayoutStatsResponse(BaseModel):
    """Live statistics for a layout."""
    total_seats: int = 0
    total_active: int = 0
    normal: int = 0
    executive: int = 0
    premium: int = 0
    wheelchair: int = 0
    couple: int = 0
    blocked: int = 0
    available_capacity: int = 0


class LayoutTemplateResponse(BaseModel):
    """Template information."""
    name: str
    description: str
    default_cols: int
    max_cols: int
    min_cols: int
    has_center_aisle: bool
    has_side_aisles: bool
