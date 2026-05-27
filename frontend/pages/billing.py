from nicegui import ui
import base64
from frontend.services.api_client import api_client
from frontend.components.ui_components import apply_theme, navbar

@ui.page('/billing/{booking_id}')
async def billing_page(booking_id: int):
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full items-center p-8'):
        ui.label('Booking Successful!').classes('text-4xl font-bold text-positive mb-8')
        
        with ui.card().classes('glass-card p-8 w-full max-w-2xl'):
            ui.label('Ticket Summary').classes('text-2xl font-bold text-primary mb-4 border-b border-gray-700 pb-2')
            
            # Note: We'd ideally fetch the exact booking details here via API. 
            # We can download the ticket directly.
            
            ui.label(f'Booking ID: #{booking_id}').classes('text-xl text-white mb-6')
            
            async def download_ticket():
                try:
                    pdf_bytes = await api_client.download_ticket(booking_id)
                    if pdf_bytes:
                        # Convert to base64 for download
                        b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                        ui.download(f"data:application/pdf;base64,{b64}", f"ticket_{booking_id}.pdf")
                        ui.notify('Ticket downloaded', type='positive')
                    else:
                        ui.notify('Failed to download ticket', type='negative')
                except Exception as e:
                    ui.notify(f'Error: {str(e)}', type='negative')
                    
            ui.button('Download E-Ticket (PDF & QR)', icon='download', color='primary', on_click=download_ticket).classes('w-full py-4 text-lg font-bold rounded-lg mb-4')
            ui.button('Back to Home', color='secondary', on_click=lambda: ui.navigate.to('/')).classes('w-full py-2')
            
@ui.page('/bookings')
async def user_bookings_page():
    if not api_client.is_authenticated():
        ui.navigate.to('/login')
        return
        
    apply_theme()
    navbar()
    
    with ui.column().classes('w-full p-8 max-w-6xl mx-auto'):
        ui.label('My Bookings').classes('text-3xl font-bold text-white mb-8 border-l-4 border-primary pl-4')
        
        bookings = await api_client.get_user_bookings()
        if not bookings:
            ui.label("You haven't booked any movies yet.").classes('text-xl text-gray-400')
            return
            
        for booking in bookings:
            with ui.card().classes('glass-card w-full mb-6 p-6 flex-row items-center gap-8 relative overflow-hidden'):
                # Status Badge
                status = booking.get('status', 'confirmed')
                badge_color = 'positive' if status == 'confirmed' else 'negative'
                with ui.row().classes('absolute top-0 right-0 p-2'):
                    ui.label(status.upper()).classes(f'bg-{badge_color} text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg shadow-sm')

                # Poster
                poster_url = booking['movie'].get('poster_url', '')
                if poster_url:
                    if poster_url.startswith('/'):
                        import os
                        base = os.getenv("API_BASE_URL", "http://localhost:8000").replace("/api", "")
                        if base.endswith("/"): base = base[:-1]
                        poster_url = f"{base}{poster_url}"
                    ui.image(poster_url).classes('w-32 h-48 rounded-lg object-cover shadow-lg border border-gray-700')
                else:
                    ui.image('https://via.placeholder.com/300x450.png?text=No+Poster').classes('w-32 h-48 rounded-lg object-cover')
                
                with ui.column().classes('flex-grow'):
                    ui.label(booking['movie']['title']).classes('text-2xl font-bold text-white mb-1')
                    
                    if booking.get('show'):
                        s = booking['show']
                        ui.label(f"{s['date']} | {s['start_time']}").classes('text-lg text-primary font-bold')
                        if s.get('screen'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('location_on', size='xs', color='gray')
                                ui.label(f"Screen: {s['screen']['name']}").classes('text-sm text-gray-400')
                    
                    with ui.row().classes('items-center gap-2 mt-2'):
                        ui.icon('event_seat', size='xs', color='warning')
                        seats = [s['seat_name'] for s in booking['booked_seats']]
                        ui.label(f"Seats: {', '.join(seats)}").classes('text-lg text-yellow-500 font-semibold')
                    
                    from datetime import datetime
                    dt = datetime.fromisoformat(booking['booking_date'])
                    ui.label(f"Booked on {dt.strftime('%d %b %Y at %H:%M')}").classes('text-gray-500 text-xs mt-1')
                    
                    ui.label(f"Amount Paid: Rs. {booking['total_amount']}").classes('text-xl text-white font-bold mt-4')
                
                with ui.column().classes('items-end justify-between self-stretch'):
                    ui.label(f"ID #{booking['id']}").classes('text-gray-600 text-xs')
                    
                    async def download_cb(bid=booking['id']):
                        pdf_bytes = await api_client.download_ticket(bid)
                        if pdf_bytes:
                            import base64
                            b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                            ui.download(f"data:application/pdf;base64,{b64}", f"ticket_{bid}.pdf")
                        else:
                            ui.notify("Error downloading ticket", type='negative')
                            
                    ui.button('DOWNLOAD TICKET', icon='download', color='primary', on_click=download_cb).classes('px-8 py-2 rounded-lg font-bold shadow-lg')
