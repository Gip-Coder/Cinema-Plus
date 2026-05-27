from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
import asyncio

SEAT_PRICES = {
    'Normal': 900,
    'Executive': 950,
    'Premium': 1000
}

@ui.page('/book/{show_id}')
async def seat_selection_page(show_id: int):
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    apply_theme()
    navbar()
    
    show = await api_client.get_show(show_id)
    if not show:
        ui.label('Show not found')
        return
        
    movie_id = show['movie_id']
    movie = await api_client.get_movie(movie_id)
    
    booked_seats_data = await api_client.get_booked_seats(show_id)
    booked_seat_names = [seat['seat_name'] for seat in booked_seats_data]
    
    selected_seats = set()
    total_price = {'value': 0}
    multiplier = show.get('price_multiplier', 1.0)
    
    def update_summary():
        summary_label.set_text(f"Selected Seats: {', '.join(sorted(selected_seats))} | Total: Rs. {total_price['value']}")
        book_btn.set_visibility(len(selected_seats) > 0)

    def toggle_seat(seat_name, category, btn):
        if seat_name in booked_seat_names:
            return
            
        price = int(SEAT_PRICES[category] * multiplier)
        if seat_name in selected_seats:
            selected_seats.remove(seat_name)
            total_price['value'] -= price
            btn.classes(remove='seat-selected', add='seat-available')
        else:
            selected_seats.add(seat_name)
            total_price['value'] += price
            btn.classes(remove='seat-available', add='seat-selected')
        update_summary()

    async def confirm_booking():
        if not selected_seats:
            return
            
        seats_payload = []
        for s in selected_seats:
            row = s[0]
            cat = 'Normal'
            if row in ['A', 'B', 'C']: cat = 'Premium'
            elif row in ['D', 'E', 'F', 'G', 'H']: cat = 'Executive'
            else: cat = 'Normal'
            
            seats_payload.append({"seat_name": s, "category": cat})
            
        booking = await api_client.book_seats(movie_id, seats_payload, total_price['value'], show_id)
        if booking:
            ui.notify('Booking successful!', type='positive')
            ui.navigate.to(f'/billing/{booking["id"]}')
        else:
            ui.notify('Booking failed. Seats might be taken.', type='negative')

    with ui.column().classes('w-full items-center p-8'):
        ui.label(f'Book Tickets: {movie["title"]}').classes('text-3xl font-bold text-white mb-8')
        
        # Screen
        with ui.column().classes('w-full max-w-4xl items-center mb-12'):
            ui.label('SCREEN').classes('text-gray-500 tracking-[1em] mb-2')
            ui.element('div').classes('w-full h-2 bg-gradient-to-b from-gray-300 to-transparent shadow-[0_10px_20px_rgba(255,255,255,0.2)] rounded-t-full mb-8')
        
        # Seat layout
        with ui.column().classes('gap-6'):
            # Premium
            ui.label('PREMIUM - Rs. 1000').classes('text-center w-full text-yellow-500 font-bold mb-2')
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
            ui.label('EXECUTIVE - Rs. 950').classes('text-center w-full text-blue-400 font-bold mb-2')
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
            ui.label('NORMAL - Rs. 900').classes('text-center w-full text-gray-400 font-bold mb-2')
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
