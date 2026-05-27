import os
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("SMTP_USER", ""),
    MAIL_PASSWORD=os.getenv("SMTP_PASS", ""),
    MAIL_FROM=os.getenv("SMTP_FROM", "no-reply@cinemaplus.com"),
    MAIL_PORT=int(os.getenv("SMTP_PORT", 587)),
    MAIL_SERVER=os.getenv("SMTP_HOST", "smtp.gmail.com"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False") == "True",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_booking_confirmation(email: str, booking_id: int, movie_title: str, pdf_content: bytes):
    # Only send if SMTP is configured
    if not os.getenv("SMTP_USER") or not os.getenv("SMTP_PASS"):
        print(f"Skipping email to {email} - SMTP not configured")
        return False

    message = MessageSchema(
        subject=f"Booking Confirmed: {movie_title} (#{booking_id})",
        recipients=[email],
        body=f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #141414; color: #ffffff; padding: 20px;">
                <h1 style="color: #E50914;">Cinema Plus Confirmation</h1>
                <p>Hello,</p>
                <p>Your booking for <strong>{movie_title}</strong> has been successfully confirmed!</p>
                <p><strong>Booking ID:</strong> #{booking_id}</p>
                <p>Please find your E-Ticket attached to this email. You can also download it from your profile on our website.</p>
                <p>Enjoy your movie!</p>
                <hr style="border: 0; border-top: 1px solid #333;">
                <p style="font-size: 12px; color: #888;">This is an automated email, please do not reply.</p>
            </body>
        </html>
        """,
        subtype=MessageType.html,
        attachments=[
            {
                "file": pdf_content,
                "filename": f"Ticket_{booking_id}.pdf",
                "content_type": "application/pdf"
            }
        ]
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
