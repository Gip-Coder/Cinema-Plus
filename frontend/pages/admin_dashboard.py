from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
from datetime import date
from typing import List, Dict

@ui.page('/admin')
async def admin_dashboard():
    if not api_client.is_authenticated() or not api_client.is_admin():
        ui.notify('Unauthorized access', type='negative')
        ui.navigate.to('/')
        return
        
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full p-8 max-w-7xl mx-auto'):
        ui.label('Admin Dashboard').classes('text-3xl font-bold text-primary mb-8 border-l-4 border-primary pl-4')
        
        with ui.tabs().classes('w-full') as tabs:
            tab_analytics = ui.tab('Analytics')
            tab_movies = ui.tab('Manage Movies')
            tab_schedule = ui.tab('Manage Schedule')
            tab_bookings = ui.tab('Manage Bookings')
            tab_reviews = ui.tab('Manage Reviews')
            
        with ui.tab_panels(tabs, value=tab_analytics).classes('w-full bg-transparent p-0 mt-8'):
            
            # --- TAB 1: ANALYTICS ---
            with ui.tab_panel(tab_analytics):
                loading_stats = ui.spinner('audio', size='lg', color='primary').classes('mx-auto mt-20')
                analytics_container = ui.column().classes('w-full invisible')
                
                async def load_analytics():
                    stats = await api_client.get_admin_stats()
                    loading_stats.delete()
                    analytics_container.classes(remove='invisible')
                    
                    with analytics_container:
                        with ui.row().classes('w-full gap-4 mb-8'):
                            with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                ui.icon('attach_money', color='positive').classes('text-4xl mb-2')
                                ui.label('Total Revenue').classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                ui.label(f"Rs. {stats.get('total_revenue', 0)}").classes('text-2xl font-bold text-white mt-1')
        
                            with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                ui.icon('local_activity', color='primary').classes('text-4xl mb-2')
                                ui.label('Total Bookings').classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                ui.label(str(stats.get('total_bookings', 0))).classes('text-2xl font-bold text-white mt-1')
        
                            with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                ui.icon('movie', color='info').classes('text-4xl mb-2')
                                ui.label('Total Movies').classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                ui.label(str(stats.get('total_movies', 0))).classes('text-2xl font-bold text-white mt-1')
        
                            with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                ui.icon('group', color='warning').classes('text-4xl mb-2')
                                ui.label('Total Users').classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                ui.label(str(stats.get('total_users', 0))).classes('text-2xl font-bold text-white mt-1')
        
                            with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                ui.icon('star', color='yellow').classes('text-4xl mb-2')
                                ui.label('Top Movie').classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                ui.label(stats.get('most_booked_movie', 'N/A')).classes('text-xl font-bold text-white mt-1 text-center line-clamp-1')
        
                            with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                ui.icon('event_seat', color='negative').classes('text-4xl mb-2')
                                ui.label('Occupancy').classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                ui.label(f"{stats.get('occupancy_percentage', 0)}%").classes('text-2xl font-bold text-white mt-1')

                        # Charts Section
                        ui.label('Trends & Analytics').classes('text-2xl font-bold text-white mb-4')
                        
                        rev_data = await api_client.get_revenue_chart()
                        trend_data = await api_client.get_booking_trends()
                        
                        with ui.row().classes('w-full gap-8 mb-12'):
                            with ui.card().classes('glass-card flex-grow w-1/2 p-4'):
                                ui.label('Daily Revenue').classes('text-lg font-bold text-gray-300 mb-4')
                                ui.echart({
                                    'tooltip': {'trigger': 'axis'},
                                    'xAxis': {'type': 'category', 'data': rev_data.get('dates', [])},
                                    'yAxis': {'type': 'value'},
                                    'series': [{'data': rev_data.get('revenues', []), 'type': 'line', 'smooth': True, 'itemStyle': {'color': '#2ecc71'}, 'areaStyle': {'opacity': 0.3}}]
                                }).classes('w-full h-80')
                                
                            with ui.card().classes('glass-card flex-grow w-1/2 p-4'):
                                ui.label('Daily Bookings').classes('text-lg font-bold text-gray-300 mb-4')
                                ui.echart({
                                    'tooltip': {'trigger': 'axis'},
                                    'xAxis': {'type': 'category', 'data': trend_data.get('dates', [])},
                                    'yAxis': {'type': 'value'},
                                    'series': [{'data': trend_data.get('counts', []), 'type': 'bar', 'itemStyle': {'color': '#E50914'}}]
                                }).classes('w-full h-80')

                # Initial Load for Analytics
                ui.timer(0.1, load_analytics, once=True)

            # --- TAB 2: MOVIE MANAGEMENT ---
            with ui.tab_panel(tab_movies):
                ui.label('Add New Movie').classes('text-2xl font-bold text-white mb-4 border-b border-gray-700 pb-2')
                with ui.card().classes('glass-card w-full p-6 mb-12'):
                    with ui.row().classes('w-full gap-8'):
                        with ui.column().classes('w-1/2'):
                            title = ui.input('Title').classes('w-full mb-2')
                            genre = ui.input('Genre').classes('w-full mb-2')
                            language = ui.input('Language').classes('w-full mb-2')
                            format = ui.input('Format').classes('w-full mb-2')
                            
                            ui.label('Poster Upload').classes('text-gray-300 font-semibold mb-1')
                            poster_state = {"url": ""}
                            poster_preview = ui.image().classes('w-24 h-36 object-cover rounded hidden mb-2')
                            
                            async def handle_upload(e):
                                content = e.content.read()
                                url = await api_client.upload_poster(content, e.name)
                                if url:
                                    poster_state["url"] = url
                                    import os
                                    base = os.getenv("API_BASE_URL", "http://localhost:8000").replace("/api", "")
                                    if base.endswith("/"): base = base[:-1]
                                    poster_preview.source = f"{base}{url}"
                                    poster_preview.classes(remove='hidden')
                                    ui.notify('Poster uploaded!', type='positive')
                                else:
                                    ui.notify('Upload failed', type='negative')
                                    
                            ui.upload(on_upload=handle_upload, multiple=False, label='Drop poster here').classes('w-full mb-2')
                        
                        with ui.column().classes('w-1/2'):
                            release_date = ui.input('Release Date (YYYY-MM-DD)', value=str(date.today())).classes('w-full mb-2')
                            running_days = ui.number('Running Days', value=30).classes('w-full mb-2')
                            duration = ui.number('Duration (mins)', value=120).classes('w-full mb-2')
                            rating = ui.number('Rating (0-10)', value=8.5, format='%.1f').classes('w-full mb-2')
                    
                    description = ui.textarea('Description').classes('w-full mt-4 h-24')
                    
                    async def submit_movie():
                        try:
                            payload = {
                                "title": title.value,
                                "genre": genre.value,
                                "language": language.value,
                                "format": format.value,
                                "release_date": release_date.value,
                                "running_days": int(running_days.value),
                                "poster_url": poster_state["url"],
                                "description": description.value,
                                "duration": int(duration.value),
                                "rating": float(rating.value)
                            }
                            success = await api_client.create_movie(payload)
                            if success:
                                ui.notify('Movie added successfully!', type='positive')
                                title.value = ''
                            else:
                                ui.notify('Failed to add movie', type='negative')
                        except Exception as e:
                            ui.notify(f'Invalid input: {e}', type='negative')
                            
                    ui.button('Add Movie', color='primary', on_click=submit_movie).classes('mt-4 px-8 py-2 font-bold rounded-lg')

                ui.label('Existing Movies').classes('text-2xl font-bold text-white mb-4 border-b border-gray-700 pb-2')
                movies = await api_client.get_movies()
                
                with ui.column().classes('w-full gap-4'):
                    for m in movies:
                        with ui.card().classes('glass-card w-full p-4 flex-row justify-between items-center'):
                            with ui.row().classes('items-center gap-6'):
                                poster_url = m.get('poster_url', '')
                                if poster_url:
                                    if poster_url.startswith('/'):
                                        import os
                                        base = os.getenv("API_BASE_URL", "http://localhost:8000").replace("/api", "")
                                        if base.endswith("/"): base = base[:-1]
                                        poster_url = f"{base}{poster_url}"
                                    ui.image(poster_url).classes('w-16 h-24 rounded object-cover')
                                with ui.column():
                                    ui.label(m['title']).classes('text-xl font-bold text-white')
                                    ui.label(f"{m['genre']} | {m['language']}").classes('text-sm text-gray-400')
                            
                            async def del_movie(mid=m['id']):
                                if await api_client.delete_movie(mid):
                                    ui.notify('Movie deleted', type='positive')
                                    ui.navigate.to('/admin') 
                                    
                            ui.button('Delete', color='negative', icon='delete', on_click=del_movie).classes('px-6 py-2 rounded-lg')

            # --- TAB 3: SCHEDULE MANAGEMENT ---
            with ui.tab_panel(tab_schedule):
                ui.label('Schedule Shows').classes('text-2xl font-bold text-white mb-4')
                
                with ui.row().classes('w-full gap-8 mb-8'):
                    with ui.card().classes('glass-card w-1/3 p-4'):
                        ui.label('1. Add Theatre').classes('text-xl font-bold text-white mb-4')
                        t_name = ui.input('Theatre Name').classes('w-full mb-2')
                        t_loc = ui.input('Location').classes('w-full mb-2')
                        async def add_t():
                            if await api_client.create_theatre({"name": t_name.value, "location": t_loc.value}):
                                ui.notify("Theatre added", type="positive")
                                ui.navigate.to('/admin')
                        ui.button('Add Theatre', on_click=add_t).classes('mt-2 w-full')
                        
                    with ui.card().classes('glass-card w-1/3 p-4'):
                        ui.label('2. Add Screen').classes('text-xl font-bold text-white mb-4')
                        theatres_list = await api_client.get_theatres()
                        t_opts = {t['id']: t['name'] for t in theatres_list} if theatres_list else {}
                        s_t_id = ui.select(t_opts, label='Select Theatre').classes('w-full mb-2')
                        s_name = ui.input('Screen Name').classes('w-full mb-2')
                        async def add_s():
                            if not s_t_id.value: return ui.notify("Select theatre")
                            if await api_client.create_screen(s_t_id.value, {"name": s_name.value}):
                                ui.notify("Screen added", type="positive")
                                ui.navigate.to('/admin')
                        ui.button('Add Screen', on_click=add_s).classes('mt-2 w-full')

                    with ui.card().classes('glass-card w-1/3 p-4'):
                        ui.label('3. Add Show').classes('text-xl font-bold text-white mb-4')
                        movies_for_show = await api_client.get_movies()
                        m_opts = {m['id']: m['title'] for m in movies_for_show} if movies_for_show else {}
                        sh_m_id = ui.select(m_opts, label='Select Movie').classes('w-full mb-2')
                        
                        # Descriptive screen options
                        screens_for_show = await api_client.get_screens()
                        scr_opts = {}
                        for s in screens_for_show:
                            t_name_found = next((t['name'] for t in theatres_list if t['id'] == s['theatre_id']), f"T{s['theatre_id']}")
                            scr_opts[s['id']] = f"{t_name_found} - {s['name']}"
                            
                        sh_scr_id = ui.select(scr_opts, label='Select Screen').classes('w-full mb-2')
                        
                        with ui.input('Show Date').classes('w-full mb-2') as sh_date:
                            with ui.menu().props('no-parent-event') as menu:
                                with ui.date().bind_value(sh_date):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=menu.close).props('flat')
                            with sh_date.add_slot('append'):
                                ui.icon('event').on('click', menu.open).classes('cursor-pointer')
                        
                        sh_date.value = str(date.today())
                        
                        with ui.row().classes('w-full gap-2'):
                            sh_start = ui.input('Start (HH:MM)', value="10:00").classes('w-full flex-grow')
                            sh_end = ui.input('End (HH:MM)', value="12:30").classes('w-full flex-grow')
                        
                        sh_price = ui.number('Price Multiplier', value=1.0).classes('w-full mb-2 mt-2')
                        
                        async def add_sh():
                            if not sh_m_id.value or not sh_scr_id.value: return ui.notify("Select movie and screen")
                            payload = {
                                "movie_id": sh_m_id.value,
                                "screen_id": sh_scr_id.value,
                                "date": sh_date.value,
                                "start_time": sh_start.value,
                                "end_time": sh_end.value,
                                "price_multiplier": sh_price.value
                            }
                            if await api_client.create_show(payload):
                                ui.notify("Show scheduled", type="positive")
                                ui.navigate.to('/admin')
                        ui.button('Schedule Show', on_click=add_sh).classes('mt-2 w-full')

                # Theatre & Screen Summary
                with ui.row().classes('w-full gap-8 mb-8'):
                    with ui.card().classes('glass-card flex-grow p-4'):
                        ui.label('Theatres & Screens').classes('text-xl font-bold text-white mb-4 border-b border-gray-700 pb-2')
                        if not theatres_list:
                            ui.label('No theatres found.').classes('text-gray-400')
                        else:
                            with ui.column().classes('w-full gap-2'):
                                for t in theatres_list:
                                    with ui.expansion(f"{t['name']} ({t['location']})", icon='theater_comedy').classes('w-full bg-gray-800 rounded-lg'):
                                        if not t.get('screens'):
                                            ui.label('No screens in this theatre.').classes('p-4 text-gray-500')
                                        else:
                                            for s in t['screens']:
                                                ui.label(f"• {s['name']} (ID: {s['id']})").classes('p-2 pl-8 text-gray-300')

                ui.label('Scheduled Shows').classes('text-2xl font-bold text-white mt-8 mb-4 border-b border-gray-700 pb-2')
                all_shows = await api_client.get_all_shows()
                if not all_shows:
                    ui.label('No shows scheduled.').classes('text-gray-400')
                else:
                    with ui.column().classes('w-full gap-4'):
                        for show in all_shows:
                            with ui.card().classes('glass-card w-full p-4 flex-row justify-between items-center'):
                                with ui.row().classes('items-center gap-6'):
                                    # Find screen and theatre name for the show
                                    scr_name = "Unknown"
                                    th_name = "Unknown"
                                    if show.get('screen_id'):
                                        for t in theatres_list:
                                            for s in t.get('screens', []):
                                                if s['id'] == show['screen_id']:
                                                    scr_name = s['name']
                                                    th_name = t['name']
                                                    break
                                    
                                    with ui.column():
                                        ui.label(f"{show.get('movie', {}).get('title', 'Unknown Movie')}").classes('text-xl font-bold text-white')
                                        ui.label(f"{th_name} - {scr_name}").classes('text-md text-primary font-bold')
                                        ui.label(f"Date: {show['date']} | Time: {show['start_time']} - {show['end_time']}").classes('text-sm text-gray-400')
                                
                                async def del_sh(sid=show['id']):
                                    if await api_client.delete_show(sid):
                                        ui.notify('Show deleted', type='positive')
                                        ui.navigate.to('/admin')
                                ui.button('Delete', color='negative', icon='delete', on_click=del_sh).classes('px-6 py-2 rounded-lg')

            # --- TAB 4: BOOKINGS MANAGEMENT ---
            with ui.tab_panel(tab_bookings):
                ui.label('Manage Customer Bookings').classes('text-2xl font-bold text-white mb-4')
                bookings: List[Dict] = await api_client.get_all_bookings()
                
                if not bookings:
                    ui.label('No bookings found.').classes('text-gray-400')
                else:
                    search_query = ui.input('Search by User or Movie...', on_change=lambda e: filter_table(e.value)).classes('w-full max-w-md mb-6')
                    
                    columns = [
                        {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                        {'name': 'user', 'label': 'User ID', 'field': 'user_id', 'sortable': True},
                        {'name': 'movie', 'label': 'Movie', 'field': 'movie_title', 'sortable': True},
                        {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
                        {'name': 'seats', 'label': 'Seats', 'field': 'seats_str'},
                        {'name': 'amount', 'label': 'Amount (Rs)', 'field': 'total_amount', 'sortable': True},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions'}
                    ]
                    
                    rows = []
                    for b in bookings:
                        date_str = b['booking_date'][:10]
                        seats_str = ", ".join([s['seat_name'] for s in b.get('booked_seats', [])])
                        rows.append({
                            'id': b['id'],
                            'user_id': b['user_id'],
                            'movie_title': b['movie']['title'],
                            'date': date_str,
                            'seats_str': seats_str,
                            'total_amount': b['total_amount'],
                            'status': b.get('status', 'confirmed'),
                            'raw': b # keep raw data for actions
                        })
                    
                    table = ui.table(columns=columns, rows=rows, row_key='id', pagination=10).classes('w-full bg-gray-900 text-white')
                    
                    def filter_table(query: str):
                        query = query.lower()
                        filtered = [
                            row for row in rows 
                            if query in str(row['user_id']) or query in row['movie_title'].lower() or query in row['status']
                        ]
                        table.rows = filtered
                        
                    table.add_slot('body-cell-status', '''
                        <q-td :props="props">
                            <q-badge :color="props.value === 'confirmed' ? 'positive' : 'negative'">
                                {{ props.value }}
                            </q-badge>
                        </q-td>
                    ''')

                    # We handle actions using custom HTML slots and Vue events in nicegui but the easiest way is to add a separate card list or use add_slot with an event.
                    # A robust way in NiceGUI 1.3+ is adding buttons in a column, but since it's a QTable slot:
                    table.add_slot('body-cell-actions', '''
                        <q-td :props="props" class="q-gutter-sm">
                            <q-btn v-if="props.row.status === 'confirmed'" size="sm" color="warning" icon="cancel" @click="$parent.$emit('cancel', props.row)" />
                            <q-btn size="sm" color="negative" icon="delete" @click="$parent.$emit('delete', props.row)" />
                        </q-td>
                    ''')

                    async def handle_cancel(e):
                        row = e.args
                        booking_id = row['id']
                        if await api_client.cancel_booking(booking_id):
                            ui.notify(f'Booking #{booking_id} cancelled.', type='positive')
                            ui.navigate.to('/admin')
                        else:
                            ui.notify('Failed to cancel', type='negative')

                    async def handle_delete(e):
                        row = e.args
                        booking_id = row['id']
                        if await api_client.delete_booking_admin(booking_id):
                            ui.notify(f'Booking #{booking_id} deleted.', type='positive')
                            ui.navigate.to('/admin')
                        else:
                            ui.notify('Failed to delete', type='negative')

                    table.on('cancel', handle_cancel)
                    table.on('delete', handle_delete)

            # --- TAB 5: REVIEWS MODERATION ---
            with ui.tab_panel(tab_reviews):
                ui.label('Moderate Customer Reviews').classes('text-2xl font-bold text-white mb-4')
                all_reviews = await api_client.get_all_reviews()
                
                if not all_reviews:
                    ui.label('No reviews found.').classes('text-gray-400')
                else:
                    for rev in all_reviews:
                        with ui.card().classes('glass-card w-full p-6 mb-4 flex-row justify-between items-center'):
                            with ui.column():
                                with ui.row().classes('items-center gap-2'):
                                    ui.label(rev.get('user', {}).get('username', 'User')).classes('font-bold text-primary')
                                    ui.label(f"on {rev.get('movie_id')}").classes('text-xs text-gray-500')
                                
                                with ui.row().classes('gap-1'):
                                    for _ in range(rev['rating']):
                                        ui.icon('star', color='yellow', size='xs')
                                
                                ui.label(rev['comment']).classes('text-gray-300 mt-2')
                            
                            async def del_rev(rid=rev['id']):
                                if await api_client.delete_review(rid):
                                    ui.notify('Review deleted', type='positive')
                                    ui.navigate.to('/admin')
                            
                            ui.button('Delete', color='negative', icon='delete', on_click=del_rev).classes('px-6 rounded-lg')
