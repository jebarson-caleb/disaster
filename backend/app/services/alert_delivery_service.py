import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from flask import current_app


class AlertDeliveryError(RuntimeError):
    """A sanitized outbound-delivery failure safe to record in an audit event."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def alert_delivery_available():
    """Return whether the signed outbound warning webhook is fully configured."""
    config = current_app.config
    return bool(
        config.get("ALERT_DELIVERY_WEBHOOK_URL")
        and config.get("ALERT_DELIVERY_WEBHOOK_SECRET")
    )


def deliver_alert(alert):
    """Deliver a minimal CAP-inspired payload to an approved provider webhook."""
    if not alert_delivery_available():
        return {"status": "not_configured", "provider": "in_app"}

    config = current_app.config
    webhook_url = config["ALERT_DELIVERY_WEBHOOK_URL"]
    parsed_webhook_url = urlsplit(webhook_url)
    if (
        parsed_webhook_url.scheme != "https"
        or not parsed_webhook_url.hostname
        or parsed_webhook_url.username is not None
        or parsed_webhook_url.password is not None
        or parsed_webhook_url.query
        or parsed_webhook_url.fragment
    ):
        raise AlertDeliveryError("Provider configuration is invalid")

    payload = {
        "schema_version": "1.0",
        "idempotency_key": alert.identifier,
        "alert": {
            "identifier": alert.identifier,
            "event": alert.event,
            "audience": alert.audience,
            "channels": alert.channels,
            "urgency": alert.urgency,
            "severity": alert.severity,
            "certainty": alert.certainty,
            "message": alert.message,
            "instruction": alert.instruction,
            "created_at": alert.created_at.isoformat(),
            "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
        },
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(
        config["ALERT_DELIVERY_WEBHOOK_SECRET"].encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    outbound_request = Request(  # noqa: S310 - HTTPS-only URL is validated immediately above.
        webhook_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Idempotency-Key": alert.identifier,
            "User-Agent": "ResQ-Command/1.0",
            "X-ResQ-Signature": f"sha256={signature}",
        },
    )

    try:
        with urlopen(  # noqa: S310 - outbound_request is constructed from a validated HTTPS URL.
            outbound_request,
            timeout=config["ALERT_DELIVERY_TIMEOUT_SECONDS"],
        ) as response:
            status_code = int(response.status)
            response.read(1024)
    except HTTPError as error:
        raise AlertDeliveryError("Provider rejected the alert", error.code) from error
    except (TimeoutError, URLError, OSError, ValueError) as error:
        raise AlertDeliveryError("Provider could not be reached") from error

    if not 200 <= status_code < 300:
        raise AlertDeliveryError("Provider rejected the alert", status_code)
    return {
        "status": "delivered",
        "provider": "webhook",
        "status_code": status_code,
    }
