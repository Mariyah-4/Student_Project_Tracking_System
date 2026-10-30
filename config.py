import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

database_url = os.getenv("DATABASE_URL")

if database_url:
    # Render may provide postgres:// or postgresql:// URLs.
    # psycopg is the PostgreSQL driver installed by requirements.txt.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
else:
    # Local development fallback only. Set DATABASE_URL to PostgreSQL
    # in Render for the deployed application.
    database_url = f"sqlite:///{(INSTANCE_DIR / 'studysync.db').as_posix()}"


class Config:
    """Base configuration for the Student Project Tracking System."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-this-secret-key")

    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # Upload configuration
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", str(BASE_DIR / "uploads")
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit

    # Session cookie security. HTTPS is used on the deployed Render site.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"

    # Flask-WTF / CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
