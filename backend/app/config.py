import os
from datetime import timedelta


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///oracle_site.db")
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
    CORS_ORIGINS = _csv(os.getenv("CORS_ORIGINS", "http://localhost:3000"))

    SITE_NAME = os.getenv("SITE_NAME", "Oracle Site")
    SITE_URL = os.getenv("SITE_URL", "http://localhost:3000").rstrip("/")
    API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", "http://localhost:8000").rstrip("/")
    SITE_INDUSTRY = os.getenv("SITE_INDUSTRY", "education")
    SITE_AUDIENCE = os.getenv("SITE_AUDIENCE", "students and independent creators")
    SITE_REGION = os.getenv("SITE_REGION", "United States")

    # i18n — first locale is the default (base columns). Add "zh" for Chinese.
    SITE_LOCALES = _csv(os.getenv("SITE_LOCALES", "en,zh")) or ["en"]
    SITE_DEFAULT_LOCALE = os.getenv("SITE_DEFAULT_LOCALE", "") or SITE_LOCALES[0]

    # Self-hosted media (blog images, etc.), served at /api/media/<file> from a volume.
    # Upload-only (no generation): POST /api/admin/media stores user images here.
    MEDIA_DIR = os.getenv("MEDIA_DIR", "/app/media")
    MEDIA_MAX_MB = int(os.getenv("MEDIA_MAX_MB", "10"))
    # Caps request bodies (Flask 413s past this). Headroom over MEDIA_MAX_MB so a
    # full-size image still fits when sent base64-encoded (~33% larger) or multipart.
    MAX_CONTENT_LENGTH = (int(os.getenv("MEDIA_MAX_MB", "10")) * 4 // 3 + 2) * 1024 * 1024

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    ADMIN_EMAILS = set(_csv(os.getenv("ADMIN_EMAILS", "")))

    JWT_ISSUER = os.getenv("JWT_ISSUER", "oracle-site")
    JWT_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRES_HOURS", "168")))

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DAILY_BLOG_AUTOPUBLISH = os.getenv("DAILY_BLOG_AUTOPUBLISH", "true").lower() == "true"

    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
