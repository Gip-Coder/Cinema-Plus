from nicegui import ui
from frontend.services.api_client import api_client

def apply_theme():
    ui.colors(
        primary='#E50914', # Netflix Red
        secondary='#141414', # Dark background
        accent='#FFFFFF', # White text
        dark='#000000',
        positive='#2ecc71',
        negative='#e74c3c',
        info='#3498db',
        warning='#f1c40f'
    )
    ui.add_head_html('''
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        <style>
            /* ===== BASE ===== */
            body {
                background-color: #0a0a0a;
                color: #FFFFFF;
                font-family: 'Inter', 'Helvetica Neue', sans-serif;
            }

            /* ===== KEYFRAME ANIMATIONS ===== */
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(24px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            @keyframes fadeIn {
                from { opacity: 0; }
                to   { opacity: 1; }
            }
            @keyframes pulseGlow {
                0%, 100% { box-shadow: 0 0 8px rgba(229, 9, 20, 0.3); }
                50%      { box-shadow: 0 0 24px rgba(229, 9, 20, 0.6); }
            }
            @keyframes pulseGlowWhite {
                0%, 100% { box-shadow: 0 0 8px rgba(255, 255, 255, 0.4); }
                50%      { box-shadow: 0 0 24px rgba(255, 255, 255, 0.8); }
            }
            @keyframes shimmer {
                0%   { background-position: -200% 0; }
                100% { background-position: 200% 0; }
            }

            /* ===== MOVIE CARDS ===== */
            .movie-card {
                background: #181818;
                border-radius: 12px;
                transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.35s ease;
                overflow: hidden;
                animation: fadeInUp 0.5s ease both;
                border: 1px solid rgba(255,255,255,0.04);
            }
            .movie-card:nth-child(1) { animation-delay: 0.05s; }
            .movie-card:nth-child(2) { animation-delay: 0.1s; }
            .movie-card:nth-child(3) { animation-delay: 0.15s; }
            .movie-card:nth-child(4) { animation-delay: 0.2s; }
            .movie-card:nth-child(5) { animation-delay: 0.25s; }
            .movie-card:nth-child(6) { animation-delay: 0.3s; }
            .movie-card:hover {
                transform: scale(1.06) translateY(-6px);
                box-shadow: 0 20px 40px rgba(229, 9, 20, 0.25), 0 0 0 1px rgba(229, 9, 20, 0.15);
            }

            /* ===== GLASS CARDS ===== */
            .glass-card {
                background: rgba(24, 24, 24, 0.85);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
                animation: fadeIn 0.4s ease both;
            }
            .glass-card:hover {
                border-color: rgba(229, 9, 20, 0.2);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            }

            /* ===== SEATS ===== */
            .seat {
                width: 32px;
                height: 32px;
                border-radius: 6px 6px 3px 3px;
                margin: 3px;
                cursor: pointer;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                border: 1px solid transparent;
            }
            .seat:hover { transform: scale(1.15); }
            .seat-available { background: linear-gradient(135deg, #e50914, #b81d24) !important; }
            .seat-booked    { background: linear-gradient(135deg, #333333, #222222) !important; cursor: not-allowed !important; opacity: 0.6 !important; }
            .seat-reserved  { background: linear-gradient(135deg, #f39c12, #d35400) !important; cursor: not-allowed !important; opacity: 0.8 !important; }
            .seat-selected  { background: linear-gradient(135deg, #ffffff, #e5e5e5) !important; border: 2px solid #000000 !important; box-shadow: 0 0 12px rgba(255,255,255,0.5) !important; animation: pulseGlowWhite 2s infinite !important; }

            /* ===== BUTTONS ===== */
            .q-btn {
                transition: transform 0.2s ease, box-shadow 0.2s ease !important;
            }
            .q-btn:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 6px 16px rgba(0,0,0,0.3) !important;
            }
            .q-btn:active {
                transform: translateY(0px) scale(0.98) !important;
            }

            /* ===== INPUTS ===== */
            .q-field--standout .q-field__control {
                background: rgba(255,255,255,0.06) !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                transition: border-color 0.3s ease !important;
            }
            .q-field--standout .q-field__control:focus-within {
                border-color: #E50914 !important;
            }

            /* ===== HEADER / NAVBAR ===== */
            .q-header {
                background: linear-gradient(180deg, rgba(10,10,10,0.98) 0%, rgba(10,10,10,0.85) 100%) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
            }

            /* ===== SCROLLBAR ===== */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: #0a0a0a; }
            ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #E50914; }

            /* ===== TABS ===== */
            .q-tab { transition: color 0.3s ease !important; }
            .q-tab--active { color: #E50914 !important; }

            /* ===== NOTIFICATION ===== */
            .q-notification { border-radius: 12px !important; }

            /* ===== LOADING SHIMMER ===== */
            .shimmer {
                background: linear-gradient(90deg, #181818 25%, #252525 50%, #181818 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: 8px;
            }
        </style>
    ''')

def navbar():
    with ui.header().classes('justify-between items-center py-3 px-8').style('border-bottom: 1px solid rgba(255,255,255,0.06)'):
        # Logo routing: route to /admin if admin, otherwise to /
        with ui.row().classes('items-center gap-2 cursor-pointer').on('click', lambda: ui.navigate.to('/admin') if api_client.is_authenticated() and api_client.is_admin() else ui.navigate.to('/')):
            ui.icon('local_movies', color='primary').classes('text-3xl')
            ui.label('CINEMA PLUS').classes('text-2xl font-extrabold text-white tracking-[0.25em]').style('letter-spacing: 0.25em; background: linear-gradient(90deg, #E50914, #ff6b6b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;')
        
        with ui.row().classes('items-center gap-1'):
            if not (api_client.is_authenticated() and api_client.is_admin()):
                ui.link('Movies', '/').classes('text-white hover:text-primary transition-colors no-underline text-sm font-medium px-4 py-2 rounded-lg hover:bg-white/5')
            
            if api_client.is_authenticated():
                if api_client.is_admin():
                    ui.link('Dashboard', '/admin').classes('text-white hover:text-primary transition-colors no-underline text-sm font-medium px-4 py-2 rounded-lg hover:bg-white/5')
                else:
                    ui.link('My Bookings', '/bookings').classes('text-white hover:text-primary transition-colors no-underline text-sm font-medium px-4 py-2 rounded-lg hover:bg-white/5')
                
                ui.separator().props('vertical').classes('mx-2 h-6 opacity-20')
                
                with ui.button(icon='account_circle', color='transparent').classes('text-white'):
                    with ui.menu():
                        if not api_client.is_admin():
                            ui.menu_item('My Profile', on_click=lambda: ui.navigate.to('/profile'))
                        ui.menu_item('Logout', on_click=lambda: logout())
            else:
                ui.button('Login', color='primary', on_click=lambda: ui.navigate.to('/login')).classes('px-6 py-1 rounded-full font-bold text-sm')

def logout():
    api_client.clear_token()
    ui.navigate.to('/')
    ui.notify('Logged out successfully', type='info')
