import sys
import os
from pathlib import Path

# Add the project root before importing app packages so this file works when run directly.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# pyrefly: ignore [missing-import]
from nicegui import ui


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Import all pages to register them with nicegui
from frontend.pages.landing import landing_page
from frontend.pages.auth import login_page
from frontend.pages.movie_detail import movie_detail_page
from frontend.pages.seat_selection import seat_selection_page
from frontend.pages.billing import billing_page, user_bookings_page
from frontend.pages.admin_dashboard import admin_dashboard
from frontend.pages.profile import profile_page
from frontend.pages.checkout import checkout_page
from frontend.pages.layout_designer import layout_designer_page

# Application entry point
if __name__ in {"__main__", "__mp_main__"}:
    frontend_port = int(os.getenv("FRONTEND_PORT", "8080"))
    reload_enabled = _env_flag("NICEGUI_RELOAD", default=False)
    ui.run(
        title="Cinema Plus - Ticket Booking",
        port=frontend_port,
        dark=True,
        reload=reload_enabled,
    )
