import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # MySQL Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "admin")
    DB_NAME: str = os.getenv("DB_NAME", "MovieTicketBooking")

    # JWT Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey12345")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Backend / API Settings
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")
    
    # Upload Storage Settings
    UPLOAD_DIR: str = "uploads"
    MEDIA_DIR: str = os.path.join(UPLOAD_DIR, "media")

    # Reservation Settings
    RESERVATION_TIMEOUT_MINUTES: int = int(os.getenv("RESERVATION_TIMEOUT_MINUTES", "10"))

settings = Settings()
