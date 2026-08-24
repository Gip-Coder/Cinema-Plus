import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Known weak default secrets that must never be used in production
_KNOWN_WEAK_SECRETS = {
    "supersecretkey12345",
    "secret",
    "changeme",
    "your-secret-key-change-in-production",
    "your-secret-key",
    "",
}


def _require_env(name: str, default: str | None = None) -> str:
    """Return env var value or raise a clear error if missing in production."""
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(
            f"[CONFIG ERROR] Required environment variable '{name}' is not set. "
            "Check your .env file or deployment configuration."
        )
    return value


class Settings:
    # ── Application Environment ─────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # ── MySQL Database Settings ─────────────────────────────
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "MovieTicketBooking")

    # ── JWT Security Settings ───────────────────────────────
    _raw_secret: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # ── Admin Bootstrap ─────────────────────────────────────
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@cinemaplus.local")

    # ── CORS ────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # Example: "http://localhost:3005,https://your-domain.com"
    ALLOWED_ORIGINS_RAW: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3005")

    # ── Frontend / API Settings ─────────────────────────────
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3005")

    # ── Upload Storage Settings ─────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MEDIA_DIR: str = os.path.join("uploads", "media")

    # ── Reservation Settings ────────────────────────────────
    RESERVATION_TIMEOUT_MINUTES: int = int(os.getenv("RESERVATION_TIMEOUT_MINUTES", "10"))

    # ── OpenAPI Docs ────────────────────────────────────────
    # Set ENABLE_DOCS=true to expose /docs and /redoc in production.
    ENABLE_DOCS: bool = os.getenv("ENABLE_DOCS", "").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def SECRET_KEY(self) -> str:
        """Return the validated JWT secret key."""
        key = self._raw_secret
        if self.is_production:
            if not key or key in _KNOWN_WEAK_SECRETS or len(key) < 32:
                raise RuntimeError(
                    "[SECURITY ERROR] SECRET_KEY is missing, too short (< 32 chars), "
                    "or is a known-weak default value. "
                    "Set a cryptographically random SECRET_KEY before deploying to production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        elif not key:
            # Development fallback — warn but don't crash
            print(
                "[WARNING] SECRET_KEY is not set. Using an insecure default for development. "
                "Set SECRET_KEY in your .env file.",
                file=sys.stderr,
            )
            return "dev-only-insecure-key-do-not-use-in-production"
        return key

    @property
    def allowed_origins(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_RAW.split(",") if origin.strip()]

    def validate_production_config(self) -> None:
        """
        Call this at startup to ensure production has all required configuration.
        Raises RuntimeError with a clear message if anything is missing.
        """
        if not self.is_production:
            return

        errors: list[str] = []

        # Validate SECRET_KEY
        try:
            _ = self.SECRET_KEY
        except RuntimeError as e:
            errors.append(str(e))

        # Validate ADMIN_PASSWORD
        if not self.ADMIN_PASSWORD:
            errors.append(
                "[CONFIG ERROR] ADMIN_PASSWORD is not set. "
                "This is required in production so the initial admin account "
                "is not created with a hardcoded insecure password."
            )

        # Validate DB credentials
        if not self.DB_PASSWORD:
            errors.append(
                "[CONFIG ERROR] DB_PASSWORD is not set for production deployment."
            )

        # Validate CORS
        if "*" in self.allowed_origins:
            errors.append(
                "[SECURITY ERROR] ALLOWED_ORIGINS must not contain '*' in production. "
                "Set it to your actual frontend domain(s)."
            )

        if errors:
            raise RuntimeError(
                "Production configuration validation failed:\n\n" + "\n".join(errors)
            )


settings = Settings()
