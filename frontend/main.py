# pyrefly: ignore [missing-import]
from nicegui import ui
import sys
import os

# Add parent directory to path so we can run frontend independently but still import things if needed (though it shouldn't import backend code)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all pages to register them with nicegui
from frontend.pages.landing import landing_page
from frontend.pages.auth import login_page
from frontend.pages.movie_detail import movie_detail_page
from frontend.pages.seat_selection import seat_selection_page
from frontend.pages.billing import billing_page, user_bookings_page
from frontend.pages.admin_dashboard import admin_dashboard
from frontend.pages.profile import profile_page

# Application entry point
if __name__ in {"__main__", "__mp_main__"}:
    # Run the UI on port 8080
    ui.run(title="Cinema Plus - Ticket Booking", port=8080, dark=True, reload=True)
