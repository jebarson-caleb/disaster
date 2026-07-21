import base64
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
    APP_ENV = os.getenv("APP_ENV", "production" if os.getenv("VERCEL") else "development").lower()
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-change-before-production"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if item.strip()]
    CORS_SUPPORTS_CREDENTIALS = True
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "true").lower() in {"1", "true", "yes"}
    MFA_ENCRYPTION_KEY = os.getenv("MFA_ENCRYPTION_KEY", "")
    MFA_ISSUER = os.getenv("MFA_ISSUER", "ResQ Command")
    MFA_CHALLENGE_MINUTES = int(os.getenv("MFA_CHALLENGE_MINUTES", "5"))
    MFA_REQUIRED_ROLES = {
        item.strip()
        for item in os.getenv(
            "MFA_REQUIRED_ROLES",
            "Admin,Police,Fire Service,Hospital,Ambulance,Shelter,NGO",
        ).split(",")
        if item.strip()
    }
    EMERGENCY_HOTLINE = os.getenv("EMERGENCY_HOTLINE", "112")
    DONATION_PAYMENT_URL = os.getenv("DONATION_PAYMENT_URL", "").rstrip("/")
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "resq_session")
    CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "resq_csrf")
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true" if APP_ENV == "production" else "false").lower() in {"1", "true", "yes"}
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_IDLE_MINUTES = int(os.getenv("SESSION_IDLE_MINUTES", "30"))
    SESSION_ABSOLUTE_HOURS = int(os.getenv("SESSION_ABSOLUTE_HOURS", "12"))
    ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
    JWT_ISSUER = os.getenv("JWT_ISSUER", "resq-command-api")
    JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "resq-command-web")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(1024 * 1024)))
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() in {"1", "true", "yes"}
    TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "true" if os.getenv("VERCEL") else "false").lower() in {"1", "true", "yes"}
    BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    BOOTSTRAP_ADMIN_NAME = os.getenv("BOOTSTRAP_ADMIN_NAME", "Incident Commander")
    BOOTSTRAP_ADMIN_PHONE = os.getenv("BOOTSTRAP_ADMIN_PHONE", "")
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


def production_configuration_issues(config):
    issues = []
    if config.get("APP_ENV") != "production":
        return issues
    database_uri = str(config.get("SQLALCHEMY_DATABASE_URI") or "")
    if not database_uri or database_uri.startswith("sqlite"):
        issues.append("DATABASE_URL must point to persistent MySQL or PostgreSQL storage")
    for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = str(config.get(name) or "")
        if len(value) < 32 or value.startswith("dev-secret"):
            issues.append(f"{name} must be an independent random value of at least 32 characters")
    if config.get("SECRET_KEY") == config.get("JWT_SECRET_KEY"):
        issues.append("SECRET_KEY and JWT_SECRET_KEY must be different values")
    if config.get("DEMO_MODE"):
        issues.append("DEMO_MODE must be false in production")
    if not config.get("AUTO_MIGRATE"):
        issues.append("AUTO_MIGRATE must be true for one-click production deployment")
    mfa_key = str(config.get("MFA_ENCRYPTION_KEY") or "")
    try:
        decoded_mfa_key = base64.urlsafe_b64decode(mfa_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        decoded_mfa_key = b""
    if len(decoded_mfa_key) != 32:
        issues.append("MFA_ENCRYPTION_KEY must be a Fernet key containing 32 random bytes")
    if "Admin" not in set(config.get("MFA_REQUIRED_ROLES") or []):
        issues.append("MFA_REQUIRED_ROLES must include Admin")
    origins = config.get("CORS_ORIGINS") or []
    if "*" in origins:
        issues.append("CORS_ORIGINS cannot contain * when credentials are enabled")
    if not config.get("SESSION_COOKIE_SECURE"):
        issues.append("COOKIE_SECURE must be true in production")
    if not config.get("BOOTSTRAP_ADMIN_EMAIL") or not config.get("BOOTSTRAP_ADMIN_PASSWORD"):
        issues.append("BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are required for first production access")
    elif len(config.get("BOOTSTRAP_ADMIN_PASSWORD", "")) < 15:
        issues.append("BOOTSTRAP_ADMIN_PASSWORD must contain at least 15 characters")
    return issues
