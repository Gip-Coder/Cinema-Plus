from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
import asyncio

@ui.page('/book/{show_id}')
async def seat_selection_page(show_id: int):
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    if api_client.is_admin():
        ui.navigate.to('/admin')
        return
        
    apply_theme()
    navbar()
    
    # Concurrent fetching with timeout handling
    try:
        show_task = api_client.get_show(show_id)
        booked_task = api_client.get_show_seat_statuses(show_id)
        
        show, seat_statuses = await asyncio.gather(show_task, booked_task)
    except Exception as e:
        ui.notify(f"Error loading booking details: {e}", type="negative")
        ui.navigate.to("/")
        return
        
    if not show:
        ui.label('Show not found')
        return
        
    movie_id = show['movie_id']
    try:
        movie = await api_client.get_movie(movie_id)
    except Exception as e:
        ui.notify(f"Error loading movie details: {e}", type="negative")
        ui.navigate.to("/")
        return
        
    if not movie:
        ui.label('Movie not found')
        return
        
    # Maintain seat state lists that get updated via polling
    booked_seat_names = set(seat_statuses.get("booked", []))
    reserved_seat_names = set(seat_statuses.get("reserved", []))
    
    selected_seats = {}
    total_price = {'value': 0}
    seat_buttons = {} # seat_name -> button UI element
    
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
        
        applied_rules = []
        for pl in prices_payload:
            for r in pl.get("applied_rules", []):
                if r["name"] not in [rule["name"] for rule in applied_rules]:
                    applied_rules.append(r)
    except Exception:
        seat_prices = {"Normal": 150, "Executive": 220, "Premium": 300}
        applied_rules = []
    
    def update_summary():
        if selected_seats:
            summary_label.set_text(f"Selected Seats: {', '.join(sorted(selected_seats.keys()))} | Total: Rs. {total_price['value']}")
            book_btn.set_visibility(True)
        else:
            summary_label.set_text("Select seats to proceed")
            book_btn.set_visibility(False)
 
    def toggle_seat(seat_name, category, btn):
        if seat_name in booked_seat_names or seat_name in reserved_seat_names:
            ui.notify(f"Seat {seat_name} is no longer available.", type="warning")
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
            
        seats_payload_names = list(selected_seats.keys())
        reservation = await api_client.create_reservation(show_id, seats_payload_names)
        if reservation:
            ui.notify('Seats temporarily reserved! Proceeding to checkout.', type='positive')
            ui.navigate.to(f'/checkout/{reservation["id"]}')
        else:
            ui.notify('Failed to reserve seats. Some seats might have been taken.', type='negative')

    async def poll_seat_statuses():
        nonlocal booked_seat_names, reserved_seat_names
        try:
            latest = await api_client.get_show_seat_statuses(show_id)
            booked_seat_names = set(latest.get("booked", []))
            reserved_seat_names = set(latest.get("reserved", []))
            
            for seat_name, btn in seat_buttons.items():
                if seat_name in selected_seats:
                    if seat_name in booked_seat_names or seat_name in reserved_seat_names:
                        # Taken by someone else
                        selected_seats.pop(seat_name)
                        total_price['value'] -= int(seat_prices[btn.seat_category])
                        btn.classes(remove='seat-selected seat-available seat-reserved', add='seat-booked' if seat_name in booked_seat_names else 'seat-reserved')
                        ui.notify(f"Seat {seat_name} was taken by another user.", type="negative")
                else:
                    if seat_name in booked_seat_names:
                        btn.classes(remove='seat-available seat-selected seat-reserved', add='seat-booked')
                    elif seat_name in reserved_seat_names:
                        btn.classes(remove='seat-available seat-selected seat-booked', add='seat-reserved')
                    else:
                        btn.classes(remove='seat-selected seat-booked seat-reserved', add='seat-available')
            update_summary()
        except Exception as e:
            print(f"Error polling seat statuses: {e}")

    # Set up polling every 5 seconds
    polling_timer = ui.timer(5.0, poll_seat_statuses)

    with ui.column().classes('w-full items-center p-8'):
        ui.label(f'Book Tickets: {movie["title"]}').classes('text-3xl font-bold text-white mb-2')
        ui.label(f"{show['date']} | Showtime: {show['start_time']}").classes('text-sm text-gray-400 mb-8')
        
        # 1. Screen Orientation Indicator
        with ui.column().classes('w-full max-w-4xl items-center mb-12'):
            ui.label('SCREEN THIS WAY').classes('text-gray-500 tracking-[1em] mb-2 font-bold text-xs')
            ui.element('div').classes('w-full h-3 bg-gradient-to-b from-[#E50914] to-transparent shadow-[0_10px_20px_rgba(229,9,20,0.4)] rounded-t-full mb-8')
        
        # Dynamic pricing rule explanation banner
        if applied_rules:
            with ui.row().classes('items-center gap-2 p-3 rounded-lg mb-8 max-w-2xl bg-primary/10 border border-primary/20'):
                ui.icon('info', color='primary')
                rules_str = ", ".join([f"{r['name']} ({r['multiplier']}x)" for r in applied_rules])
                ui.label(f"Pricing includes active rules: {rules_str}").classes('text-xs text-primary font-medium')
        
        # Fetch layout for screen if available
        screen_id = show.get("screen_id")
        layout = None
        try:
            layout = await api_client.get_layout_for_screen(screen_id)
        except Exception as e:
            print(f"Error fetching layout for screen {screen_id}: {e}")

        if layout:
            # Render from visual layout definitions
            seats_by_pos = {(s['position_x'], s['position_y']): s for s in layout.get('seats', [])}
            layout_rows = layout['rows']
            layout_cols = layout['cols']
            
            with ui.row().classes('justify-center gap-6 mb-6 w-full text-sm font-semibold'):
                ui.label(f'NORMAL: Rs. {seat_prices["Normal"]}').classes('text-gray-400')
                ui.label(f'EXECUTIVE: Rs. {seat_prices["Executive"]}').classes('text-blue-400')
                ui.label(f'PREMIUM: Rs. {seat_prices["Premium"]}').classes('text-yellow-500')
            
            with ui.column().classes('gap-2'):
                for y in range(layout_rows):
                    with ui.row().classes('justify-center gap-1 items-center'):
                        # Get row label from first active seat in this row
                        row_seats = [seats_by_pos[p] for p in seats_by_pos if p[1] == y and seats_by_pos[p].get('is_active', True)]
                        row_label = row_seats[0]['row_label'] if row_seats else chr(65 + y)
                        ui.label(row_label).classes('w-6 text-center font-bold text-xs text-gray-500 mr-2')
                        
                        for x in range(layout_cols):
                            pos = (x, y)
                            seat = seats_by_pos.get(pos)
                            
                            if seat and seat.get('is_active', True) and seat.get('seat_type') != 'blocked':
                                seat_name = seat['seat_code']
                                category = seat['category']
                                seat_type = seat['seat_type']
                                
                                is_booked = seat_name in booked_seat_names
                                is_reserved = seat_name in reserved_seat_names
                                
                                color_class = 'seat-booked' if is_booked else ('seat-reserved' if is_reserved else 'seat-available')
                                
                                icon_str = None
                                btn_label = ""
                                
                                if seat_type == "wheelchair":
                                    icon_str = "accessible"
                                elif seat_type == "couple":
                                    icon_str = "favorite"
                                else:
                                    btn_label = str(seat['seat_number'])
                                    
                                btn = ui.button(btn_label, icon=icon_str, color=None).classes(f'seat {color_class} min-w-[32px] min-h-[32px] p-0 text-[10px] font-bold text-white')
                                btn.seat_category = category
                                seat_buttons[seat_name] = btn
                                
                                if not (is_booked or is_reserved):
                                    btn.on('click', lambda sn=seat_name, c=category, b=btn: toggle_seat(sn, c, b))
                            else:
                                ui.element('div').classes('w-[32px] h-[32px] m-[1px]').style('opacity: 0; pointer-events: none;')
        else:
            # Fallback to algorithmic generation
            total_seats = show.get("screen", {}).get("total_seats", 220)
            cols = 20 if total_seats > 100 else 10
            import math
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
            
            normal_rows = row_letters[0 : normal_rows_count]
            executive_rows = row_letters[normal_rows_count : normal_rows_count + executive_rows_count]
            premium_rows = row_letters[normal_rows_count + executive_rows_count : ]

            def render_category_rows(rows_list, start_global_idx, category):
                for row_idx, row in enumerate(rows_list):
                    row_global_idx = start_global_idx + row_idx
                    
                    if row_global_idx < total_rows_needed - 1:
                        seat_map = {c: c + 1 for c in range(cols)}
                    else:
                        k = total_seats - row_global_idx * cols
                        if k == cols:
                            seat_map = {c: c + 1 for c in range(cols)}
                        elif k == 1:
                            seat_map = {(cols - 1) // 2: 1}
                        else:
                            seat_map = {}
                            for i in range(k):
                                idx = round(i * (cols - 1) / (k - 1))
                                seat_map[idx] = i + 1
                    
                    with ui.row().classes('justify-center gap-2'):
                        ui.label(row).classes('w-6 text-center font-bold self-center')
                        for col_idx in range(cols):
                            if col_idx in seat_map:
                                seat_num = seat_map[col_idx]
                                seat_name = f"{row}{seat_num}"
                                is_booked = seat_name in booked_seat_names
                                is_reserved = seat_name in reserved_seat_names
                                
                                color_class = 'seat-booked' if is_booked else ('seat-reserved' if is_reserved else 'seat-available')
                                btn = ui.button('', color=None).classes(f'seat {color_class} min-w-[30px] min-h-[30px] p-0')
                                btn.seat_category = category
                                seat_buttons[seat_name] = btn
                                
                                if not (is_booked or is_reserved):
                                    btn.on('click', lambda sn=seat_name, c=category, b=btn: toggle_seat(sn, c, b))
                            else:
                                ui.element('div').classes('w-[30px] h-[30px] m-[3px]').style('opacity: 0; pointer-events: none;')

            # Seat layout
            with ui.column().classes('gap-6'):
                if normal_rows:
                    ui.label(f'NORMAL - Rs. {seat_prices["Normal"]}').classes('text-center w-full text-gray-400 font-bold mb-2')
                    render_category_rows(normal_rows, 0, 'Normal')
                    
                if executive_rows:
                    if normal_rows:
                        ui.separator().classes('my-4')
                    ui.label(f'EXECUTIVE - Rs. {seat_prices["Executive"]}').classes('text-center w-full text-blue-400 font-bold mb-2')
                    render_category_rows(executive_rows, normal_rows_count, 'Executive')
                                    
                if premium_rows:
                    if normal_rows or executive_rows:
                        ui.separator().classes('my-4')
                    ui.label(f'PREMIUM - Rs. {seat_prices["Premium"]}').classes('text-center w-full text-yellow-500 font-bold mb-2')
                    render_category_rows(premium_rows, normal_rows_count + executive_rows_count, 'Premium')

        # Legend
        with ui.row().classes('mt-12 gap-8'):
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-available')
                ui.label('Available')
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-selected')
                ui.label('Selected')
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-reserved')
                ui.label('Reserved')
            with ui.row().classes('items-center gap-2'):
                ui.element('div').classes('seat seat-booked')
                ui.label('Booked')
            if layout:
                with ui.row().classes('items-center gap-2'):
                    ui.icon('accessible', color='white').classes('text-lg')
                    ui.label('Wheelchair')
                with ui.row().classes('items-center gap-2'):
                    ui.icon('favorite', color='white').classes('text-lg')
                    ui.label('Couple')

        # Summary Bar
        with ui.card().classes('fixed bottom-0 left-0 w-full glass-card rounded-none p-4 z-50 flex-row justify-between items-center'):
            summary_label = ui.label('Select seats to proceed').classes('text-xl font-bold text-white')
            book_btn = ui.button('CONTINUE', color='primary', on_click=confirm_booking).classes('px-8 py-2 rounded-full font-bold')
            book_btn.set_visibility(False)
