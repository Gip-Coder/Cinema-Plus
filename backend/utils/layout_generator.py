"""Theatre Layout Generator Engine.

Generates realistic cinema seat layouts given a total capacity and template type.
Pure logic module — no database dependency. Takes parameters, returns data structures.

Pricing zone hierarchy (enforced throughout):
    SCREEN (front)
    ↓ Normal   (closest to screen, cheapest)
    ↓ Executive (middle)
    ↓ Premium  (farthest from screen, most expensive)
"""

import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class SeatData:
    """Represents a single seat in a generated layout."""
    seat_code: str       # e.g., "A1"
    row_label: str       # e.g., "A"
    seat_number: int     # e.g., 1
    seat_type: str       # standard, wheelchair, couple, blocked
    category: str        # Normal, Executive, Premium
    position_x: int      # column index (0-indexed)
    position_y: int      # row index (0-indexed, 0 = closest to screen)
    is_active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TemplateConfig:
    """Configuration for a layout template."""
    name: str
    description: str
    default_cols: int
    max_cols: int
    min_cols: int
    has_center_aisle: bool
    has_side_aisles: bool
    seat_spacing: float       # multiplier for visual spacing
    row_spacing: float        # multiplier for visual row gaps
    aisle_width: int          # number of empty columns for center aisle
    side_aisle_width: int     # number of empty columns for side aisles
    auto_wheelchair: bool     # auto-place wheelchair seats
    wheelchair_count: int     # default wheelchair seats per side


@dataclass
class LayoutData:
    """Complete generated layout result."""
    seats: List[SeatData]
    rows: int
    cols: int               # total visual columns (including aisles)
    total_seats: int        # actual bookable seats
    template: str
    stats: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "seats": [s.to_dict() for s in self.seats],
            "rows": self.rows,
            "cols": self.cols,
            "total_seats": self.total_seats,
            "template": self.template,
            "stats": self.stats,
        }


# ─── Template Definitions ────────────────────────────────────────────

TEMPLATES: Dict[str, TemplateConfig] = {
    "STANDARD": TemplateConfig(
        name="STANDARD",
        description="Classic cinema layout with center aisle",
        default_cols=20,
        max_cols=24,
        min_cols=8,
        has_center_aisle=True,
        has_side_aisles=False,
        seat_spacing=1.0,
        row_spacing=1.0,
        aisle_width=2,
        side_aisle_width=0,
        auto_wheelchair=True,
        wheelchair_count=2,
    ),
    "IMAX": TemplateConfig(
        name="IMAX",
        description="Wide IMAX layout with center and side aisles",
        default_cols=26,
        max_cols=30,
        min_cols=16,
        has_center_aisle=True,
        has_side_aisles=True,
        seat_spacing=1.0,
        row_spacing=1.2,
        aisle_width=2,
        side_aisle_width=1,
        auto_wheelchair=True,
        wheelchair_count=3,
    ),
    "VIP": TemplateConfig(
        name="VIP",
        description="Spacious VIP layout with wider seats",
        default_cols=12,
        max_cols=14,
        min_cols=6,
        has_center_aisle=True,
        has_side_aisles=False,
        seat_spacing=1.5,
        row_spacing=1.5,
        aisle_width=2,
        side_aisle_width=0,
        auto_wheelchair=True,
        wheelchair_count=2,
    ),
    "RECLINER": TemplateConfig(
        name="RECLINER",
        description="Luxury recliner layout with extra spacing",
        default_cols=8,
        max_cols=10,
        min_cols=4,
        has_center_aisle=True,
        has_side_aisles=False,
        seat_spacing=2.0,
        row_spacing=2.0,
        aisle_width=2,
        side_aisle_width=0,
        auto_wheelchair=True,
        wheelchair_count=1,
    ),
    "CUSTOM": TemplateConfig(
        name="CUSTOM",
        description="Fully customizable layout",
        default_cols=20,
        max_cols=30,
        min_cols=4,
        has_center_aisle=True,
        has_side_aisles=False,
        seat_spacing=1.0,
        row_spacing=1.0,
        aisle_width=2,
        side_aisle_width=0,
        auto_wheelchair=False,
        wheelchair_count=0,
    ),
}


def get_template_config(template_name: str) -> TemplateConfig:
    """Returns configuration for the given template name."""
    return TEMPLATES.get(template_name.upper(), TEMPLATES["STANDARD"])


def get_all_templates() -> List[Dict[str, Any]]:
    """Returns all templates with their configurations for the API."""
    result = []
    for name, config in TEMPLATES.items():
        result.append({
            "name": config.name,
            "description": config.description,
            "default_cols": config.default_cols,
            "max_cols": config.max_cols,
            "min_cols": config.min_cols,
            "has_center_aisle": config.has_center_aisle,
            "has_side_aisles": config.has_side_aisles,
        })
    return result


def _row_label(index: int) -> str:
    """Converts a 0-based row index to a letter label: 0→A, 25→Z, 26→AA, etc."""
    if index < 26:
        return chr(65 + index)
    # For large layouts: AA, AB, AC...
    first = chr(65 + (index // 26) - 1)
    second = chr(65 + (index % 26))
    return first + second


def _compute_optimal_cols(total_seats: int, config: TemplateConfig) -> int:
    """Compute the optimal number of seat columns (excluding aisles) for a capacity."""
    seat_cols = config.default_cols
    
    if total_seats <= 30:
        seat_cols = max(config.min_cols, min(6, config.max_cols))
    elif total_seats <= 60:
        seat_cols = max(config.min_cols, min(10, config.max_cols))
    elif total_seats <= 120:
        seat_cols = max(config.min_cols, min(14, config.max_cols))
    elif total_seats <= 200:
        seat_cols = max(config.min_cols, min(18, config.max_cols))
    else:
        seat_cols = config.default_cols
    
    return min(seat_cols, config.max_cols)


def _assign_categories(total_rows: int) -> Dict[int, str]:
    """Assign pricing categories to rows.
    
    Hierarchy (from screen outward):
        Row 0 (front, closest to screen) → Normal (cheapest)
        Middle rows → Executive
        Last rows (back, farthest from screen) → Premium (most expensive)
    """
    if total_rows <= 0:
        return {}

    categories = {}

    if total_rows == 1:
        categories[0] = "Normal"
    elif total_rows == 2:
        categories[0] = "Normal"
        categories[1] = "Executive"
    elif total_rows == 3:
        categories[0] = "Normal"
        categories[1] = "Executive"
        categories[2] = "Premium"
    else:
        # Proportional split: ~25% Normal, ~50% Executive, ~25% Premium
        normal_count = max(1, total_rows // 4)
        premium_count = max(1, total_rows // 4)
        executive_count = total_rows - normal_count - premium_count
        if executive_count <= 0:
            executive_count = 1
            normal_count = max(1, (total_rows - executive_count) // 2)
            premium_count = total_rows - normal_count - executive_count

        for i in range(total_rows):
            if i < normal_count:
                categories[i] = "Normal"
            elif i < normal_count + executive_count:
                categories[i] = "Executive"
            else:
                categories[i] = "Premium"

    return categories


def _compute_aisle_columns(seat_cols: int, config: TemplateConfig) -> List[int]:
    """Determine which visual column indices are aisle gaps (non-seat)."""
    aisles = []
    total_visual_cols = seat_cols

    if config.has_center_aisle:
        center = seat_cols // 2
        for a in range(config.aisle_width):
            aisles.append(center + a)
        total_visual_cols += config.aisle_width

    if config.has_side_aisles:
        # Side aisles at ~25% and ~75%
        left_pos = seat_cols // 4
        right_pos = total_visual_cols - (seat_cols // 4) - config.side_aisle_width
        for a in range(config.side_aisle_width):
            aisles.append(left_pos + a)
            aisles.append(right_pos + a)
        total_visual_cols += config.side_aisle_width * 2

    return sorted(set(aisles)), total_visual_cols


def generate_layout(
    total_seats: int,
    template: str = "STANDARD",
    custom_cols: Optional[int] = None,
    layout_name: Optional[str] = None,
) -> LayoutData:
    """Generate a complete theatre seat layout.

    Args:
        total_seats: Target number of bookable seats.
        template: Template name (STANDARD, IMAX, VIP, RECLINER, CUSTOM).
        custom_cols: Override column count (for CUSTOM template).
        layout_name: Optional name for the layout.

    Returns:
        LayoutData with all seat definitions and metadata.
    """
    if total_seats <= 0:
        return LayoutData(seats=[], rows=0, cols=0, total_seats=0, template=template)

    config = get_template_config(template)

    # Determine seat columns (excluding aisles)
    if custom_cols and template == "CUSTOM":
        seat_cols = max(config.min_cols, min(custom_cols, config.max_cols))
    else:
        seat_cols = _compute_optimal_cols(total_seats, config)

    # Calculate rows needed
    total_rows = math.ceil(total_seats / seat_cols)

    # Compute aisle positions and total visual columns
    aisle_cols, total_visual_cols = _compute_aisle_columns(seat_cols, config)

    # Assign categories to rows
    row_categories = _assign_categories(total_rows)

    # Generate seats
    seats: List[SeatData] = []
    seats_placed = 0

    for row_idx in range(total_rows):
        row_label = _row_label(row_idx)
        category = row_categories.get(row_idx, "Normal")
        seat_num = 1  # Reset per row

        remaining = total_seats - seats_placed
        seats_in_this_row = min(seat_cols, remaining)

        if row_idx == total_rows - 1 and seats_in_this_row < seat_cols:
            # Last row may be partial — center the seats
            # Compute which seat columns to fill (centered in the visual grid)
            all_seat_positions = []
            visual_col = 0
            for vc in range(total_visual_cols):
                if vc in aisle_cols:
                    continue
                all_seat_positions.append(vc)

            # Center the partial row
            total_available = len(all_seat_positions)
            if seats_in_this_row >= total_available:
                used_positions = all_seat_positions
            else:
                start = (total_available - seats_in_this_row) // 2
                used_positions = all_seat_positions[start:start + seats_in_this_row]

            for vx in used_positions:
                seat_code = f"{row_label}{seat_num}"
                seats.append(SeatData(
                    seat_code=seat_code,
                    row_label=row_label,
                    seat_number=seat_num,
                    seat_type="standard",
                    category=category,
                    position_x=vx,
                    position_y=row_idx,
                ))
                seat_num += 1
                seats_placed += 1
        else:
            # Full row — fill all seat columns left to right
            for vx in range(total_visual_cols):
                if vx in aisle_cols:
                    continue
                if seats_placed >= total_seats:
                    break

                seat_code = f"{row_label}{seat_num}"
                seats.append(SeatData(
                    seat_code=seat_code,
                    row_label=row_label,
                    seat_number=seat_num,
                    seat_type="standard",
                    category=category,
                    position_x=vx,
                    position_y=row_idx,
                ))
                seat_num += 1
                seats_placed += 1

    # Auto-place wheelchair seats on the last row, outermost aisle positions
    if config.auto_wheelchair and config.wheelchair_count > 0 and len(seats) > 0:
        last_row = max(s.position_y for s in seats)
        last_row_seats = sorted(
            [s for s in seats if s.position_y == last_row],
            key=lambda s: s.position_x
        )
        # Mark outermost seats of the last row as wheelchair
        wc_placed = 0
        for s in last_row_seats:
            if wc_placed >= config.wheelchair_count:
                break
            s.seat_type = "wheelchair"
            wc_placed += 1
        # Also from the right side
        wc_placed = 0
        for s in reversed(last_row_seats):
            if s.seat_type == "wheelchair":
                continue
            if wc_placed >= config.wheelchair_count:
                break
            s.seat_type = "wheelchair"
            wc_placed += 1

    # Compute stats
    stats = compute_layout_stats(seats)

    return LayoutData(
        seats=seats,
        rows=total_rows,
        cols=total_visual_cols,
        total_seats=stats["total_active"],
        template=template,
        stats=stats,
    )


def compute_layout_stats(seats: List[SeatData]) -> Dict[str, int]:
    """Compute statistics from a list of seats."""
    active_seats = [s for s in seats if s.is_active]
    blocked = [s for s in seats if s.seat_type == "blocked"]
    wheelchair = [s for s in active_seats if s.seat_type == "wheelchair"]
    couple = [s for s in active_seats if s.seat_type == "couple"]
    normal = [s for s in active_seats if s.category == "Normal" and s.seat_type not in ("blocked",)]
    executive = [s for s in active_seats if s.category == "Executive" and s.seat_type not in ("blocked",)]
    premium = [s for s in active_seats if s.category == "Premium" and s.seat_type not in ("blocked",)]

    return {
        "total_seats": len(seats),
        "total_active": len(active_seats),
        "normal": len(normal),
        "executive": len(executive),
        "premium": len(premium),
        "wheelchair": len(wheelchair),
        "couple": len(couple),
        "blocked": len(blocked),
        "available_capacity": len(active_seats) - len(blocked),
    }


def validate_layout(seats: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """Validate a layout for consistency.
    
    Checks:
    - No duplicate seat codes
    - No overlapping positions
    - Valid categories
    - Valid seat types
    - Seat codes follow pattern (letter + number)
    
    Returns:
        (is_valid, list_of_error_messages)
    """
    errors = []
    valid_categories = {"Normal", "Executive", "Premium"}
    valid_types = {"standard", "wheelchair", "couple", "blocked"}

    seen_codes = set()
    seen_positions = set()

    for i, seat in enumerate(seats):
        code = seat.get("seat_code", "")
        pos = (seat.get("position_x"), seat.get("position_y"))
        category = seat.get("category", "")
        seat_type = seat.get("seat_type", "")

        # Duplicate code check
        if code in seen_codes:
            errors.append(f"Duplicate seat code: {code}")
        seen_codes.add(code)

        # Overlapping position check (only for active seats)
        if seat.get("is_active", True):
            if pos in seen_positions:
                errors.append(f"Overlapping position at ({pos[0]}, {pos[1]}) for seat {code}")
            seen_positions.add(pos)

        # Category validation
        if category not in valid_categories:
            errors.append(f"Invalid category '{category}' for seat {code}. Must be one of: {valid_categories}")

        # Type validation
        if seat_type not in valid_types:
            errors.append(f"Invalid seat type '{seat_type}' for seat {code}. Must be one of: {valid_types}")

        # Seat code format: at least one letter followed by at least one digit
        if code and (not code[0].isalpha() or not any(c.isdigit() for c in code)):
            errors.append(f"Invalid seat code format: '{code}'. Expected format like 'A1', 'B12'")

    return (len(errors) == 0, errors)
