import os
import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

def generate_ticket_pdf(booking, user, movie, show=None):
    # Generates a PDF byte string for the booking
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Cinema Theme
    c.setFillColor(colors.black)
    c.rect(0, 0, width, height, fill=1)
    
    c.setFillColor(colors.red)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(50, height - 80, "CINEMA PLUS TICKETS")
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 16)
    
    y = height - 150
    c.drawString(50, y, f"Booking ID: #{booking.id}")
    y -= 30
    c.drawString(50, y, f"Customer: {user.username}")
    y -= 30
    c.drawString(50, y, f"Movie: {movie.title}")
    y -= 30
    c.drawString(50, y, f"Format: {movie.format} ({movie.language})")
    
    if show:
        y -= 40
        c.setFillColor(colors.lightgrey)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, y, "SHOW DETAILS")
        y -= 25
        c.setFont("Helvetica", 16)
        c.setFillColor(colors.white)
        c.drawString(50, y, f"Date: {show.date}")
        y -= 25
        c.drawString(50, y, f"Time: {show.start_time} - {show.end_time}")
        y -= 25
        if show.screen:
            screen_name = show.screen.name
            theatre_name = show.screen.theatre.name if show.screen.theatre else "Main Theatre"
            c.drawString(50, y, f"Location: {theatre_name} - {screen_name}")
    else:
        y -= 30
        c.drawString(50, y, f"Booking Date: {booking.booking_date.strftime('%Y-%m-%d %H:%M')}")
    
    y -= 40
    c.setFillColor(colors.yellow)
    c.setFont("Helvetica-Bold", 18)
    seat_names = [seat.seat_name for seat in booking.booked_seats]
    c.drawString(50, y, f"Seats: {', '.join(seat_names)}")
    
    y -= 30
    c.drawString(50, y, f"Total Amount: Rs. {booking.total_amount}")
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr_data = f"Booking:{booking.id}|User:{user.username}|Movie:{movie.title}|Show:{show.date if show else 'N/A'}|Seats:{','.join(seat_names)}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to a temporary file or buffer
    qr_buffer = io.BytesIO()
    img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    # Draw QR on PDF using reportlab ImageReader
    from reportlab.lib.utils import ImageReader
    qr_image = ImageReader(qr_buffer)
    c.drawImage(qr_image, width - 250, height - 300, width=200, height=200)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
