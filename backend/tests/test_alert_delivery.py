import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from urllib.error import URLError

from app.extensions import db
from app.models import AuditEvent, EmergencyAlert
from app.seed import seed_demo_data


def admin_headers(client, app):
    with app.app_context():
        seed_demo_data()
    session = client.post("/api/v1/auth/demo-session", json={"role": "Admin"})
    return {"Authorization": f"Bearer {session.get_json()['token']}"}


def alert_payload():
    return {
        "event": "Flash flood",
        "audience": "Ward 176",
        "channels": "SMS + radio",
        "message": "Water is rising.",
        "instruction": "Move to the designated school shelter.",
    }


def test_alert_delivery_falls_back_to_in_app_when_unconfigured(client, app):
    response = client.post(
        "/api/v1/alerts",
        headers=admin_headers(client, app),
        json=alert_payload(),
    )

    assert response.status_code == 201
    assert response.get_json()["delivery"] == {
        "status": "not_configured",
        "provider": "in_app",
    }
    assert response.get_json()["alert"]["delivery_status"] == "not_configured"
    assert response.get_json()["alert"]["delivery_attempts"] == 0
    snapshot = client.get(
        "/api/v1/operations/bootstrap",
        headers=admin_headers(client, app),
    ).get_json()
    tracked = next(
        item
        for item in snapshot["alerts"]
        if item["id"] == response.get_json()["alert"]["id"]
    )
    assert tracked["delivery_status"] == "not_configured"
    assert tracked["delivery_attempts"] == 0
    with app.app_context():
        event = db.session.execute(
            db.select(AuditEvent).where(AuditEvent.event_type == "alert_delivery")
        ).scalar_one()
        assert event.outcome == "skipped"


def test_alert_delivery_posts_signed_minimal_payload(client, app, monkeypatch):
    captured = {}

    class FakeResponse:
        status = 202

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit):
            captured["read_limit"] = limit
            return b'{"accepted":true}'

    def fake_urlopen(outbound_request, timeout):
        captured["body"] = outbound_request.data
        captured["headers"] = dict(outbound_request.header_items())
        captured["timeout"] = timeout
        captured["url"] = outbound_request.full_url
        return FakeResponse()

    secret = "approved-provider-webhook-secret-32-bytes"
    app.config.update(
        ALERT_DELIVERY_WEBHOOK_URL="https://alerts.example/provider",
        ALERT_DELIVERY_WEBHOOK_SECRET=secret,
        ALERT_DELIVERY_TIMEOUT_SECONDS=4,
    )
    monkeypatch.setattr("app.services.alert_delivery_service.urlopen", fake_urlopen)

    response = client.post(
        "/api/v1/alerts",
        headers=admin_headers(client, app),
        json=alert_payload(),
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["delivery"] == {
        "status": "delivered",
        "provider": "webhook",
        "status_code": 202,
    }
    assert body["alert"]["delivery_status"] == "delivered"
    assert body["alert"]["delivery_attempts"] == 1
    assert body["alert"]["delivery_status_code"] == 202
    assert body["alert"]["delivery_attempted_at"]
    outbound = json.loads(captured["body"])
    assert captured["url"] == "https://alerts.example/provider"
    assert captured["timeout"] == 4
    assert captured["read_limit"] == 1024
    assert outbound["idempotency_key"] == body["alert"]["identifier"]
    assert outbound["alert"]["message"] == alert_payload()["message"]
    assert "sender_id" not in outbound["alert"]
    assert "user" not in outbound

    expected_signature = hmac.new(
        secret.encode(),
        captured["body"],
        hashlib.sha256,
    ).hexdigest()
    assert captured["headers"]["X-resq-signature"] == f"sha256={expected_signature}"
    assert captured["headers"]["Idempotency-key"] == body["alert"]["identifier"]

    with app.app_context():
        event = db.session.execute(
            db.select(AuditEvent).where(AuditEvent.event_type == "alert_delivery")
        ).scalar_one()
        assert event.outcome == "success"


def test_alert_remains_published_when_provider_delivery_fails(client, app, monkeypatch):
    app.config.update(
        ALERT_DELIVERY_WEBHOOK_URL="https://alerts.example/provider",
        ALERT_DELIVERY_WEBHOOK_SECRET="approved-provider-webhook-secret-32-bytes",
        ALERT_DELIVERY_TIMEOUT_SECONDS=4,
    )

    def fail_delivery(*_args, **_kwargs):
        raise URLError("provider unavailable")

    monkeypatch.setattr("app.services.alert_delivery_service.urlopen", fail_delivery)
    response = client.post(
        "/api/v1/alerts",
        headers=admin_headers(client, app),
        json=alert_payload(),
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["delivery"] == {
        "status": "failed",
        "provider": "webhook",
    }
    assert body["alert"]["delivery_status"] == "failed"
    assert body["alert"]["delivery_attempts"] == 1
    with app.app_context():
        event = db.session.execute(
            db.select(AuditEvent).where(AuditEvent.event_type == "alert_delivery")
        ).scalar_one()
        assert event.outcome == "failure"

    class RetryResponse:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return b""

    monkeypatch.setattr(
        "app.services.alert_delivery_service.urlopen",
        lambda *_args, **_kwargs: RetryResponse(),
    )
    retried = client.post(
        f"/api/v1/alerts/{body['alert']['id']}/deliver",
        headers=admin_headers(client, app),
        json={},
    )
    assert retried.status_code == 200
    assert retried.get_json()["delivery"]["status"] == "delivered"
    assert retried.get_json()["alert"]["delivery_status"] == "delivered"
    assert retried.get_json()["alert"]["delivery_attempts"] == 2

    with app.app_context():
        alert = db.session.get(EmergencyAlert, body["alert"]["id"])
        alert.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.session.commit()
    expired = client.post(
        f"/api/v1/alerts/{body['alert']['id']}/deliver",
        headers=admin_headers(client, app),
        json={},
    )
    assert expired.status_code == 409
    assert expired.get_json()["error"] == "Only active, unexpired alerts can be delivered"


def test_alert_delivery_rejects_oversized_or_invalid_cap_fields(client, app):
    headers = admin_headers(client, app)
    oversized = client.post(
        "/api/v1/alerts",
        headers=headers,
        json={**alert_payload(), "message": "x" * 2001},
    )
    assert oversized.status_code == 400
    assert "at most 2000" in oversized.get_json()["error"]

    invalid_cap = client.post(
        "/api/v1/alerts",
        headers=headers,
        json={**alert_payload(), "urgency": "whenever"},
    )
    assert invalid_cap.status_code == 400
    assert "urgency must be one of" in invalid_cap.get_json()["error"]

    invalid_expiry = client.post(
        "/api/v1/alerts",
        headers=headers,
        json={**alert_payload(), "expires_in_hours": []},
    )
    assert invalid_expiry.status_code == 400
    assert invalid_expiry.get_json()["error"] == "expires_in_hours must be an integer"
