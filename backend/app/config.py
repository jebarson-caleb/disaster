import os
import re
from urllib.parse import urlsplit

from dotenv import load_dotenv

from .release import APPLICATION_VERSION, release_commit

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


def cors_origins():
    environment = os.getenv("APP_ENV", "production" if os.getenv("VERCEL") else "development").lower()
    default_origins = "" if environment == "production" else "http://localhost:5173"
    return [item.strip() for item in os.getenv("CORS_ORIGINS", default_origins).split(",") if item.strip()]


def public_base_url():
    configured_url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if configured_url:
        return configured_url.rstrip("/")
    vercel_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL", "").strip()
    if vercel_url:
        return f"https://{vercel_url}".rstrip("/")
    return "http://localhost:5173" if not os.getenv("VERCEL") else ""


class Config:
    APP_ENV = os.getenv("APP_ENV", "production" if os.getenv("VERCEL") else "development").lower()
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-change-before-production"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = cors_origins()
    CORS_SUPPORTS_CREDENTIALS = True
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
    AUTO_MIGRATE = os.getenv("AUTO_MIGRATE", "true").lower() in {"1", "true", "yes"}
    EMERGENCY_HOTLINE = os.getenv("EMERGENCY_HOTLINE", "112")
    ALERT_DELIVERY_WEBHOOK_URL = os.getenv("ALERT_DELIVERY_WEBHOOK_URL", "").strip()
    ALERT_DELIVERY_WEBHOOK_SECRET = os.getenv("ALERT_DELIVERY_WEBHOOK_SECRET", "")
    ALERT_DELIVERY_TIMEOUT_SECONDS = int(os.getenv("ALERT_DELIVERY_TIMEOUT_SECONDS", "5"))
    DONATION_PAYMENT_URL = os.getenv("DONATION_PAYMENT_URL", "").rstrip("/")
    PUBLIC_BASE_URL = public_base_url()
    PASSWORD_RESET_MINUTES = int(os.getenv("PASSWORD_RESET_MINUTES", "30"))
    SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() in {"1", "true", "yes"}
    SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", "8"))
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
    RELEASE_VERSION = APPLICATION_VERSION
    RELEASE_COMMIT = release_commit()
    RUNNING_ON_VERCEL = bool(os.getenv("VERCEL"))
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
    if not database_uri.startswith(("postgresql+psycopg://", "mysql+pymysql://")):
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
    origins = config.get("CORS_ORIGINS") or []
    if "*" in origins:
        issues.append("CORS_ORIGINS cannot contain * when credentials are enabled")
    if any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
        issues.append("CORS_ORIGINS cannot contain local development origins in production")
    if not config.get("SESSION_COOKIE_SECURE"):
        issues.append("COOKIE_SECURE must be true in production")
    if not config.get("BOOTSTRAP_ADMIN_EMAIL") or not config.get("BOOTSTRAP_ADMIN_PASSWORD"):
        issues.append("BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are required for first production access")
    elif len(config.get("BOOTSTRAP_ADMIN_PASSWORD", "")) < 15:
        issues.append("BOOTSTRAP_ADMIN_PASSWORD must contain at least 15 characters")
    release_commit_value = str(config.get("RELEASE_COMMIT") or "")
    if config.get("RUNNING_ON_VERCEL") and not re.fullmatch(r"[0-9a-f]{40}", release_commit_value):
        issues.append("A 40-character Vercel Git commit SHA is required for production release provenance")
    payment_url = str(config.get("DONATION_PAYMENT_URL") or "")
    if payment_url and not _is_secure_public_url(payment_url):
        issues.append("DONATION_PAYMENT_URL must be an absolute HTTPS URL without embedded credentials")
    alert_webhook_url = str(config.get("ALERT_DELIVERY_WEBHOOK_URL") or "")
    alert_webhook_secret = str(config.get("ALERT_DELIVERY_WEBHOOK_SECRET") or "")
    if bool(alert_webhook_url) != bool(alert_webhook_secret):
        issues.append("ALERT_DELIVERY_WEBHOOK_URL and ALERT_DELIVERY_WEBHOOK_SECRET must be supplied together")
    if alert_webhook_url:
        parsed_alert_webhook_url = urlsplit(alert_webhook_url)
        if (
            not _is_secure_public_url(alert_webhook_url)
            or parsed_alert_webhook_url.query
            or parsed_alert_webhook_url.fragment
        ):
            issues.append(
                "ALERT_DELIVERY_WEBHOOK_URL must be an absolute HTTPS URL without credentials, query, or fragment"
            )
        if len(alert_webhook_secret) < 32:
            issues.append("ALERT_DELIVERY_WEBHOOK_SECRET must contain at least 32 characters")
    if not 1 <= int(config.get("ALERT_DELIVERY_TIMEOUT_SECONDS") or 0) <= 15:
        issues.append("ALERT_DELIVERY_TIMEOUT_SECONDS must be between 1 and 15")
    ollama_url = str(config.get("OLLAMA_BASE_URL") or "")
    if ollama_url:
        parsed_ollama_url = urlsplit(ollama_url)
        if parsed_ollama_url.scheme not in {"http", "https"} or not parsed_ollama_url.hostname:
            issues.append("OLLAMA_BASE_URL must be an absolute HTTP(S) URL")
    rate_limit_storage = str(config.get("RATELIMIT_STORAGE_URI") or "")
    if rate_limit_storage not in {"", "memory://"} and not rate_limit_storage.startswith("rediss://"):
        issues.append("RATELIMIT_STORAGE_URI must use rediss:// in production")
    smtp_requested = any(
        str(config.get(name) or "")
        for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL")
    )
    if smtp_requested:
        if not config.get("SMTP_HOST") or not config.get("SMTP_FROM_EMAIL"):
            issues.append("SMTP_HOST and SMTP_FROM_EMAIL are required when email recovery is configured")
        elif not _is_valid_email_address(config.get("SMTP_FROM_EMAIL")):
            issues.append("SMTP_FROM_EMAIL must be a valid bare email address")
        if bool(config.get("SMTP_USERNAME")) != bool(config.get("SMTP_PASSWORD")):
            issues.append("SMTP_USERNAME and SMTP_PASSWORD must be supplied together")
        if config.get("SMTP_USE_TLS") and config.get("SMTP_USE_SSL"):
            issues.append("SMTP_USE_TLS and SMTP_USE_SSL cannot both be enabled")
        if not 1 <= int(config.get("SMTP_PORT") or 0) <= 65535:
            issues.append("SMTP_PORT must be between 1 and 65535")
        if not 1 <= int(config.get("SMTP_TIMEOUT_SECONDS") or 0) <= 60:
            issues.append("SMTP_TIMEOUT_SECONDS must be between 1 and 60")
        public_url = str(config.get("PUBLIC_BASE_URL") or "")
        parsed_public_url = urlsplit(public_url)
        if not _is_secure_public_url(public_url) or parsed_public_url.query or parsed_public_url.fragment:
            issues.append(
                "PUBLIC_BASE_URL must be an absolute HTTPS URL without credentials, query, or fragment "
                "when email recovery is configured"
            )
    if not 5 <= int(config.get("PASSWORD_RESET_MINUTES") or 0) <= 120:
        issues.append("PASSWORD_RESET_MINUTES must be between 5 and 120")
    return issues


def _is_secure_public_url(value):
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
    )


def _is_valid_email_address(value):
    email = str(value or "")
    if len(email) > 160 or any(character.isspace() for character in email):
        return False
    local, separator, domain = email.rpartition("@")
    return bool(separator and local and "." in domain and not domain.startswith(".") and not domain.endswith("."))
