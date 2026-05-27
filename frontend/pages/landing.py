from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar

@ui.page('/')
async def landing_page():
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full p-8 max-w-7xl mx-auto'):
        # Hero heading
        with ui.row().classes('w-full justify-between items-end mb-10'):
            with ui.column().classes('gap-1'):
                ui.label('NOW SHOWING').classes('text-5xl font-extrabold text-white tracking-tight').style('background: linear-gradient(90deg, #fff, #ccc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;')
                ui.html('<div style="width:60px; height:4px; background: linear-gradient(90deg, #E50914, transparent); border-radius:2px; margin-top:4px;"></div>', sanitize=False)
            
            with ui.row().classes('gap-3 items-center'):
                search_input = ui.input('Search movies...', on_change=lambda: refresh_movies()).props('dark standout rounded dense').classes('w-56')
                genre_filter = ui.select(['All Genres', 'Action', 'Drama', 'Comedy', 'Sci-Fi', 'Horror', 'Thriller'], value='All Genres', on_change=lambda: refresh_movies()).props('dark standout rounded dense').classes('w-44')

        movie_container = ui.row().classes('w-full gap-6 justify-start flex-wrap')
        
        async def refresh_movies():
            movie_container.clear()
            q = search_input.value if search_input.value else None
            genre = genre_filter.value if genre_filter.value != 'All Genres' else None
            
            try:
                movies = await api_client.search_movies(q=q, genre=genre)
            except Exception as e:
                with movie_container:
                    ui.label(f'Could not connect to backend. Please ensure the server is running.').classes('text-xl text-red-400 mt-8')
                return
            
            if not movies:
                with movie_container:
                    ui.label('No movies found matching your search.').classes('text-xl text-gray-400 mt-8')
                return
                
            with movie_container:
                for movie in movies:
                    with ui.card().classes('movie-card w-64 cursor-pointer relative overflow-hidden h-[500px]').on('click', lambda m=movie: ui.navigate.to(f'/movie/{m["id"]}')):
                        poster_url = movie.get("poster_url", "")
                        if poster_url:
                            if poster_url.startswith('/'):
                                import os
                                base = os.getenv("API_BASE_URL", "http://localhost:8000").replace("/api", "")
                                if base.endswith("/"): base = base[:-1]
                                poster_url = f"{base}{poster_url}"
                            ui.image(poster_url).classes('w-full h-full object-cover')
                        else:
                            ui.image('https://via.placeholder.com/300x450.png?text=No+Poster').classes('w-full h-full object-cover')
                        
                        with ui.column().classes('p-4 w-full bg-gradient-to-t from-black via-black/80 to-transparent absolute bottom-0 left-0 right-0'):
                            ui.label(movie["title"]).classes('text-xl font-bold text-white truncate w-full')
                            ui.label(f'{movie["genre"]} • {movie["language"]}').classes('text-sm text-gray-300')
                            with ui.row().classes('w-full justify-between items-center mt-2'):
                                ui.label(f'{movie["duration"]} min').classes('text-xs text-gray-400')
                                if movie.get("rating"):
                                    with ui.row().classes('items-center gap-1'):
                                        ui.icon('star', color='warning').classes('text-sm')
                                        ui.label(str(movie["rating"])).classes('text-sm font-bold text-white')

        # Initial Load via timer to prevent blocking page render
        ui.timer(0.1, refresh_movies, once=True)
