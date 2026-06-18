# pyrefly: ignore [missing-import]
from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar
from datetime import date
from typing import List, Dict, Any

@ui.page('/admin')
async def admin_dashboard():
    if not api_client.is_authenticated() or not api_client.is_admin():
        ui.notify('Unauthorized access', type='negative')
        ui.navigate.to('/')
        return
        
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full p-8 max-w-7xl mx-auto'):
        ui.label('Admin Control Panel').classes('text-3xl font-bold text-primary mb-8 border-l-4 border-primary pl-4')
        
        with ui.tabs().classes('w-full') as tabs:
            tab_analytics = ui.tab('Analytics')
            tab_movies = ui.tab('Manage Movies')
            tab_schedule = ui.tab('Manage Schedule')
            tab_theatres = ui.tab('Theatres')
            tab_screens = ui.tab('Screens')
            tab_pricing = ui.tab('Pricing & Rules')
            tab_media = ui.tab('Media Assets')
            tab_bookings = ui.tab('Manage Bookings')
            tab_reviews = ui.tab('Manage Reviews')
            
        with ui.tab_panels(tabs, value=tab_analytics).classes('w-full bg-transparent p-0 mt-8'):
            
            # --- TAB 1: ANALYTICS ---
            with ui.tab_panel(tab_analytics):
                loading_stats = ui.row().classes('w-full gap-4 mb-8')
                with loading_stats:
                    for _ in range(6):
                        with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                            ui.element('div').classes('shimmer h-10 w-10 rounded-full mb-2')
                            ui.element('div').classes('shimmer h-4 w-20 mb-2')
                            ui.element('div').classes('shimmer h-6 w-16')
                
                analytics_container = ui.column().classes('w-full invisible')
                
                async def load_analytics():
                    stats = await api_client.get_admin_stats()
                    loading_stats.delete()
                    analytics_container.classes(remove='invisible')
                    
                    with analytics_container:
                        with ui.row().classes('w-full gap-4 mb-8'):
                            for icon, label, val, color in [
                                ('attach_money', 'Total Revenue', f"Rs. {stats.get('total_revenue', 0)}", 'positive'),
                                ('local_activity', 'Total Bookings', str(stats.get('total_bookings', 0)), 'primary'),
                                ('movie', 'Total Movies', str(stats.get('total_movies', 0)), 'info'),
                                ('group', 'Total Users', str(stats.get('total_users', 0)), 'warning'),
                                ('star', 'Top Movie', stats.get('most_booked_movie', 'N/A'), 'yellow'),
                                ('event_seat', 'Occupancy', f"{stats.get('occupancy_percentage', 0)}%", 'negative')
                            ]:
                                with ui.card().classes('glass-card flex-grow p-6 flex-col items-center justify-center min-w-[150px]'):
                                    ui.icon(icon, color=color).classes('text-4xl mb-2')
                                    ui.label(label).classes('text-gray-400 text-sm font-semibold uppercase tracking-wider')
                                    ui.label(val).classes('text-2xl font-bold text-white mt-1 text-center truncate line-clamp-1 w-full')
        
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

                ui.timer(0.1, load_analytics, once=True)

            # --- TAB 2: MOVIE MANAGEMENT ---
            with ui.tab_panel(tab_movies):
                import os
                base = os.getenv("API_BASE_URL", "http://localhost:8001").replace("/api", "")
                if base.endswith("/"): base = base[:-1]

                async def open_edit_dialog(movie_data):
                    edit_poster_state = {"url": movie_data.get("poster_url", "")}
                    
                    with ui.dialog() as edit_dialog, ui.card().classes('w-full max-w-4xl p-6 bg-[#141414] border border-gray-800 text-white'):
                        ui.label(f'Edit Movie: {movie_data["title"]}').classes('text-2xl font-bold text-primary mb-4 border-b border-gray-800 pb-2')
                        
                        with ui.row().classes('w-full gap-8'):
                            with ui.column().classes('w-1/2'):
                                e_title = ui.input('Title', value=movie_data["title"]).classes('w-full mb-2')
                                e_genre = ui.input('Genre', value=movie_data["genre"]).classes('w-full mb-2')
                                e_lang = ui.input('Language', value=movie_data["language"]).classes('w-full mb-2')
                                e_format = ui.input('Format', value=movie_data["format"]).classes('w-full mb-2')
                                
                                ui.label('Movie Poster').classes('text-gray-300 font-semibold mb-1')
                                
                                init_poster = movie_data.get("poster_url") if movie_data.get("poster_url") else "/uploads/defaults/no-poster.png"
                                if not init_poster.startswith('http'):
                                    init_resolved = f"{base}{init_poster}"
                                else:
                                    init_resolved = init_poster
                                    
                                e_poster_preview = ui.image(init_resolved).classes('w-24 h-36 object-cover rounded mb-2').props(f"onerror=\"this.onerror=null; this.src='{base}/uploads/defaults/no-poster.png';\"")
                                
                                async def handle_edit_upload(e):
                                    content = e.content.read()
                                    url = await api_client.upload_poster(content, e.name)
                                    if url:
                                        edit_poster_state["url"] = url
                                        e_poster_preview.source = f"{base}{url}" if url.startswith('/') else url
                                        ui.notify('Poster uploaded successfully!', type='positive')
                                    else:
                                        ui.notify('Upload failed', type='negative')
                                        
                                with ui.tabs().classes('w-full mb-3') as e_poster_tabs:
                                    e_upload_tab = ui.tab('Upload Image')
                                    e_url_tab = ui.tab('Use Image URL')
                                    
                                init_tab = e_url_tab if movie_data.get("poster_source_type") == "external_url" else e_upload_tab
                                with ui.tab_panels(e_poster_tabs, value=init_tab).classes('w-full bg-transparent p-0 mb-2') as e_poster_panels:
                                    with ui.tab_panel(e_upload_tab):
                                        ui.upload(on_upload=handle_edit_upload, multiple=False, label='Drop poster here').classes('w-full mb-2')
                                        
                                    with ui.tab_panel(e_url_tab):
                                        with ui.row().classes('w-full items-center gap-2 mb-2'):
                                            e_url_input = ui.input('Paste image URL here...', value=movie_data.get("poster_url", "") if movie_data.get("poster_url", "").startswith('http') else "").props('dark standout rounded').classes('flex-grow')
                                            async def verify_edit_url():
                                                val = e_url_input.value.strip()
                                                if not val:
                                                    ui.notify("Please paste a URL first.", type="warning")
                                                    return
                                                if not (val.startswith("http://") or val.startswith("https://")):
                                                    ui.notify("Invalid protocol. Only http:// and https:// allowed.", type="warning")
                                                    return
                                                ui.notify("Validating external image URL...", type="info")
                                                validated_url = await api_client.upload_poster(image_url=val)
                                                if validated_url:
                                                    edit_poster_state["url"] = validated_url
                                                    e_poster_preview.source = val
                                                    ui.notify("External Image URL validated successfully!", type="positive")
                                                else:
                                                    ui.notify("Invalid external image URL or broken headers.", type="negative")
                                                    
                                            ui.button('Verify', on_click=verify_edit_url, color='info').classes('px-4 rounded-lg')
                            
                            with ui.column().classes('w-1/2'):
                                e_rel_date = ui.input('Release Date (YYYY-MM-DD)', value=str(movie_data["release_date"])).classes('w-full mb-2')
                                e_run_days = ui.number('Running Days', value=movie_data["running_days"]).classes('w-full mb-2')
                                e_duration = ui.number('Duration (mins)', value=movie_data["duration"]).classes('w-full mb-2')
                                e_rating = ui.number('Rating (0-10)', value=movie_data["rating"], format='%.1f').classes('w-full mb-2')
                                e_desc = ui.textarea('Description', value=movie_data.get("description", "")).classes('w-full h-24')
                        
                        async def submit_edit():
                            if not e_title.value.strip():
                                ui.notify('Movie title is required!', type='negative')
                                return
                            if not e_genre.value.strip():
                                ui.notify('Movie genre is required!', type='negative')
                                return
                            if not e_lang.value.strip():
                                ui.notify('Movie language is required!', type='negative')
                                return
                                
                            final_poster = edit_poster_state["url"].strip()
                            if not final_poster:
                                with ui.dialog() as e_confirm_dialog, ui.card().classes('p-6 bg-[#1a1a1a] border border-gray-800 text-white'):
                                    ui.label('No Poster Provided').classes('text-xl font-bold mb-2 text-primary')
                                    ui.label('You have not uploaded or pasted a poster URL. A default placeholder will be used. Do you want to save this movie?').classes('text-gray-300 mb-6')
                                    with ui.row().classes('w-full justify-end gap-4'):
                                        ui.button('Cancel', color='secondary', on_click=lambda: e_confirm_dialog.submit(False)).classes('px-4')
                                        ui.button('Proceed', color='primary', on_click=lambda: e_confirm_dialog.submit(True)).classes('px-4')
                                
                                proceed = await e_confirm_dialog
                                if not proceed:
                                    return
                            
                            payload = {
                                "title": e_title.value,
                                "genre": e_genre.value,
                                "language": e_lang.value,
                                "format": e_format.value,
                                "release_date": e_rel_date.value,
                                "running_days": int(e_run_days.value) if e_run_days.value else 30,
                                "poster_url": final_poster if final_poster else "/uploads/defaults/no-poster.png",
                                "poster_source_type": ("upload" if e_poster_tabs.value == e_upload_tab else "external_url") if final_poster else "upload",
                                "description": e_desc.value,
                                "duration": int(e_duration.value) if e_duration.value else 120,
                                "rating": float(e_rating.value) if e_rating.value else 8.5
                            }
                            
                            if await api_client.update_movie(movie_data["id"], payload):
                                ui.notify('Movie updated successfully!', type='positive')
                                edit_dialog.close()
                                ui.navigate.to('/admin')
                            else:
                                ui.notify('Failed to update movie.', type='negative')
                        
                        with ui.row().classes('w-full justify-end gap-4 mt-6'):
                            ui.button('Cancel', color='secondary', on_click=edit_dialog.close).classes('px-6 rounded-lg')
                            ui.button('Save Changes', color='primary', on_click=submit_edit).classes('px-6 rounded-lg font-bold')
                            
                    edit_dialog.open()

                ui.label('Add New Movie').classes('text-2xl font-bold text-white mb-4 border-b border-gray-700 pb-2')
                with ui.card().classes('glass-card w-full p-6 mb-12'):
                    with ui.row().classes('w-full gap-8'):
                        with ui.column().classes('w-1/2'):
                            title = ui.input('Title').classes('w-full mb-2')
                            genre = ui.input('Genre').classes('w-full mb-2')
                            language = ui.input('Language').classes('w-full mb-2')
                            format = ui.input('Format').classes('w-full mb-2')
                            
                            ui.label('Movie Poster').classes('text-gray-300 font-semibold mb-1')
                            poster_state = {"url": ""}
                            
                            poster_preview = ui.image().classes('w-24 h-36 object-cover rounded hidden mb-2').props(f"onerror=\"this.onerror=null; this.src='{base}/uploads/defaults/no-poster.png'; ui.notify('Warning: The image URL could not be resolved or loaded in the browser.', type='warning');\"")
                            
                            async def handle_upload(e):
                                content = e.content.read()
                                url = await api_client.upload_poster(content, e.name)
                                if url:
                                    poster_state["url"] = url
                                    poster_preview.source = f"{base}{url}" if url.startswith('/') else url
                                    poster_preview.classes(remove='hidden')
                                    ui.notify('Poster uploaded successfully!', type='positive')
                                else:
                                    ui.notify('Upload failed', type='negative')

                            with ui.tabs().classes('w-full mb-3') as poster_tabs:
                                upload_tab = ui.tab('Upload Image')
                                url_tab = ui.tab('Use Image URL')
                                
                            with ui.tab_panels(poster_tabs, value=upload_tab).classes('w-full bg-transparent p-0 mb-2') as poster_panels:
                                with ui.tab_panel(upload_tab):
                                    ui.upload(on_upload=handle_upload, multiple=False, label='Drop poster here').classes('w-full mb-2')
                                    
                                with ui.tab_panel(url_tab):
                                    with ui.row().classes('w-full items-center gap-2 mb-2'):
                                        url_input = ui.input('Paste image URL here...').props('dark standout rounded').classes('flex-grow')
                                        async def verify_url():
                                            val = url_input.value.strip()
                                            if not val:
                                                ui.notify("Please paste a URL first.", type="warning")
                                                return
                                            if not (val.startswith("http://") or val.startswith("https://")):
                                                ui.notify("Invalid protocol. Only http:// and https:// allowed.", type="warning")
                                                return
                                            ui.notify("Validating external image URL...", type="info")
                                            validated_url = await api_client.upload_poster(image_url=val)
                                            if validated_url:
                                                poster_state["url"] = validated_url
                                                poster_preview.source = val
                                                poster_preview.classes(remove='hidden')
                                                ui.notify("External Image URL validated successfully!", type="positive")
                                            else:
                                                ui.notify("Invalid external image URL or broken headers.", type="negative")
                                                
                                        ui.button('Verify', on_click=verify_url, color='info').classes('px-4 rounded-lg')
                        
                        with ui.column().classes('w-1/2'):
                            release_date = ui.input('Release Date (YYYY-MM-DD)', value=str(date.today())).classes('w-full mb-2')
                            running_days = ui.number('Running Days', value=30).classes('w-full mb-2')
                            duration = ui.number('Duration (mins)', value=120).classes('w-full mb-2')
                            rating = ui.number('Rating (0-10)', value=8.5, format='%.1f').classes('w-full mb-2')
                    
                    description = ui.textarea('Description').classes('w-full mt-4 h-24')
                    
                    async def submit_movie():
                        if not title.value.strip():
                            ui.notify('Movie title is required!', type='negative')
                            return
                        if not genre.value.strip():
                            ui.notify('Movie genre is required!', type='negative')
                            return
                        if not language.value.strip():
                            ui.notify('Movie language is required!', type='negative')
                            return
                            
                        p_url = poster_state["url"].strip()
                        if not p_url:
                            with ui.dialog() as confirm_dialog, ui.card().classes('p-6 bg-[#1a1a1a] border border-gray-800 text-white'):
                                ui.label('No Poster Provided').classes('text-xl font-bold mb-2 text-primary')
                                ui.label('You have not uploaded or pasted a poster URL. A default placeholder will be used. Do you want to save this movie?').classes('text-gray-300 mb-6')
                                with ui.row().classes('w-full justify-end gap-4'):
                                    ui.button('Cancel', color='secondary', on_click=lambda: confirm_dialog.submit(False)).classes('px-4')
                                    ui.button('Proceed', color='primary', on_click=lambda: confirm_dialog.submit(True)).classes('px-4')
                            
                            proceed = await confirm_dialog
                            if not proceed:
                                return
                                
                        payload = {
                            "title": title.value,
                            "genre": genre.value,
                            "language": language.value,
                            "format": format.value,
                            "release_date": release_date.value,
                            "running_days": int(running_days.value) if running_days.value else 30,
                            "poster_url": p_url if p_url else "/uploads/defaults/no-poster.png",
                            "poster_source_type": ("upload" if poster_tabs.value == upload_tab else "external_url") if p_url else "upload",
                            "description": description.value,
                            "duration": int(duration.value) if duration.value else 120,
                            "rating": float(rating.value) if rating.value else 8.5
                        }
                        if await api_client.create_movie(payload):
                            ui.notify('Movie added successfully!', type='positive')
                            ui.navigate.to('/admin')
                            
                    ui.button('Add Movie', color='primary', on_click=submit_movie).classes('mt-4 px-8 py-2 font-bold rounded-lg')

                ui.label('Existing Movies').classes('text-2xl font-bold text-white mb-4 border-b border-gray-700 pb-2')
                movies = await api_client.get_movies()
                with ui.column().classes('w-full gap-4'):
                    for m in movies:
                        with ui.card().classes('glass-card w-full p-4 flex-row justify-between items-center'):
                            with ui.row().classes('items-center gap-6'):
                                poster = m.get('poster_url') if m.get('poster_url') else "/uploads/defaults/no-poster.png"
                                
                                if not poster.startswith('http'):
                                    resolved_url = f"{base}{poster}"
                                else:
                                    resolved_url = poster
                                    
                                ui.image(resolved_url).classes('w-16 h-24 rounded object-cover').props(f"onerror=\"this.onerror=null; this.src='{base}/uploads/defaults/no-poster.png';\"")
                                with ui.column():
                                    ui.label(m['title']).classes('text-xl font-bold text-white')
                                    ui.label(f"{m['genre']} | {m['language']}").classes('text-sm text-gray-400')
                            with ui.row().classes('gap-2'):
                                ui.button('Edit', color='primary', icon='edit', on_click=lambda movie=m: open_edit_dialog(movie)).classes('px-4 py-2 rounded-lg')
                                async def delete_movie_action(mid=m['id']):
                                    if await api_client.delete_movie(mid):
                                        ui.notify("Movie deleted successfully!", type="positive")
                                        ui.navigate.to('/admin')
                                    else:
                                        ui.notify("Failed to delete movie.", type="negative")
                                ui.button('Delete', color='negative', icon='delete', on_click=delete_movie_action).classes('px-4 py-2 rounded-lg')

            # --- TAB 3: SCHEDULE MANAGEMENT ---
            with ui.tab_panel(tab_schedule):
                ui.label('Schedule Shows').classes('text-2xl font-bold text-white mb-4')
                theatres_list = await api_client.get_theatres()
                
                with ui.card().classes('glass-card w-full p-4 mb-6'):
                    ui.label('Create Showtime').classes('text-xl font-bold text-white mb-4')
                    movies_for_show = await api_client.get_movies()
                    m_opts = {m['id']: m['title'] for m in movies_for_show}
                    sh_m_id = ui.select(m_opts, label='Select Movie').classes('w-full mb-2')
                    
                    screens_for_show = await api_client.get_screens()
                    scr_opts = {}
                    for s in screens_for_show:
                        th_name = next((t['name'] for t in theatres_list if t['id'] == s['theatre_id']), f"T{s['theatre_id']}")
                        scr_opts[s['id']] = f"{th_name} - {s['name']}"
                    sh_scr_id = ui.select(scr_opts, label='Select Screen').classes('w-full mb-2')
                    sh_date = ui.input('Show Date (YYYY-MM-DD)', value=str(date.today())).classes('w-full mb-2')
                    sh_start = ui.input('Start (HH:MM)', value="10:00").classes('w-full mb-2')
                    sh_end = ui.input('End (HH:MM)', value="12:30").classes('w-full mb-2')
                    sh_price = ui.number('Price Multiplier', value=1.0).classes('w-full mb-2')
                    
                    async def add_sh():
                        payload = {
                            "movie_id": sh_m_id.value,
                            "screen_id": sh_scr_id.value,
                            "date": sh_date.value,
                            "start_time": sh_start.value,
                            "end_time": sh_end.value,
                            "price_multiplier": sh_price.value
                        }
                        if await api_client.create_show(payload):
                            ui.notify("Show scheduled!", type="positive")
                            ui.navigate.to('/admin')
                    ui.button('Schedule Show', on_click=add_sh).classes('mt-2 w-full')

                ui.label('Existing Scheduled Shows & Seating Grid').classes('text-xl font-bold text-white mt-8 mb-4 border-b border-gray-700 pb-2')
                shows = await api_client.get_all_shows()
                
                for s in shows:
                    movie_title = m_opts.get(s['movie_id'], f"Movie #{s['movie_id']}")
                    screen_desc = scr_opts.get(s['screen_id'], f"Screen #{s['screen_id']}")
                    
                    try:
                        stats = await api_client.get_show_stats(s['id'])
                    except Exception:
                        stats = {}
                        
                    occ_rate = stats.get("occupancy_rate", 0.0)
                    res_rate = stats.get("reservation_rate", 0.0)
                    conv_rate = stats.get("conversion_rate", 0.0)
                    metrics = stats.get("reservation_metrics", {})
                    
                    with ui.card().classes('glass-card w-full p-4 mb-4 flex-row justify-between items-center'):
                        with ui.column().classes('gap-1'):
                            ui.label(movie_title).classes('text-lg font-bold text-white')
                            ui.label(f"{screen_desc} | {s['date']} at {s['start_time']} - {s['end_time']}").classes('text-sm text-gray-400')
                            with ui.row().classes('gap-4 mt-2 text-xs font-semibold'):
                                ui.label(f"Occupancy: {occ_rate}% ({stats.get('booked_count', 0)} booked)").classes('text-positive')
                                ui.label(f"Reserved: {res_rate}% ({stats.get('reserved_count', 0)} reserved)").classes('text-amber-500')
                                ui.label(f"Conversion: {conv_rate}%").classes('text-info')
                                ui.label(f"Convs: {metrics.get('converted', 0)} | Exps: {metrics.get('expired', 0)}").classes('text-gray-400')
                        
                        with ui.row().classes('gap-2'):
                            async def open_seating_dialog(show_id=s['id'], title=f"{movie_title} - {s['start_time']}"):
                                try:
                                    latest_stats = await api_client.get_show_seat_statuses(show_id)
                                    booked_seats = set(latest_stats.get("booked", []))
                                    reserved_seats = set(latest_stats.get("reserved", []))
                                except Exception:
                                    booked_seats = set()
                                    reserved_seats = set()
                                    
                                try:
                                    this_show = await api_client.get_show(show_id)
                                    screen_total_seats = this_show.get("screen", {}).get("total_seats", 220)
                                except Exception:
                                    screen_total_seats = 220
                                    
                                with ui.dialog() as diag, ui.card().classes('w-full max-w-4xl p-6 bg-[#0a0a0a] border border-zinc-800 text-white items-center'):
                                    ui.label(f"Live Occupancy Grid: {title}").classes('text-2xl font-bold text-primary mb-2')
                                    ui.label("SCREEN THIS WAY").classes('text-gray-500 tracking-[0.5em] mb-4 text-xs')
                                    ui.element('div').classes('w-full h-2 bg-gradient-to-b from-[#E50914] to-transparent rounded-t-full mb-6')
                                    
                                    cols = 20 if screen_total_seats > 100 else 10
                                    import math
                                    total_rows = math.ceil(screen_total_seats / cols)
                                    row_letters = [chr(65 + i) for i in range(total_rows)]
                                    
                                    with ui.column().classes('gap-3'):
                                        for row_idx, row in enumerate(row_letters):
                                            if row_idx < total_rows - 1:
                                                seat_map = {c: c + 1 for c in range(cols)}
                                            else:
                                                k = screen_total_seats - row_idx * cols
                                                if k == cols:
                                                    seat_map = {c: c + 1 for c in range(cols)}
                                                elif k == 1:
                                                    seat_map = {(cols - 1) // 2: 1}
                                                else:
                                                    seat_map = {}
                                                    for i in range(k):
                                                        idx = round(i * (cols - 1) / (k - 1))
                                                        seat_map[idx] = i + 1
                                                        
                                            with ui.row().classes('justify-center gap-1'):
                                                ui.label(row).classes('w-6 text-center font-bold self-center text-xs text-gray-500')
                                                for col_idx in range(cols):
                                                    if col_idx in seat_map:
                                                        seat_num = seat_map[col_idx]
                                                        seat_name = f"{row}{seat_num}"
                                                        
                                                        if seat_name in booked_seats:
                                                            seat_color = '#333333'
                                                            tooltip_text = f"Seat {seat_name} (Booked)"
                                                        elif seat_name in reserved_seats:
                                                            seat_color = '#d35400'
                                                            tooltip_text = f"Seat {seat_name} (Reserved)"
                                                        else:
                                                            seat_color = '#e50914'
                                                            tooltip_text = f"Seat {seat_name} (Available)"
                                                            
                                                        btn = ui.button('', color=None).classes('min-w-[24px] min-h-[24px] max-w-[24px] max-h-[24px] p-0 rounded-sm').style(f'background: {seat_color}; border: 1px solid rgba(0,0,0,0.5); cursor: default;')
                                                        btn.tooltip(tooltip_text)
                                                    else:
                                                        ui.element('div').classes('w-[24px] h-[24px] m-[1px]').style('opacity: 0;')
                                                        
                                    with ui.row().classes('mt-6 gap-6 text-xs justify-center'):
                                        with ui.row().classes('items-center gap-1'):
                                            ui.element('div').classes('w-4 h-4 rounded-sm').style('background: #e50914;')
                                            ui.label('Available')
                                        with ui.row().classes('items-center gap-1'):
                                            ui.element('div').classes('w-4 h-4 rounded-sm').style('background: #d35400;')
                                            ui.label('Reserved')
                                        with ui.row().classes('items-center gap-1'):
                                            ui.element('div').classes('w-4 h-4 rounded-sm').style('background: #333333;')
                                            ui.label('Booked')
                                            
                                    ui.button('Close', on_click=diag.close).classes('mt-6 px-6 py-2 rounded-lg bg-zinc-800')
                                diag.open()
                                
                            ui.button('View Layout Grid', icon='grid_on', color='info', on_click=open_seating_dialog).classes('px-4 rounded-lg')
                            
                            async def delete_sh_action(show_id=s['id']):
                                if await api_client.delete_show(show_id):
                                    ui.notify("Show deleted successfully!", type="positive")
                                    ui.navigate.to('/admin')
                                else:
                                    ui.notify("Failed to delete show.", type="negative")
                            ui.button('Delete', color='negative', icon='delete', on_click=delete_sh_action).classes('px-4 rounded-lg')

            # --- TAB 4: THEATRES MANAGEMENT ---
            with ui.tab_panel(tab_theatres):
                ui.label('Manage Theatres').classes('text-2xl font-bold text-white mb-4')
                
                with ui.card().classes('glass-card w-full p-6 mb-8'):
                    ui.label('Add New Theatre').classes('text-xl font-bold text-white mb-4')
                    with ui.row().classes('w-full gap-4'):
                        new_th_name = ui.input('Theatre Name').classes('flex-grow')
                        new_th_city = ui.input('City').classes('flex-grow')
                        new_th_state = ui.input('State').classes('flex-grow')
                    new_th_addr = ui.input('Address').classes('w-full mb-2')
                    new_th_desc = ui.textarea('Description').classes('w-full mb-2')
                    
                    ui.label('Theatre Banner/Poster').classes('text-gray-300 font-semibold mb-1')
                    th_banner_state = {"url": ""}
                    th_banner_preview = ui.image().classes('w-36 h-20 object-cover rounded hidden mb-2').props("onerror=\"this.onerror=null; this.src='https://via.placeholder.com/300x150.png?text=Invalid+Image'; ui.notify('Warning: The image URL could not be resolved or loaded in the browser.', type='warning');\"")
                    
                    async def handle_th_upload(e):
                        content = e.content.read()
                        asset = await api_client.upload_media_asset(content, e.name, "banner")
                        if asset:
                            th_banner_state["url"] = asset["public_url"]
                            import os
                            base = os.getenv("API_BASE_URL", "http://localhost:8001").replace("/api", "")
                            if base.endswith("/"): base = base[:-1]
                            th_banner_preview.source = f"{base}{asset['public_url']}" if asset['public_url'].startswith('/') else asset['public_url']
                            th_banner_preview.classes(remove='hidden')
                            ui.notify('Banner uploaded successfully!', type='positive')
                        else:
                            ui.notify('Upload failed', type='negative')
                            
                    with ui.tabs().classes('w-full mb-3') as th_tabs:
                        th_upload_tab = ui.tab('Upload Image')
                        th_url_tab = ui.tab('Use Image URL')
                        
                    with ui.tab_panels(th_tabs, value=th_upload_tab).classes('w-full bg-transparent p-0 mb-2') as th_panels:
                        with ui.tab_panel(th_upload_tab):
                            ui.upload(on_upload=handle_th_upload, multiple=False, label='Drop banner here').classes('w-full mb-2')
                            
                        with ui.tab_panel(th_url_tab):
                            async def on_th_url_change(e):
                                val = e.value.strip()
                                if val:
                                    if not (val.startswith("http://") or val.startswith("https://")):
                                        ui.notify("Invalid protocol. Only http:// and https:// allowed.", type="warning")
                                        return
                                    
                                    asset = await api_client.upload_media_asset(asset_type="banner", image_url=val)
                                    if asset:
                                        th_banner_state["url"] = asset["public_url"]
                                        th_banner_preview.source = val
                                        th_banner_preview.classes(remove='hidden')
                                        ui.notify("External Banner URL validated successfully!", type="positive")
                                    else:
                                        ui.notify("Invalid external image URL or broken headers.", type="negative")
                                    
                            ui.input('Paste banner URL here...', on_change=on_th_url_change).props('dark standout rounded').classes('w-full mb-2')
                    
                    async def save_theatre():
                        payload = {
                            "name": new_th_name.value,
                            "address": new_th_addr.value,
                            "city": new_th_city.value,
                            "state": new_th_state.value,
                            "description": new_th_desc.value,
                            "banner_image_url": th_banner_state["url"],
                            "is_active": True
                        }
                        if await api_client.create_theatre(payload):
                            ui.notify("Theatre added successfully!", type="positive")
                            ui.navigate.to('/admin')
                    ui.button('Add Theatre', on_click=save_theatre).classes('w-full mt-2')

                ui.label('Existing Theatres').classes('text-xl font-bold text-white mb-4')
                for t in theatres_list:
                    status_badge = "Active" if t["is_active"] else "Inactive"
                    badge_color = "positive" if t["is_active"] else "negative"
                    with ui.card().classes('glass-card w-full p-4 mb-4 flex-row justify-between items-center'):
                        with ui.column():
                            ui.label(t["name"]).classes('text-xl font-bold text-white')
                            ui.label(f"{t['address']}, {t['city']}, {t['state']}").classes('text-sm text-gray-400')
                            ui.badge(status_badge, color=badge_color)
                        with ui.row().classes('gap-2'):
                            # Toggle Active/Inactive
                            async def toggle_active(theatre=t):
                                payload = {"is_active": not theatre["is_active"]}
                                if await api_client.update_theatre(theatre["id"], payload):
                                    ui.notify("Theatre status updated!", type="positive")
                                    ui.navigate.to('/admin')
                            ui.button('Toggle Status', color='warning', on_click=toggle_active).classes('px-4 rounded-lg')
                            async def delete_theatre_action(tid=t['id']):
                                if await api_client.delete_theatre(tid):
                                    ui.notify("Theatre deleted successfully!", type="positive")
                                    ui.navigate.to('/admin')
                                else:
                                    ui.notify("Failed to delete theatre.", type="negative")
                            ui.button('Delete', color='negative', on_click=delete_theatre_action).classes('px-4 rounded-lg')

            # --- TAB 5: SCREENS MANAGEMENT ---
            with ui.tab_panel(tab_screens):
                ui.label('Manage Screens').classes('text-2xl font-bold text-white mb-4')
                
                with ui.card().classes('glass-card w-full p-6 mb-8'):
                    ui.label('Add New Screen').classes('text-xl font-bold text-white mb-4')
                    s_t_id = ui.select({t['id']: t['name'] for t in theatres_list}, label='Select Theatre').classes('w-full mb-2')
                    s_name = ui.input('Screen Name').classes('w-full mb-2')
                    s_type = ui.select(['Standard', 'IMAX', '3D', 'Dolby Atmos'], value='Standard', label='Screen Type').classes('w-full mb-2')
                    s_seats = ui.number('Total Seats', value=220).classes('w-full mb-2')
                    
                    async def save_screen():
                        payload = {
                            "theatre_id": s_t_id.value,
                            "name": s_name.value,
                            "screen_type": s_type.value,
                            "total_seats": int(s_seats.value),
                            "is_active": True
                        }
                        if await api_client.create_screen(payload):
                            ui.notify("Screen added successfully!", type="positive")
                            ui.navigate.to('/admin')
                    ui.button('Add Screen', on_click=save_screen).classes('w-full mt-2')

                ui.label('Existing Screens').classes('text-xl font-bold text-white mb-4')
                all_screens = await api_client.get_screens()
                for s in all_screens:
                    th_name = next((t['name'] for t in theatres_list if t['id'] == s['theatre_id']), "Unknown Theatre")
                    
                    try:
                        layouts = await api_client.get_all_layouts_for_screen(s['id'])
                    except Exception:
                        layouts = []
                    
                    has_published = any(l.get('is_published') for l in layouts)
                    if has_published:
                        status_text = "Published"
                        badge_color = "positive"
                    elif layouts:
                        status_text = "Draft"
                        badge_color = "warning"
                    else:
                        status_text = "No Layout"
                        badge_color = "negative"

                    with ui.card().classes('glass-card w-full p-4 mb-4 flex-row justify-between items-center'):
                        with ui.column():
                            with ui.row().classes('items-center gap-3'):
                                ui.label(s["name"]).classes('text-xl font-bold text-white')
                                ui.badge(status_text, color=badge_color)
                            ui.label(f"Theatre: {th_name} | Type: {s['screen_type']} | Seats: {s['total_seats']}").classes('text-sm text-gray-400')
                        with ui.row().classes('gap-2'):
                            ui.button('Design Layout', color='primary', on_click=lambda sid=s['id']: ui.navigate.to(f'/admin/layout-designer/{sid}')).classes('px-4 rounded-lg')
                            
                            async def toggle_screen_status(sid=s['id'], active=s['is_active']):
                                if await api_client.update_screen(sid, {"is_active": not active}):
                                    ui.notify("Screen status updated!", type="positive")
                                    ui.navigate.to('/admin')
                                else:
                                    ui.notify("Failed to update screen status.", type="negative")
                            
                            ui.button('Deactivate' if s["is_active"] else 'Activate', color='warning', on_click=toggle_screen_status).classes('px-4 rounded-lg')

            # --- TAB 6: PRICING & RULES ---
            with ui.tab_panel(tab_pricing):
                ui.label('Seat Pricing & Rules Engine').classes('text-2xl font-bold text-white mb-6')
                
                # Dropdowns for filtering/selecting base pricing
                pricings = await api_client.get_pricings()
                all_screens = await api_client.get_screens()
                
                selected_theatre_id = {"value": None}
                selected_screen_id = {"value": None}
                selected_seat_cat = {"value": "Normal"}
                
                override_state = {"override": False}
                override_switch = ui.switch('Admin Seat Hierarchy Override', value=False, on_change=lambda e: override_state.update({"override": e.value})).classes('mb-4')
                
                pricing_edit_container = ui.column().classes('w-full mt-4')
                
                def update_pricing_editor():
                    pricing_edit_container.clear()
                    
                    tid = selected_theatre_id["value"]
                    sid = selected_screen_id["value"]
                    cat = selected_seat_cat["value"]
                    
                    if not tid:
                        with pricing_edit_container:
                            ui.label("Please select a theatre first.").classes("text-gray-400 italic")
                        return
                        
                    matching_pricing = None
                    for pr in pricings:
                        if pr["theatre_id"] == tid and pr["seat_category"] == cat:
                            if pr.get("screen_id") == sid:
                                matching_pricing = pr
                                break
                                
                    with pricing_edit_container:
                        if matching_pricing:
                            with ui.card().classes('glass-card w-full p-6 flex-row justify-between items-center'):
                                with ui.column():
                                    ui.label(f"Configure rate for {cat}").classes('text-lg font-bold text-white')
                                    th_name = next((t['name'] for t in theatres_list if t['id'] == tid), "Theatre")
                                    scr_name = "Global" if sid is None else next((s['name'] for s in all_screens if s['id'] == sid), "Screen")
                                    ui.label(f"{th_name} — {scr_name}").classes('text-sm text-gray-400')
                                with ui.row().classes('items-center gap-4'):
                                    price_input = ui.number('Base Price', value=matching_pricing["base_price"], format='%.2f').classes('w-32')
                                    
                                    async def save_pr(pricing_id=matching_pricing["id"], inp=price_input):
                                        try:
                                            success = await api_client.update_pricing(pricing_id, float(inp.value), override=override_state["override"])
                                            if success:
                                                ui.notify("Pricing base rate saved!", type="positive")
                                                nonlocal pricings
                                                pricings = await api_client.get_pricings()
                                        except Exception as e:
                                            ui.notify(str(e), type="negative")
                                            
                                    ui.button('Save', color='primary', on_click=save_pr).classes('px-6 py-2 rounded-lg font-bold')
                        else:
                            ui.label("No pricing configuration found for this combination.").classes("text-yellow-400 italic")
                
                with ui.row().classes('w-full gap-4 mb-4 items-center'):
                    th_opts = {t['id']: t['name'] for t in theatres_list}
                    def on_theatre_select(e):
                        selected_theatre_id["value"] = e.value
                        if e.value:
                            scr_opts = {None: "Global (All Screens)"}
                            for s in all_screens:
                                if s["theatre_id"] == e.value:
                                    scr_opts[s["id"]] = s["name"]
                            screen_dropdown.options = scr_opts
                            screen_dropdown.value = None
                        else:
                            screen_dropdown.options = {None: "Global (All Screens)"}
                            screen_dropdown.value = None
                        selected_screen_id["value"] = None
                        update_pricing_editor()
                        
                    theatre_dropdown = ui.select(th_opts, label='Select Theatre', on_change=on_theatre_select).classes('flex-grow')
                    
                    def on_screen_select(e):
                        selected_screen_id["value"] = e.value
                        update_pricing_editor()
                        
                    screen_dropdown = ui.select({None: "Global (All Screens)"}, label='Select Screen', on_change=on_screen_select).classes('flex-grow')
                    
                    def on_cat_select(e):
                        selected_seat_cat["value"] = e.value
                        update_pricing_editor()
                        
                    cat_dropdown = ui.select(['Normal', 'Executive', 'Premium'], value='Normal', label='Seat Category', on_change=on_cat_select).classes('flex-grow')
                
                update_pricing_editor()

                # Rule builder
                ui.separator().classes('my-8')
                ui.label('Add Dynamic Pricing Rule').classes('text-xl font-bold text-white mb-4')
                with ui.card().classes('glass-card w-full p-6 mb-8'):
                    r_name = ui.input('Rule Name (e.g. Weekend Surge)').classes('w-full mb-2')
                    r_type = ui.select(['weekend', 'holiday', 'event', 'surge', 'time_based'], value='weekend', label='Rule Type').classes('w-full mb-2')
                    r_mult = ui.number('Surge Multiplier', value=1.2).classes('w-full mb-2')
                    r_priority = ui.number('Priority', value=1).classes('w-full mb-2')
                    r_stack = ui.switch('Stackable', value=True).classes('mb-2')
                    
                    async def save_rule():
                        payload = {
                            "name": r_name.value,
                            "rule_type": r_type.value,
                            "multiplier": float(r_mult.value),
                            "priority": int(r_priority.value),
                            "stackable": r_stack.value,
                            "is_active": True
                        }
                        if await api_client.create_pricing_rule(payload):
                            ui.notify("Pricing rule added!", type="positive")
                            ui.navigate.to('/admin')
                    ui.button('Create Rule', on_click=save_rule).classes('w-full mt-2')

            # --- TAB 7: MEDIA ASSETS ---
            with ui.tab_panel(tab_media):
                ui.label('Media Library & Uploads').classes('text-2xl font-bold text-white mb-4')
                
                with ui.card().classes('glass-card w-full p-6 mb-8'):
                    ui.label('Register / Upload New Media Asset (Max 2MB, JPEG/PNG)').classes('text-xl font-bold text-white mb-4')
                    m_type = ui.select(['poster', 'banner', 'screen_preview'], value='poster', label='Asset Type').classes('w-full mb-2')
                    
                    media_preview = ui.image().classes('w-32 h-20 object-cover rounded hidden mb-2').props("onerror=\"this.onerror=null; this.src='https://via.placeholder.com/300x150.png?text=Invalid+Image'; ui.notify('Warning: The image URL could not be resolved or loaded in the browser.', type='warning');\"")
                    
                    async def handle_media_upload(e):
                        content = e.content.read()
                        asset = await api_client.upload_media_asset(content, e.name, m_type.value)
                        if asset:
                            ui.notify(f"Uploaded: {asset['filename']}", type="positive")
                            import os
                            base = os.getenv("API_BASE_URL", "http://localhost:8001").replace("/api", "")
                            if base.endswith("/"): base = base[:-1]
                            media_preview.source = f"{base}{asset['public_url']}" if asset['public_url'].startswith('/') else asset['public_url']
                            media_preview.classes(remove='hidden')
                            ui.navigate.to('/admin')
                        else:
                            ui.notify("Upload failed! Dimension/size rules constraint violation.", type="negative")
                            
                    with ui.tabs().classes('w-full mb-3') as m_tabs:
                        m_upload_tab = ui.tab('Upload Image')
                        m_url_tab = ui.tab('Use Image URL')
                        
                    with ui.tab_panels(m_tabs, value=m_upload_tab).classes('w-full bg-transparent p-0 mb-2') as m_panels:
                        with ui.tab_panel(m_upload_tab):
                            ui.upload(on_upload=handle_media_upload, multiple=False, label='Drop images here').classes('w-full')
                            
                        with ui.tab_panel(m_url_tab):
                            async def on_m_url_change(e):
                                val = e.value.strip()
                                if val:
                                    if not (val.startswith("http://") or val.startswith("https://")):
                                        ui.notify("Invalid protocol. Only http:// and https:// allowed.", type="warning")
                                        return
                                    
                                    # Register external URL with backend
                                    asset = await api_client.upload_media_asset(asset_type=m_type.value, image_url=val)
                                    if asset:
                                        media_preview.source = val
                                        media_preview.classes(remove='hidden')
                                        ui.notify(f"Registered External URL: {asset['filename']}", type="positive")
                                    else:
                                        ui.notify("Invalid external image URL or broken headers.", type="negative")
                                        
                            ui.input('Paste image URL here...', on_change=on_m_url_change).props('dark standout rounded').classes('w-full mb-2')

            # --- TAB 8: BOOKINGS MANAGEMENT ---
            with ui.tab_panel(tab_bookings):
                ui.label('Manage Customer Bookings').classes('text-2xl font-bold text-white mb-4')
                bookings = await api_client.get_all_bookings()
                if not bookings:
                    ui.label('No bookings found.').classes('text-gray-400')
                else:
                    columns = [
                        {'name': 'id', 'label': 'ID', 'field': 'id', 'sortable': True},
                        {'name': 'user', 'label': 'User ID', 'field': 'user_id', 'sortable': True},
                        {'name': 'movie', 'label': 'Movie', 'field': 'movie_title', 'sortable': True},
                        {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
                        {'name': 'seats', 'label': 'Seats', 'field': 'seats_str'},
                        {'name': 'amount', 'label': 'Amount (Rs)', 'field': 'total_amount', 'sortable': True},
                        {'name': 'status', 'label': 'Status', 'field': 'status', 'sortable': True}
                    ]
                    rows = []
                    for b in bookings:
                        seats_str = ", ".join([s['seat_name'] for s in b.get('booked_seats', [])])
                        rows.append({
                            'id': b['id'],
                            'user_id': b['user_id'],
                            'movie_title': b['movie']['title'],
                            'date': b['booking_date'][:10],
                            'seats_str': seats_str,
                            'total_amount': b['total_amount'],
                            'status': b.get('status', 'confirmed')
                        })
                    ui.table(columns=columns, rows=rows, row_key='id', pagination=10).classes('w-full bg-gray-900 text-white')

            # --- TAB 9: REVIEWS MODERATION ---
            with ui.tab_panel(tab_reviews):
                ui.label('Moderate Customer Reviews').classes('text-2xl font-bold text-white mb-4')
                all_reviews = await api_client.get_all_reviews()
                if not all_reviews:
                    ui.label('No reviews found.').classes('text-gray-400')
                else:
                    for rev in all_reviews:
                        with ui.card().classes('glass-card w-full p-6 mb-4 flex-row justify-between items-center'):
                            with ui.column():
                                ui.label(rev.get('user', {}).get('username', 'User')).classes('font-bold text-primary')
                                ui.label(rev['comment']).classes('text-gray-300 mt-2')
                            async def delete_review_action(rid=rev['id']):
                                if await api_client.delete_review(rid):
                                    ui.notify("Review deleted successfully!", type="positive")
                                    ui.navigate.to('/admin')
                                else:
                                    ui.notify("Failed to delete review.", type="negative")
                            ui.button('Delete', color='negative', icon='delete', on_click=delete_review_action).classes('px-6 rounded-lg')
