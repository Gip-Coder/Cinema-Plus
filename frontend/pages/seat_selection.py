from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
import asyncio

@ui.page('/book/{show_id}')
async def seat_selection_page(show_id: int):
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    apply_theme()
    navbar()
    
    # Concurrent fetching with timeout handling
    try:
        show_task = api_client.get_show(show_id)
        booked_task = api_client.get_booked_seats(show_id)
        
        show, booked_seats_data = await asyncio.gather(show_task, booked_task)
    except Exception as e:
        ui.notify(f"Error loading booking details: {e}", type="negative")
        ui.navigate.to("/")
        return
        
    if not show:
        ui.label('Show not found')
        return
        
    movie_id = show['movie_id']
    movie = await api_client.get_movie(movie_id)
    
    booked_seat_names = [seat['seat_name'] for seat in booked_seats_data]
    
    selected_seats = {}
    total_price = {'value': 0}
    
    # Dynamic price retrieval and surge rules logging on page load
    try:
        prices_payload = await asyncio.gather(
            api_client.get_seat_price_details(show_id, "Normal"),
            api_client.get_seat_price_details(show_id, "Executive"),
            api_client.get_seat_price_details(show_id, "Premium"),
        )
        seat_prices = {
            "Normal": prices_payload[0].get("final_price", 150),
            "Executive": prices_payload[1].get("final_price", 220),
            "Premium": prices_payload[2].get("final_price", 300)
        }
        
        # Accumulate applied rules lists to display them dynamically on the page
        applied_rules = []
        for pl in prices_payload:
            for r in pl.get("applied_rules", []):
                if r["name"] not in [rule["name"] for rule in applied_rules]:
                    applied_rules.append(r)
    except Exception:
        seat_prices = {"Normal": 150, "Executive": 220, "Premium": 300}
        applied_rules = []
    
    def update_summary():
        summary_label.set_text(f"Selected Seats: {', '.join(sorted(selected_seats.keys()))} | Total: Rs. {total_price['value']}")
        book_btn.set_visibility(len(selected_seats) > 0)

    def toggle_seat(seat_name, category, btn):
        if seat_name in booked_seat_names:
            return
            
        price = int(seat_prices[category])
        if seat_name in selected_seats:
            selected_seats.pop(seat_name)
            total_price['value'] -= price
            btn.classes(remove='seat-selected', add='seat-available')
        else:
            selected_seats[seat_name] = category
            total_price['value'] += price
            btn.classes(remove='seat-available', add='seat-selected')
        update_summary()

    async def confirm_booking():
        if not selected_seats:
            return
            
        seats_payload = []
        for s, cat in selected_seats.items():
            seats_payload.append({"seat_name": s, "category": cat})
            
        booking = await api_client.book_seats(movie_id, seats_payload, total_price['value'], show_id)
        if booking:
            ui.notify('Booking successful!', type='positive')
            ui.navigate.to(f'/billing/{booking["id"]}')
        else:
            ui.notify('Booking failed. Seats might be taken.', type='negative')

    with ui.column().classes('w-full items-center p-8'):
        ui.label(f'Book Tickets: {movie["title"]}').classes('text-3xl font-bold text-white mb-2')
        ui.label(f"{show['date']} | Showtime: {show['start_time']}").classes('text-sm text-gray-400 mb-8')
        
        # 1. Screen Orientation Indicator ("SCREEN THIS WAY")
        with ui.column().classes('w-full max-w-4xl items-center mb-12'):
            ui.label('SCREEN THIS WAY').classes('text-gray-500 tracking-[1em] mb-2 font-bold text-xs')
            ui.element('div').classes('w-full h-3 bg-gradient-to-b from-[#E50914] to-transparent shadow-[0_10px_20px_rgba(229,9,20,0.4)] rounded-t-full mb-8')
        
        # Dynamic pricing rule explanation banner
        if applied_rules:
            with ui.row().classes('items-center gap-2 p-3 rounded-lg mb-8 max-w-2xl bg-primary/10 border border-primary/20'):
                ui.icon('info', color='primary')
                rules_str = ", ".join([f"{r['name']} ({r['multiplier']}x)" for r in applied_rules])
                ui.label(f"Pricing includes active rules: {rules_str}").classes('text-xs text-primary font-medium')
        
        # Seat layout
        with ui.column().classes('gap-6'):
            # Premium
            ui.label(f'PREMIUM - Rs. {seat_prices["Premium"]}').classes('text-center w-full text-yellow-500 font-bold mb-2')
            for row in ['A', 'B', 'C']:
                with ui.row().classes('justify-center gap-2'):
                    ui.label(row).classes('w-6 text-center font-bold self-center')
                    for col in range(1, 21):
                        seat_name = f"{row}{col}"
                        cat = 'Premium'
                        is_booked = seat_name in booked_seat_names
                        color_class = 'seat-booked' if is_booked else 'seat-available'
                        btn = ui.button('').classes(f'seat {color_class} min-w-[30px] min-h-[30px] p-0')
                        if not is_booked:
                            btn.on('click', lambda sn=seat_name, c=cat, b=btn: toggle_seat(sn, c, b))
            
            ui.separator().classes('my-4')
            
            # Executive
            ui.label(f'EXECUTIVE - Rs. {seat_prices["Executive"]}').classes('text-center w-full text-blue-400 font-bold mb-2')
            for row in ['D', 'E', 'F', 'G', 'H']:
                with ui.row().classes('justify-center gap-2'):
                    ui.label(row).classes('w-6 text-center font-bold self-center')
                    for col in range(1, 21):
                        seat_name = f"{row}{col}"
                        cat = 'Executive'
                        is_booked = seat_name in booked_seat_names
                        color_class = 'seat-booked' if is_booked else 'seat-available'
                        btn = ui.button('').classes(f'seat {color_class} min-w-[30px] min-h-[30px] p-0')
                        if not is_booked:
                            btn.on('click', lambda sn=seat_name, c=cat, b=btn: toggle_seat(sn, c, b))

            ui.separator().classes('my-4')
            
            # Normal
            ui.label(f'NORMAL - Rs. {seat_prices["Normal"]}').classes('text-center w-full text-gray-400 font-bold mb-2')
            for row in ['I', 'J', 'K']:
                with ui.row().classes('justify-center gap-2'):
                    ui.label(row).classes('w-6 text-center font-bold self-center')
                    for col in range(1, 21):
                        seat_name = f"{row}{col}"
                        cat = 'Normal'
                        is_booked = seat_name in booked_seat_names
                        color_class = 'seat-booked' if is_booked else 'seat-available'
                        btn = ui.button('').classes(f'seat {color_class} min-w-[30px] min-h-[30px] p-0')
                        if not is_booked:
                            btn.on('click', lambda sn=seat_name, c=cat, b=btn: toggle_seat(sn, c, b))

        # Legend
        with ui.row().classes('mt-12 gap-8'):
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-available')
                ui.label('Available')
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-selected')
                ui.label('Selected')
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-booked')
                ui.label('Booked')

        # Summary Bar
        with ui.card().classes('fixed bottom-0 left-0 w-full glass-card rounded-none p-4 z-50 flex-row justify-between items-center'):
            summary_label = ui.label('Select seats to proceed').classes('text-xl font-bold text-white')
            book_btn = ui.button('CONFIRM BOOKING', color='primary', on_click=confirm_booking).classes('px-8 py-2 rounded-full font-bold')
            book_btn.set_visibility(False)
