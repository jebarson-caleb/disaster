"""Secret-safe integration readiness reporting for administrators."""

from datetime import UTC, datetime

from flask import current_app

from .email_service import password_recovery_available


def _integration(
    identifier,
    name,
    configured,
    active_mode,
    fallback_mode,
    activation_variables=None,
    *,
    required_for_core=False,
):
    return {
        "id": identifier,
        "name": name,
        "configured": bool(configured),
        "status": "active" if configured else "fallback",
        "mode": active_mode if configured else fallback_mode,
        "fallback": fallback_mode,
        "activation_variables": list(activation_variables or []),
        "required_for_core": required_for_core,
    }


def integration_readiness():
    """Describe integration modes without exposing endpoints, accounts, or secrets."""
    config = current_app.config
    database_uri = str(config.get("SQLALCHEMY_DATABASE_URI") or "")
    production_database = database_uri.startswith(("postgresql+psycopg://", "mysql+pymysql://"))
    development_database = config.get("APP_ENV") != "production" and database_uri.startswith("sqlite")
    database_configured = production_database or development_database
    rate_limit_storage = str(config.get("RATELIMIT_STORAGE_URI") or "")

    integrations = [
        _integration(
            "persistent_database",
            "Persistent operational database",
            database_configured,
            "Managed PostgreSQL/MySQL storage",
            "No safe production fallback",
            ["DATABASE_URL"],
            required_for_core=True,
        ),
        _integration(
            "public_alert_delivery",
            "External public-warning delivery",
            config.get("ALERT_DELIVERY_WEBHOOK_URL") and config.get("ALERT_DELIVERY_WEBHOOK_SECRET"),
            "Signed HTTPS alert gateway",
            "In-app warnings and acknowledgements only",
            ["ALERT_DELIVERY_WEBHOOK_URL", "ALERT_DELIVERY_WEBHOOK_SECRET"],
        ),
        _integration(
            "email_recovery",
            "Email password recovery",
            password_recovery_available(),
            "Standard SMTP single-use recovery links",
            "Administrator-assisted reset after identity verification",
            ["PUBLIC_BASE_URL", "SMTP_HOST", "SMTP_FROM_EMAIL"],
        ),
        _integration(
            "online_donations",
            "Hosted donation checkout",
            config.get("DONATION_PAYMENT_URL"),
            "Approved hosted payment checkout",
            "Auditable pledges only; no money represented as collected",
            ["DONATION_PAYMENT_URL"],
        ),
        _integration(
            "shared_throttling",
            "Shared request throttling",
            rate_limit_storage.startswith("rediss://"),
            "TLS Redis shared throttling",
            "Per-instance throttling plus database-backed account lockout",
            ["RATELIMIT_STORAGE_URI"],
        ),
        _integration(
            "ai_explanations",
            "Private AI explanations",
            config.get("OLLAMA_BASE_URL"),
            "Privacy-approved Ollama service",
            "Deterministic local scoring without personal-data transmission",
            ["OLLAMA_BASE_URL", "OLLAMA_MODEL"],
        ),
        _integration(
            "maps",
            "Maps and destination guidance",
            True,
            "OpenStreetMap browser tiles with typed-coordinate fallback",
            "Typed coordinates and addresses",
        ),
    ]
    active_count = sum(item["status"] == "active" for item in integrations)
    fallback_count = len(integrations) - active_count
    external_integrations = [item for item in integrations if not item["required_for_core"] and item["id"] != "maps"]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            "active": active_count,
            "fallback": fallback_count,
            "total": len(integrations),
            "external_activation_complete": all(item["configured"] for item in external_integrations),
        },
        "integrations": integrations,
    }
