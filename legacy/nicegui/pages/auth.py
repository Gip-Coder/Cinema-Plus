from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar

@ui.page('/login')
def login_page():
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full items-center justify-center min-h-[80vh]'):
        with ui.card().classes('glass-card w-full max-w-sm p-10').style('animation: fadeInUp 0.5s ease both'):
            with ui.column().classes('items-center mb-8 gap-2'):
                ui.icon('local_movies', color='primary').classes('text-5xl')
                ui.label('Welcome Back').classes('text-3xl font-extrabold text-white')
                ui.label('Sign in to your account').classes('text-sm text-gray-500')
            
            username = ui.input('Username').props('dark standout rounded dense').classes('w-full mb-3')
            password = ui.input('Password').props('type=password dark standout rounded dense').classes('w-full mb-6')
            
            async def do_login():
                if not username.value or not password.value:
                    ui.notify('Please fill all fields', type='warning')
                    return
                
                success = await api_client.login(username.value, password.value)
                if success:
                    ui.notify('Login successful!', type='positive')
                    ui.navigate.to('/')
                else:
                    ui.notify('Invalid credentials', type='negative')
            
            ui.button('Sign In', color='primary', on_click=do_login).classes('w-full py-3 rounded-lg font-bold text-lg mb-4')
            
            with ui.row().classes('w-full justify-center mt-2'):
                ui.label("Don't have an account?").classes('text-gray-500 text-sm')
                ui.link('Sign up', '/register').classes('text-primary ml-2 no-underline hover:underline text-sm font-bold')

@ui.page('/register')
def register_page():
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full items-center justify-center min-h-[80vh]'):
        with ui.card().classes('glass-card w-full max-w-sm p-10').style('animation: fadeInUp 0.5s ease both'):
            with ui.column().classes('items-center mb-8 gap-2'):
                ui.icon('person_add', color='primary').classes('text-5xl')
                ui.label('Create Account').classes('text-3xl font-extrabold text-white')
                ui.label('Join Cinema Plus today').classes('text-sm text-gray-500')
            
            username = ui.input('Username').props('dark standout rounded dense').classes('w-full mb-3')
            email = ui.input('Email').props('dark standout rounded dense').classes('w-full mb-3')
            password = ui.input('Password').props('type=password dark standout rounded dense').classes('w-full mb-6')
            
            async def do_register():
                if not username.value or not email.value or not password.value:
                    ui.notify('Please fill all fields', type='warning')
                    return
                    
                success = await api_client.register(username.value, email.value, password.value)
                if success:
                    ui.notify('Registration successful! Please login.', type='positive')
                    ui.navigate.to('/login')
                else:
                    ui.notify('Registration failed. Username or email may already exist.', type='negative')
            
            ui.button('Sign Up', color='primary', on_click=do_register).classes('w-full py-3 rounded-lg font-bold text-lg mb-4')
            
            with ui.row().classes('w-full justify-center mt-2'):
                ui.label("Already have an account?").classes('text-gray-500 text-sm')
                ui.link('Sign in', '/login').classes('text-primary ml-2 no-underline hover:underline text-sm font-bold')
