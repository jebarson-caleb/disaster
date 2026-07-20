import os

from dotenv import load_dotenv

load_dotenv()


def database_url():
    configured_url = os.getenv("DATABASE_URL", "").strip()
    if configured_url.startswith("postgres://"):
        return configured_url.replace("postgres://", "postgresql+psycopg://", 1)
    if configured_url.startswith("postgresql://"):
        return configured_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if configured_url:
        return configured_url
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/disaster_response.db"
    return "sqlite:///disaster_dev.db"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("VERCEL_GIT_COMMIT_SHA") or "dev-secret"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
    DEMO_MODE = os.getenv("DEMO_MODE", "true" if os.getenv("VERCEL") else "false").lower() in {"1", "true", "yes"}
    EMERGENCY_HOTLINE = os.getenv("EMERGENCY_HOTLINE", "112")
    DONATION_PAYMENT_URL = os.getenv("DONATION_PAYMENT_URL", "").rstrip("/")
