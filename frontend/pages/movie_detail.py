from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar

@ui.page('/movie/{movie_id}')
async def movie_detail_page(movie_id: int):
    apply_theme()
    navbar()
    
    movie = await api_client.get_movie(movie_id)
    if not movie:
        with ui.column().classes('w-full items-center mt-20'):
            ui.label('Movie not found').classes('text-2xl text-red-500')
            ui.button('Back to Home', on_click=lambda: ui.navigate.to('/')).classes('mt-4')
        return

    with ui.row().classes('w-full p-8 max-w-6xl mx-auto mt-4 gap-10').style('animation: fadeInUp 0.4s ease both'):
        # Poster Column
        with ui.column().classes('w-1/3'):
            poster_url = movie.get("poster_url", "")
            if poster_url:
                if poster_url.startswith('/'):
                    import os
                    base = os.getenv("API_BASE_URL", "http://localhost:8001")
                    if base.endswith("/"): base = base[:-1]
                    poster_url = f"{base}{poster_url}"
                ui.image(poster_url).classes('w-full rounded-2xl shadow-2xl').style('border: 1px solid rgba(255,255,255,0.06)')
            else:
                ui.image('https://via.placeholder.com/400x600.png?text=No+Poster').classes('w-full rounded-2xl shadow-2xl')
                
        # Details Column
        with ui.column().classes('w-2/3'):
            ui.label(movie["title"]).classes('text-5xl font-extrabold text-white mb-3 leading-tight')
            
            # Metadata pills
            with ui.row().classes('gap-2 mb-6 flex-wrap'):
                for pill in [movie["release_date"], f'{movie["duration"]} min', movie["genre"], movie["language"], movie["format"]]:
                    if pill:
                        ui.label(pill).classes('text-xs font-medium text-gray-300 px-3 py-1 rounded-full').style('background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08)')
                
            if movie.get("rating"):
                with ui.row().classes('items-center gap-2 mb-6'):
                    ui.icon('star', color='warning').classes('text-3xl')
                    ui.label(f'{movie["rating"]}').classes('text-3xl font-extrabold text-white')
                    ui.label('/10').classes('text-lg text-gray-500 font-medium')

            ui.label('Synopsis').classes('text-lg font-bold text-gray-400 uppercase tracking-wider mb-2')
            ui.label(movie.get("description", "No description available.")).classes('text-gray-300 text-base leading-relaxed mb-8')
            
            ui.html('<div style="width:100%; height:1px; background: linear-gradient(90deg, rgba(229,9,20,0.3), transparent); margin: 8px 0 24px;"></div>', sanitize=False)
            
            ui.label('Available Shows').classes('text-lg font-bold text-gray-400 uppercase tracking-wider mb-4')
            
            shows = await api_client.get_shows_by_movie(movie_id)
            if not shows:
                ui.label('No shows scheduled currently.').classes('text-gray-500 italic')
            else:
                with ui.row().classes('gap-3 w-full flex-wrap'):
                    for show in shows:
                        def book_show(s=show):
                            if api_client.is_authenticated():
                                ui.navigate.to(f'/book/{s["id"]}')
                            else:
                                ui.notify('Please login to book tickets', type='warning')
                                ui.navigate.to('/login')
                                
                        with ui.card().classes('glass-card p-4 items-center justify-center cursor-pointer min-w-[120px]').on('click', book_show):
                            ui.label(show['date']).classes('text-xs text-gray-500 font-semibold')
                            ui.label(show['start_time']).classes('text-2xl font-extrabold text-primary mt-1')
                            ui.label(f"Screen {show['screen_id']}").classes('text-[10px] text-gray-600 mt-2 uppercase tracking-wider')

    # Reviews Section
    with ui.column().classes('w-full p-8 max-w-6xl mx-auto mt-12'):
        ui.html('<div style="width:100%; height:1px; background: linear-gradient(90deg, transparent, rgba(229,9,20,0.3), transparent); margin-bottom: 32px;"></div>', sanitize=False)
        ui.label('Reviews & Ratings').classes('text-2xl font-extrabold text-white mb-8')
        
        # Add Review Form
        if api_client.is_authenticated():
            with ui.card().classes('glass-card w-full p-6 mb-10').style('animation: fadeIn 0.5s ease both'):
                with ui.row().classes('items-center gap-2 mb-4'):
                    ui.icon('rate_review', color='primary').classes('text-xl')
                    ui.label('Write a Review').classes('text-lg font-bold text-white')
                rating_input = ui.slider(min=1, max=5, value=5).classes('w-full max-w-xs')
                ui.label().bind_text_from(rating_input, 'value', backward=lambda v: '⭐' * int(v) + '☆' * (5 - int(v))).classes('text-2xl')
                
                comment_input = ui.textarea('Share your thoughts...').props('dark standout rounded').classes('w-full mt-4')
                
                async def post_review():
                    if not comment_input.value:
                        ui.notify('Please write a comment', type='warning')
                        return
                    payload = {
                        "movie_id": movie_id,
                        "rating": rating_input.value,
                        "comment": comment_input.value
                    }
                    if await api_client.create_review(payload):
                        ui.notify('Review posted!', type='positive')
                        comment_input.value = ''
                        ui.navigate.to(f'/movie/{movie_id}')
                    else:
                        ui.notify('Failed to post review', type='negative')
                
                ui.button('POST REVIEW', icon='send', color='primary', on_click=post_review).classes('mt-4 px-8 py-2 font-bold rounded-lg')
        else:
            with ui.row().classes('items-center gap-2 mb-8 p-4 rounded-lg').style('background: rgba(229,9,20,0.08); border: 1px solid rgba(229,9,20,0.15)'):
                ui.icon('info', color='primary')
                ui.link('Sign in to post a review', '/login').classes('text-primary no-underline font-medium')

        # List Reviews
        reviews = await api_client.get_movie_reviews(movie_id)
        if not reviews:
            ui.label('No reviews yet. Be the first to review!').classes('text-gray-500 italic')
        else:
            for review in reviews:
                with ui.card().classes('glass-card w-full p-6 mb-3'):
                    with ui.row().classes('w-full justify-between items-start'):
                        with ui.column():
                            with ui.row().classes('items-center gap-2 mb-1'):
                                ui.icon('account_circle', color='gray').classes('text-2xl')
                                ui.label(review.get('user', {}).get('username', 'Anonymous')).classes('text-base font-bold text-white')
                            
                            with ui.row().classes('items-center gap-0 mb-3'):
                                for i in range(5):
                                    color = 'yellow' if i < review['rating'] else 'grey'
                                    ui.icon('star', color=color).classes('text-sm')
                        
                        ui.label(review['created_at'][:10]).classes('text-[10px] text-gray-600 font-medium')
                    
                    ui.label(review['comment']).classes('text-gray-300 leading-relaxed text-sm')

