from nicegui import ui
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar

@ui.page('/profile')
async def profile_page():
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    apply_theme()
    navbar()
    
    user = await api_client.get_me()
    if not user:
        ui.notify('Could not load user data', type='negative')
        return

    with ui.column().classes('w-full p-8 max-w-4xl mx-auto'):
        # Header
        with ui.row().classes('items-center gap-4 mb-10'):
            ui.icon('account_circle', color='primary').classes('text-6xl')
            with ui.column().classes('gap-0'):
                ui.label(user['username']).classes('text-4xl font-extrabold text-white')
                ui.label(user['email']).classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-6'):
            # Profile Info
            with ui.card().classes('glass-card flex-grow p-8').style('animation: fadeInUp 0.4s ease both'):
                with ui.row().classes('items-center gap-2 mb-6'):
                    ui.icon('edit', color='primary').classes('text-xl')
                    ui.label('Account Details').classes('text-xl font-bold text-white')
                
                username_input = ui.input('Username', value=user['username']).props('dark standout rounded dense').classes('w-full mb-4')
                email_input = ui.input('Email', value=user['email']).props('dark standout rounded dense').classes('w-full mb-6')
                
                async def save_profile():
                    if await api_client.update_profile(username=username_input.value, email=email_input.value):
                        ui.notify('Profile updated successfully', type='positive')
                    else:
                        ui.notify('Failed to update profile', type='negative')
                
                ui.button('Save Changes', color='primary', on_click=save_profile).classes('w-full py-3 font-bold rounded-lg')

            # Change Password
            with ui.card().classes('glass-card flex-grow p-8').style('animation: fadeInUp 0.5s ease both'):
                with ui.row().classes('items-center gap-2 mb-6'):
                    ui.icon('lock', color='primary').classes('text-xl')
                    ui.label('Security').classes('text-xl font-bold text-white')
                
                old_pwd = ui.input('Current Password', password=True).props('dark standout rounded dense').classes('w-full mb-4')
                new_pwd = ui.input('New Password', password=True).props('dark standout rounded dense').classes('w-full mb-4')
                confirm_pwd = ui.input('Confirm New Password', password=True).props('dark standout rounded dense').classes('w-full mb-6')
                
                async def update_pwd():
                    if new_pwd.value != confirm_pwd.value:
                        ui.notify('Passwords do not match', type='warning')
                        return
                    if await api_client.change_password(old_pwd.value, new_pwd.value):
                        ui.notify('Password changed successfully', type='positive')
                        old_pwd.value = ''
                        new_pwd.value = ''
                        confirm_pwd.value = ''
                    else:
                        ui.notify('Incorrect old password or update failed', type='negative')
                
                ui.button('Update Password', on_click=update_pwd).classes('w-full py-3 font-bold rounded-lg border border-primary text-primary')

        # Stats section
        with ui.row().classes('w-full mt-8 gap-4'):
            with ui.card().classes('glass-card p-6 flex-grow items-center').style('animation: fadeInUp 0.6s ease both'):
                ui.icon('verified_user', color='positive').classes('text-3xl mb-2')
                ui.label('Status').classes('text-gray-500 text-xs uppercase tracking-wider')
                ui.label('Active').classes('text-xl font-bold text-positive')
            
            with ui.card().classes('glass-card p-6 flex-grow items-center').style('animation: fadeInUp 0.65s ease both'):
                ui.icon('badge', color='primary').classes('text-3xl mb-2')
                ui.label('Role').classes('text-gray-500 text-xs uppercase tracking-wider')
                ui.label(user['role'].upper()).classes('text-xl font-bold text-primary')
