# pyrefly: ignore [missing-import]
from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
from backend.utils.layout_generator import generate_layout, validate_layout
import copy

@ui.page('/admin/layout-designer/{screen_id}')
async def layout_designer_page(screen_id: int):
    # Authorization checks
    if not api_client.is_authenticated() or not api_client.is_admin():
        ui.notify('Unauthorized access', type='negative')
        ui.navigate.to('/')
        return

    apply_theme()
    navbar()
    
    # ─── Load Screen & Layouts ────────────────────────────────────────
    try:
        screens = await api_client.get_screens()
        screen = next((s for s in screens if s['id'] == screen_id), None)
    except Exception as e:
        ui.notify(f"Error loading screen: {e}", type="negative")
        ui.navigate.to('/admin')
        return

    if not screen:
        ui.notify("Screen not found", type="negative")
        ui.navigate.to('/admin')
        return

    # Load layouts for this screen
    current_layout = None
    try:
        layouts = await api_client.get_all_layouts_for_screen(screen_id)
        # Find published or latest updated draft
        published = next((l for l in layouts if l['is_published']), None)
        if published:
            current_layout = published
        elif layouts:
            current_layout = layouts[0]
    except Exception as e:
        print(f"Error loading layouts: {e}")

    # ─── State Initialization ─────────────────────────────────────────
    state = {
        "layout_id": current_layout['id'] if current_layout else None,
        "layout_name": current_layout['layout_name'] if current_layout else "Default Layout",
        "layout_type": current_layout['layout_type'] if current_layout else "STANDARD",
        "total_seats": current_layout['total_seats'] if current_layout else screen['total_seats'],
        "rows": current_layout['rows'] if current_layout else 0,
        "cols": current_layout['cols'] if current_layout else 0,
        "version": current_layout.get('version', 1) if current_layout else 1,
        "status": current_layout.get('status', 'draft') if current_layout else 'draft',
        "selected_seat_pos": None, # (x, y)
        "seats_map": {}, # (x, y) -> seat dict
        "move_mode": False,
    }

    if current_layout:
        for s in current_layout.get('seats', []):
            state["seats_map"][(s['position_x'], s['position_y'])] = {
                'seat_code': s['seat_code'],
                'row_label': s['row_label'],
                'seat_number': s['seat_number'],
                'seat_type': s['seat_type'],
                'category': s['category'],
                'position_x': s['position_x'],
                'position_y': s['position_y'],
                'is_active': s['is_active']
            }
    else:
        # Default generation on first open
        layout_data = generate_layout(total_seats=state["total_seats"], template=state["layout_type"])
        state["rows"] = layout_data.rows
        state["cols"] = layout_data.cols
        for s in layout_data.seats:
            state["seats_map"][(s.position_x, s.position_y)] = s.to_dict()

    # History stacks for Undo/Redo
    undo_stack = []
    redo_stack = []

    def push_history():
        undo_stack.append({
            "seats_map": copy.deepcopy(state["seats_map"]),
            "rows": state["rows"],
            "cols": state["cols"],
            "layout_type": state["layout_type"],
            "total_seats": state["total_seats"]
        })
        redo_stack.clear()
        update_undo_redo_buttons()

    def update_undo_redo_buttons():
        undo_btn.set_enabled(len(undo_stack) > 0)
        redo_btn.set_enabled(len(redo_stack) > 0)

    # ─── Statistics Calculation ───────────────────────────────────────
    def compute_current_stats():
        active = [state["seats_map"][pos] for pos in state["seats_map"] if state["seats_map"][pos].get('is_active', True)]
        normal = len([s for s in active if s['category'] == 'Normal' and s['seat_type'] != 'blocked'])
        executive = len([s for s in active if s['category'] == 'Executive' and s['seat_type'] != 'blocked'])
        premium = len([s for s in active if s['category'] == 'Premium' and s['seat_type'] != 'blocked'])
        wheelchair = len([s for s in active if s['seat_type'] == 'wheelchair'])
        couple = len([s for s in active if s['seat_type'] == 'couple'])
        blocked = len([s for s in active if s['seat_type'] == 'blocked'])
        
        return {
            "total_active": len(active),
            "normal": normal,
            "executive": executive,
            "premium": premium,
            "wheelchair": wheelchair,
            "couple": couple,
            "blocked": blocked
        }

    # ─── Grid Rebuild & Seat Selection ─────────────────────────────────
    def rebuild_grid():
        grid_container.clear()
        with grid_container:
            # Visual Screen Orientation
            with ui.column().classes('w-full max-w-4xl items-center mb-8 mt-2'):
                ui.label('SCREEN THIS WAY').classes('text-gray-500 tracking-[1em] mb-2 font-bold text-xs')
                ui.element('div').classes('w-full h-3 bg-gradient-to-b from-[#E50914] to-transparent shadow-[0_10px_20px_rgba(229,9,20,0.4)] rounded-t-full')

            # Seating Grid Rows
            for y in range(state["rows"]):
                with ui.row().classes('justify-center gap-1 items-center w-full'):
                    # Row label on left
                    row_seats = [state["seats_map"][pos] for pos in state["seats_map"] if pos[1] == y and state["seats_map"][pos].get('is_active', True)]
                    if row_seats:
                        row_label_text = row_seats[0]['row_label']
                    else:
                        from backend.utils.layout_generator import _row_label
                        row_label_text = _row_label(y)
                    
                    ui.label(row_label_text).classes('w-6 text-center font-bold text-xs text-gray-500 mr-2')
                    
                    for x in range(state["cols"]):
                        pos = (x, y)
                        seat = state["seats_map"].get(pos)
                        
                        if seat and seat.get('is_active', True):
                            seat_code = seat['seat_code']
                            category = seat['category']
                            seat_type = seat['seat_type']
                            
                            # Distinct category/type styling
                            if category == "Premium":
                                bg_style = "background: linear-gradient(135deg, #f39c12, #d35400) !important;"
                            elif category == "Executive":
                                bg_style = "background: linear-gradient(135deg, #3498db, #2980b9) !important;"
                            else:
                                bg_style = "background: linear-gradient(135deg, #e50914, #b81d24) !important;"
                                
                            icon_str = None
                            btn_label = seat_code
                            
                            if seat_type == "blocked":
                                bg_style = "background: linear-gradient(135deg, #444, #222) !important; border: 1px dashed #666;"
                                btn_label = "X"
                            elif seat_type == "wheelchair":
                                icon_str = "accessible"
                                btn_label = ""
                            elif seat_type == "couple":
                                icon_str = "favorite"
                                btn_label = ""
                                
                            is_selected = (state["selected_seat_pos"] == pos)
                            border_style = "border: 2px solid #ffffff !important; box-shadow: 0 0 10px #ffffff;" if is_selected else "border: 1px solid rgba(0,0,0,0.3);"
                            
                            btn = ui.button(btn_label, icon=icon_str, color=None).classes('min-w-[32px] min-h-[32px] max-w-[32px] max-h-[32px] p-0 rounded-sm text-[9px] font-bold text-white').style(f'{bg_style} {border_style} cursor-pointer')
                            btn.on('click', lambda p=pos: select_seat(p))
                        else:
                            # Empty slot — move selected seat or add new seat
                            btn = ui.button('', icon='add', color=None).classes('min-w-[32px] min-h-[32px] max-w-[32px] max-h-[32px] p-0 rounded-sm opacity-10 hover:opacity-50 transition-opacity').style('border: 1px dashed #555; background: transparent; color: #777;')
                            btn.on('click', lambda p=pos: handle_empty_cell_click(p))

    def handle_empty_cell_click(pos):
        if state["move_mode"] and state["selected_seat_pos"] and state["selected_seat_pos"] != pos:
            move_seat_to(pos)
        elif state["selected_seat_pos"] and state["selected_seat_pos"] in state["seats_map"]:
            move_seat_to(pos)
        else:
            add_seat_at(pos)

    def move_seat_to(dest_pos):
        src_pos = state["selected_seat_pos"]
        if not src_pos or src_pos not in state["seats_map"]:
            return
        if dest_pos in state["seats_map"] and state["seats_map"][dest_pos].get('is_active', True):
            ui.notify("Destination already has a seat!", type="warning")
            return

        push_history()
        seat = state["seats_map"].pop(src_pos)
        x, y = dest_pos
        seat['position_x'] = x
        seat['position_y'] = y
        state["seats_map"][dest_pos] = seat
        state["selected_seat_pos"] = dest_pos
        state["move_mode"] = False
        ui.notify(f"Moved seat {seat['seat_code']} to ({x}, {y})", type="positive")
        rebuild_grid()
        update_sidebar()

    def insert_aisle_column(at_x: int):
        """Insert an aisle gap at column at_x, shifting seats right."""
        if at_x < 0 or at_x > state["cols"]:
            ui.notify("Invalid aisle column position", type="warning")
            return

        push_history()
        new_map = {}
        for pos, seat in state["seats_map"].items():
            x, y = pos
            if not seat.get('is_active', True):
                new_map[pos] = seat
                continue
            new_x = x + 1 if x >= at_x else x
            seat['position_x'] = new_x
            new_map[(new_x, y)] = seat

        state["seats_map"] = new_map
        state["cols"] += 1
        state["selected_seat_pos"] = None
        ui.notify(f"Aisle inserted at column {at_x}", type="positive")
        rebuild_grid()
        update_sidebar()

    def select_seat(pos):
        state["selected_seat_pos"] = pos
        rebuild_grid()
        update_sidebar()

    def add_seat_at(pos):
        push_history()
        x, y = pos
        from backend.utils.layout_generator import _row_label, _assign_categories
        row_label = _row_label(y)
        
        row_seats = [state["seats_map"][p] for p in state["seats_map"] if p[1] == y and state["seats_map"][p].get('is_active', True)]
        next_num = max(s['seat_number'] for s in row_seats) + 1 if row_seats else 1
        seat_code = f"{row_label}{next_num}"
        
        row_categories = _assign_categories(state["rows"])
        category = row_categories.get(y, "Normal")
        
        state["seats_map"][pos] = {
            'seat_code': seat_code,
            'row_label': row_label,
            'seat_number': next_num,
            'seat_type': 'standard',
            'category': category,
            'position_x': x,
            'position_y': y,
            'is_active': True
        }
        
        state["selected_seat_pos"] = pos
        ui.notify(f"Added seat {seat_code}!", type="positive")
        rebuild_grid()
        update_sidebar()

    # ─── Sidebar Update ───────────────────────────────────────────────
    def update_sidebar():
        sidebar_container.clear()
        stats = compute_current_stats()
        
        with sidebar_container:
            ui.label('Layout Statistics').classes('text-lg font-bold text-white mb-2')
            
            with ui.column().classes('w-full gap-2 text-sm text-gray-300 bg-black/40 p-4 rounded-lg border border-zinc-800'):
                ui.html(f'''
                    <div class="flex justify-between"><span>Total Active Seats:</span><span class="font-bold text-white">{stats["total_active"]}</span></div>
                    <div class="flex justify-between"><span>Normal (Red):</span><span class="font-bold text-red-400">{stats["normal"]}</span></div>
                    <div class="flex justify-between"><span>Executive (Blue):</span><span class="font-bold text-blue-400">{stats["executive"]}</span></div>
                    <div class="flex justify-between"><span>Premium (Gold):</span><span class="font-bold text-yellow-500">{stats["premium"]}</span></div>
                    <div class="flex justify-between"><span>Wheelchair:</span><span class="font-bold text-info">{stats["wheelchair"]}</span></div>
                    <div class="flex justify-between"><span>Couple:</span><span class="font-bold text-pink-400">{stats["couple"]}</span></div>
                    <div class="flex justify-between"><span>Blocked (X):</span><span class="font-bold text-gray-500">{stats["blocked"]}</span></div>
                    <div class="flex justify-between"><span>Visual Grid Size:</span><span class="font-bold text-white">{state["rows"]} × {state["cols"]}</span></div>
                ''')

            ui.separator().classes('my-2')
            
            pos = state["selected_seat_pos"]
            if pos and pos in state["seats_map"] and state["seats_map"][pos].get('is_active', True):
                seat = state["seats_map"][pos]
                ui.label(f'Edit Seat: {seat["seat_code"]}').classes('text-lg font-bold text-white')
                
                code_input = ui.input('Seat Code', value=seat['seat_code']).classes('w-full')
                category_select = ui.select(
                    ['Normal', 'Executive', 'Premium'],
                    value=seat['category'],
                    label='Pricing Category'
                ).classes('w-full')
                
                type_select = ui.select(
                    {
                        'standard': 'Standard Seat',
                        'wheelchair': 'Wheelchair Seat',
                        'couple': 'Couple Seat',
                        'blocked': 'Blocked / Invisible'
                    },
                    value=seat['seat_type'],
                    label='Seat Type'
                ).classes('w-full')
                
                async def apply_seat_changes():
                    new_code = code_input.value.strip()
                    if not new_code:
                        ui.notify("Seat code cannot be empty!", type="warning")
                        return
                        
                    push_history()
                    seat['seat_code'] = new_code
                    seat['category'] = category_select.value
                    seat['seat_type'] = type_select.value
                    
                    letters = "".join([c for c in new_code if c.isalpha()])
                    digits = "".join([c for c in new_code if c.isdigit()])
                    if letters and digits:
                        seat['row_label'] = letters
                        seat['seat_number'] = int(digits)
                    
                    ui.notify(f"Updated seat {new_code}!", type="positive")
                    rebuild_grid()
                    update_sidebar()
                
                def delete_selected_seat():
                    push_history()
                    seat['is_active'] = False
                    state["selected_seat_pos"] = None
                    ui.notify("Seat marked inactive/removed", type="warning")
                    rebuild_grid()
                    update_sidebar()

                with ui.row().classes('w-full gap-2 justify-between mt-2'):
                    ui.button('Apply', color='primary', on_click=apply_seat_changes).classes('flex-grow')
                    ui.button('Move', color='secondary', on_click=lambda: toggle_move_mode()).classes('px-4')
                    ui.button('Remove', color='negative', on_click=delete_selected_seat).classes('px-4')

                def toggle_move_mode():
                    state["move_mode"] = not state["move_mode"]
                    if state["move_mode"]:
                        ui.notify("Move mode: click an empty cell to relocate this seat", type="info")
                    else:
                        ui.notify("Move mode disabled", type="info")
            else:
                ui.label('Select a seat or empty cell in the grid to edit properties or add seats.').classes('text-sm text-gray-500 text-center italic mt-4')

            ui.separator().classes('my-2')
            ui.label('Grid Tools').classes('text-md font-bold text-white')
            aisle_col_input = ui.number('Aisle Column', value=state["cols"] // 2, min=0, max=max(state["cols"], 1), format='%d').classes('w-full')
            ui.button('Insert Aisle', icon='view_week', color='zinc-700', on_click=lambda: insert_aisle_column(int(aisle_col_input.value))).classes('w-full')

            ui.separator().classes('my-2')
            ui.label(f'Version: v{state["version"]} ({state["status"]})').classes('text-sm text-gray-400')
            rollback_version_input = ui.number(
                'Rollback to version',
                value=max(1, state["version"] - 1),
                min=1,
                format='%d',
            ).classes('w-full')

            async def new_version_action():
                if not state["layout_id"]:
                    ui.notify("Save a draft first before creating a new version", type="warning")
                    return
                try:
                    res = await api_client.create_layout_version(state["layout_id"])
                    data = (res or {}).get('data', res)
                    if data and data.get('id'):
                        state["layout_id"] = data['id']
                        state["version"] = data.get('version', state["version"] + 1)
                        state["status"] = data.get('status', 'draft')
                        ui.notify(f"Created version v{state['version']}", type="positive")
                        update_sidebar()
                    else:
                        ui.notify("Failed to create new version", type="negative")
                except Exception as e:
                    ui.notify(f"Error creating version: {e}", type="negative")

            async def rollback_action():
                target = int(rollback_version_input.value)
                try:
                    res = await api_client.rollback_layout_version(screen_id, target)
                    if res:
                        ui.notify(f"Rolled back to v{target}", type="positive")
                        ui.timer(1.0, lambda: ui.navigate.to(f'/admin/layout-designer/{screen_id}'), once=True)
                except Exception as e:
                    ui.notify(f"Rollback failed: {e}", type="negative")

            with ui.row().classes('w-full gap-2'):
                ui.button('New Version', icon='content_copy', color='zinc-700', on_click=new_version_action).classes('flex-grow')
                ui.button('Rollback', icon='history', color='warning', on_click=rollback_action).classes('flex-grow')

    # ─── Undo / Redo Actions ──────────────────────────────────────────
    def undo_action():
        if not undo_stack:
            return
        state["selected_seat_pos"] = None
        
        redo_stack.append({
            "seats_map": copy.deepcopy(state["seats_map"]),
            "rows": state["rows"],
            "cols": state["cols"],
            "layout_type": state["layout_type"],
            "total_seats": state["total_seats"]
        })
        
        prev = undo_stack.pop()
        state["seats_map"] = prev["seats_map"]
        state["rows"] = prev["rows"]
        state["cols"] = prev["cols"]
        state["layout_type"] = prev["layout_type"]
        state["total_seats"] = prev["total_seats"]
        
        template_select.value = state["layout_type"]
        capacity_input.value = state["total_seats"]
        custom_cols_input.value = state["cols"]
        
        ui.notify("Undo", type="info")
        rebuild_grid()
        update_sidebar()
        update_undo_redo_buttons()

    def redo_action():
        if not redo_stack:
            return
        state["selected_seat_pos"] = None
        
        undo_stack.append({
            "seats_map": copy.deepcopy(state["seats_map"]),
            "rows": state["rows"],
            "cols": state["cols"],
            "layout_type": state["layout_type"],
            "total_seats": state["total_seats"]
        })
        
        nxt = redo_stack.pop()
        state["seats_map"] = nxt["seats_map"]
        state["rows"] = nxt["rows"]
        state["cols"] = nxt["cols"]
        state["layout_type"] = nxt["layout_type"]
        state["total_seats"] = nxt["total_seats"]
        
        template_select.value = state["layout_type"]
        capacity_input.value = state["total_seats"]
        custom_cols_input.value = state["cols"]
        
        ui.notify("Redo", type="info")
        rebuild_grid()
        update_sidebar()
        update_undo_redo_buttons()

    # ─── Persistence (Save & Publish) Actions ──────────────────────────
    async def save_draft_action():
        active_seats = [state["seats_map"][pos] for pos in state["seats_map"] if state["seats_map"][pos].get('is_active', True)]
        if not active_seats:
            ui.notify("Cannot save an empty layout!", type="warning")
            return False
            
        is_valid, errors = validate_layout(active_seats)
        if not is_valid:
            ui.notify(f"Validation Error: {errors[0]}", type="negative")
            return False

        try:
            if state["layout_id"]:
                res = await api_client.update_layout_seats(state["layout_id"], active_seats, state["rows"], state["cols"])
                if res:
                    ui.notify("Layout draft updated successfully!", type="positive")
                    return True
            else:
                res = await api_client.save_layout(
                    screen_id=screen_id,
                    layout_name=state["layout_name"],
                    seats=active_seats,
                    layout_type=state["layout_type"],
                    rows=state["rows"],
                    cols=state["cols"]
                )
                if res:
                    state["layout_id"] = res['id']
                    ui.notify("New layout draft saved successfully!", type="positive")
                    return True
            ui.notify("Failed to save layout.", type="negative")
            return False
        except Exception as e:
            ui.notify(f"Error saving layout: {e}", type="negative")
            return False

    async def publish_layout_action():
        saved = await save_draft_action()
        if not saved or not state["layout_id"]:
            return
            
        try:
            if await api_client.publish_layout(state["layout_id"]):
                ui.notify("Layout published successfully!", type="positive")
                ui.timer(1.0, lambda: ui.navigate.to('/admin'), once=True)
            else:
                ui.notify("Failed to publish layout.", type="negative")
        except Exception as e:
            ui.notify(f"Error publishing layout: {e}", type="negative")

    # ─── Page Layout & Rendering ──────────────────────────────────────
    with ui.column().classes('w-full p-8 max-w-7xl mx-auto'):
        ui.label(f'Layout Designer: {screen["name"]}').classes('text-3xl font-bold text-primary mb-2 border-l-4 border-primary pl-4')
        ui.label(f'Designing layout for Screen ID: {screen_id} at theatre {screen.get("theatre_name", "")}').classes('text-sm text-gray-400 mb-6')
        
        # Toolbar
        with ui.row().classes('w-full justify-between items-center mb-6 gap-4 p-4 glass-card'):
            with ui.row().classes('items-center gap-4'):
                template_select = ui.select(
                    ['STANDARD', 'IMAX', 'VIP', 'RECLINER', 'CUSTOM'],
                    value=state["layout_type"],
                    label='Template'
                ).classes('w-40')
                
                capacity_input = ui.number(
                    'Capacity',
                    value=state["total_seats"],
                    min=1,
                    max=2000,
                    format='%d'
                ).classes('w-28')
                
                custom_cols_input = ui.number(
                    'Columns',
                    value=state["cols"] if state["cols"] else 20,
                    min=4,
                    max=30,
                    format='%d'
                ).classes('w-24')
                custom_cols_input.bind_visibility_from(template_select, 'value', value='CUSTOM')

                def generate_new():
                    push_history()
                    state["selected_seat_pos"] = None
                    state["layout_type"] = template_select.value
                    state["total_seats"] = int(capacity_input.value)
                    
                    c_cols = int(custom_cols_input.value) if state["layout_type"] == "CUSTOM" else None
                    layout_data = generate_layout(total_seats=state["total_seats"], template=state["layout_type"], custom_cols=c_cols)
                    
                    state["rows"] = layout_data.rows
                    state["cols"] = layout_data.cols
                    state["seats_map"] = {}
                    for s in layout_data.seats:
                        state["seats_map"][(s.position_x, s.position_y)] = s.to_dict()
                    
                    ui.notify(f"Generated default {state['layout_type']} layout!", type="positive")
                    rebuild_grid()
                    update_sidebar()
                    
                ui.button('Generate', icon='cached', color='primary', on_click=generate_new).classes('px-6 rounded-lg h-10')

            with ui.row().classes('items-center gap-2'):
                undo_btn = ui.button(icon='undo', color='zinc-800', on_click=undo_action).props('dense round')
                redo_btn = ui.button(icon='redo', color='zinc-800', on_click=redo_action).props('dense round')
                update_undo_redo_buttons()
                
                ui.button('Save Draft', icon='save', color='info', on_click=save_draft_action).classes('px-4 rounded-lg')
                ui.button('Publish Layout', icon='publish', color='positive', on_click=publish_layout_action).classes('px-4 rounded-lg')
                ui.button('Cancel', icon='close', color='zinc-700', on_click=lambda: ui.navigate.to('/admin')).classes('px-4 rounded-lg')

        # Main Workspace: Grid + Sidebar
        with ui.row().classes('w-full gap-6 items-start'):
            # Seating Canvas Area
            grid_container = ui.column().classes('flex-grow items-center p-6 border border-zinc-800 bg-[#0c0c0c] rounded-xl overflow-auto')
            
            # Control sidebar
            sidebar_container = ui.column().classes('w-[350px] p-6 glass-card gap-6')

        # Initial Render
        rebuild_grid()
        update_sidebar()
