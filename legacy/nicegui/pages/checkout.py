from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
from datetime import datetime, timezone
import asyncio

def get_seat_category_local(total_seats: int, seat_name: str) -> str:
    import math
    cols = 20 if total_seats > 100 else 10
    total_rows_needed = math.ceil(total_seats / cols)
    
    if total_rows_needed == 1:
        normal_rows_count = 1
        executive_rows_count = 0
        premium_rows_count = 0
    elif total_rows_needed == 2:
        normal_rows_count = 1
        executive_rows_count = 1
        premium_rows_count = 0
    else:
        premium_rows_count = max(1, total_rows_needed // 4)
        executive_rows_count = max(1, total_rows_needed // 2)
        normal_rows_count = total_rows_needed - premium_rows_count - executive_rows_count
        if normal_rows_count <= 0:
            normal_rows_count = 1
            executive_rows_count = total_rows_needed - premium_rows_count - normal_rows_count

    row_letters = [chr(65 + i) for i in range(total_rows_needed)]
    executive_start = normal_rows_count
    premium_start = normal_rows_count + executive_rows_count
    
    row_letter = seat_name[0]
    row_idx = row_letters.index(row_letter) if row_letter in row_letters else 0
    
    if row_idx >= premium_start:
        return "Premium"
    elif row_idx >= executive_start:
        return "Executive"
    else:
        return "Normal"

@ui.page('/checkout/{group_id}')
async def checkout_page(group_id: int):
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    if api_client.is_admin():
        ui.navigate.to('/admin')
        return
        
    apply_theme()
    navbar()
    
    # 1. Fetch reservation group details
    try:
        reservation = await api_client.get_reservation(group_id)
    except Exception as e:
        ui.notify(f"Error loading reservation: {e}", type="negative")
        ui.navigate.to("/")
        return
        
    if not reservation:
        ui.notify("Reservation not found.", type="negative")
        ui.navigate.to("/")
        return

    # Check if already processed
    if reservation["status"] == "converted":
        ui.notify("This reservation has already been confirmed.", type="info")
        ui.navigate.to("/bookings")
        return
    elif reservation["status"] in ("expired", "cancelled"):
        ui.notify("This reservation is no longer active.", type="warning")
        ui.navigate.to(f"/book/{reservation['show_id']}")
        return

    # 2. Fetch show and movie details
    try:
        show = await api_client.get_show(reservation["show_id"])
        if not show:
            ui.notify("Show details not found.", type="negative")
            ui.navigate.to("/")
            return
        movie = await api_client.get_movie(show["movie_id"])
        if not movie:
            ui.notify("Movie details not found.", type="negative")
            ui.navigate.to("/")
            return
    except Exception as e:
        ui.notify(f"Error loading details: {e}", type="negative")
        ui.navigate.to("/")
        return

    # Calculate price details per seat
    seats_details = []
    total_amount = 0.0
    total_seats = show.get("screen", {}).get("total_seats", 220)
    
    # Fetch layout for screen if available
    layout = None
    try:
        layout = await api_client.get_layout_for_screen(show["screen_id"])
    except Exception as e:
        print(f"Error fetching layout in checkout: {e}")
        
    layout_seats_map = {}
    if layout:
        layout_seats_map = {s['seat_code']: s['category'] for s in layout.get('seats', []) if s.get('is_active', True)}

    # Pre-cache pricing rules for show
    pricing_cache = {}
    for cat in ["Normal", "Executive", "Premium"]:
        try:
            p_details = await api_client.get_seat_price_details(show["id"], cat)
            pricing_cache[cat] = p_details.get("final_price", 150.0)
        except Exception:
            pricing_cache[cat] = 150.0 if cat == "Normal" else (220.0 if cat == "Executive" else 300.0)

    for seat in reservation["reserved_seats"]:
        seat_name = seat["seat_id"]
        category = layout_seats_map.get(seat_name) or get_seat_category_local(total_seats, seat_name)
        price = pricing_cache.get(category, 150.0)
        total_amount += price
        seats_details.append({
            "seat_name": seat_name,
            "category": category,
            "price": price
        })

    # Countdown calculation
    expires_str = reservation["expires_at"].replace("Z", "+00:00")
    try:
        expiry_dt = datetime.fromisoformat(expires_str)
        if expiry_dt.tzinfo is not None:
            expiry_dt = expiry_dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        expiry_dt = datetime.now(timezone.utc).replace(tzinfo=None)

    seconds_left = int((expiry_dt - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())

    async def cancel_action():
        res = await api_client.cancel_reservation(group_id)
        if res:
            ui.notify("Reservation cancelled. Seats released.", type="info")
        ui.navigate.to(f"/book/{reservation['show_id']}")

    async def confirm_action():
        confirm_btn.set_enabled(False)
        cancel_btn.set_enabled(False)
        try:
            booking = await api_client.confirm_reservation(group_id)
            if booking:
                ui.notify("Booking confirmed successfully!", type="positive")
                timer.deactivate()
                ui.navigate.to(f"/billing/{booking['id']}")
            else:
                ui.notify("Failed to confirm booking. Session may have expired.", type="negative")
                confirm_btn.set_enabled(True)
                cancel_btn.set_enabled(True)
        except Exception as e:
            ui.notify(f"Booking error: {e}", type="negative")
            confirm_btn.set_enabled(True)
            cancel_btn.set_enabled(True)

    show_id = reservation["show_id"]

    def tick():
        nonlocal seconds_left
        seconds_left -= 1
        if seconds_left <= 0:
            timer.deactivate()
            timer_label.set_text("EXPIRED")
            timer_label.classes(remove='text-amber-500', add='text-red-500')
            confirm_btn.set_enabled(False)
            ui.notify("Your seat reservation session has expired.", type="negative")
            ui.timer(2.0, lambda: ui.navigate.to(f"/book/{show_id}"), once=True)
        else:
            mins = seconds_left // 60
            secs = seconds_left % 60
            timer_label.set_text(f"{mins:02d}:{secs:02d}")
            progress_bar.set_value(max(0.0, min(1.0, seconds_left / 600.0)))

    timer = ui.timer(1.0, tick)

    with ui.column().classes('w-full items-center p-8 max-w-6xl mx-auto'):
        ui.label('CHECKOUT & CONFIRMATION').classes('text-3xl font-extrabold text-white mb-2 tracking-wider')
        ui.label('Please review and complete your booking details below.').classes('text-sm text-gray-400 mb-8')

        # Countdown card
        with ui.card().classes('w-full bg-gradient-to-r from-neutral-900 to-zinc-900 border border-zinc-800 p-6 mb-8 rounded-2xl flex-row items-center justify-between'):
            with ui.column():
                ui.label('Reservation Session Time Remaining').classes('text-xs text-gray-500 font-bold uppercase tracking-wider')
                timer_label = ui.label('--:--').classes('text-4xl font-extrabold text-amber-500 font-mono')
            progress_bar = ui.linear_progress(value=1.0).classes('w-1/2')

        # Main checkout grid
        with ui.grid(columns='1fr 1.2fr').classes('w-full gap-8'):
            # Left: Movie Details & Summary
            with ui.column().classes('gap-4'):
                if movie.get("poster_image_url"):
                    poster_url = str(api_client.client.base_url).rstrip("/") + movie["poster_image_url"]
                    ui.image(poster_url).classes('w-full h-80 rounded-2xl object-cover shadow-2xl border border-zinc-800')
                else:
                    with ui.element('div').classes('w-full h-80 bg-zinc-800 rounded-2xl border border-zinc-700 flex items-center justify-center'):
                        ui.html('<i class="material-icons text-5xl text-gray-500">local_movies</i>')

                with ui.card().classes('glass-card p-6 w-full'):
                    ui.label(movie["title"]).classes('text-2xl font-bold text-white')
                    ui.label(f"Genre: {movie.get('genre', 'N/A')} | {movie.get('duration_minutes', 120)} mins").classes('text-xs text-gray-400')
                    ui.separator().classes('my-3 opacity-30')
                    
                    with ui.row().classes('items-center gap-2 text-sm text-gray-300'):
                        ui.icon('schedule', color='primary')
                        ui.label(f"{show['date']} | Showtime: {show['start_time']}")
                    with ui.row().classes('items-center gap-2 text-sm text-gray-300 mt-2'):
                        ui.icon('room', color='primary')
                        ui.label(f"{show.get('screen', {}).get('name', 'Screen 1')} | {show.get('screen', {}).get('theatre', {}).get('name', 'Theatre')}")

            # Right: Seat Booking details & Payment simulator
            with ui.column().classes('gap-6'):
                with ui.card().classes('glass-card p-8 w-full flex-grow'):
                    ui.label('Order Summary').classes('text-xl font-bold text-white mb-4 border-b border-zinc-800 pb-2')
                    
                    # Seat breakdown
                    for seat_info in seats_details:
                        with ui.row().classes('justify-between w-full text-sm py-2 border-b border-zinc-900'):
                            with ui.row().classes('items-center gap-2'):
                                ui.element('div').classes('w-3 h-3 rounded-full bg-primary')
                                ui.label(f"Seat {seat_info['seat_name']} ({seat_info['category']})").classes('text-gray-300 font-medium')
                            ui.label(f"Rs. {seat_info['price']}").classes('text-white font-bold')

                    ui.separator().classes('my-4')
                    with ui.row().classes('justify-between w-full text-lg font-bold text-white'):
                        ui.label('Total Amount')
                        ui.label(f"Rs. {total_amount:.2f}").classes('text-primary')

                    ui.label('Payment Method').classes('text-sm text-gray-400 font-bold uppercase mt-6 mb-2 tracking-wider')
                    with ui.card().classes('w-full bg-zinc-900 border border-zinc-800 p-4 flex-row items-center gap-4'):
                        ui.icon('credit_card', color='primary').classes('text-2xl')
                        with ui.column():
                            ui.label('Simulated Fast Payment Gateway').classes('text-sm text-white font-bold')
                            ui.label('Secure sandbox instant processing').classes('text-xs text-gray-500')

                    with ui.row().classes('w-full gap-4 mt-8'):
                        cancel_btn = ui.button('RELEASE SEATS', color='secondary', on_click=cancel_action).classes('flex-1 py-3 font-bold rounded-xl text-xs')
                        confirm_btn = ui.button('PAY & CONFIRM', color='primary', on_click=confirm_action).classes('flex-1 py-3 font-bold rounded-xl text-xs')

    tick()
