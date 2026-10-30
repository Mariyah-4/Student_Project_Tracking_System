import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'spts.db'}")
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql+psycopg://", 1)
    elif SQLALCHEMY_DATABASE_URI.startswith("postgresql://") and "+psycopg" not in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "txt", "csv", "zip", "png", "jpg", "jpeg"}

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
