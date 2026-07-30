from app.seed import seed_demo_data


def role_headers(client, app, role):
    with app.app_context():
        seed_demo_data()
    session = client.post("/api/v1/auth/demo-session", json={"role": role})
    return {"Authorization": f"Bearer {session.get_json()['token']}"}


def by_id(response):
    return {item["id"]: item for item in response.get_json()["integrations"]}


def test_integration_readiness_is_admin_only(client, app):
    assert client.get("/api/v1/admin/integrations").status_code == 401
    citizen_headers = role_headers(client, app, "Citizen")
    assert client.get("/api/v1/admin/integrations", headers=citizen_headers).status_code == 403


def test_integration_readiness_reports_safe_fallbacks(client, app):
    admin_headers = role_headers(client, app, "Admin")
    response = client.get("/api/v1/admin/integrations", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    integrations = by_id(response)
    assert payload["summary"] == {
        "active": 2,
        "fallback": 5,
        "total": 7,
        "external_activation_complete": False,
    }
    assert integrations["persistent_database"]["status"] == "active"
    assert integrations["maps"]["status"] == "active"
    assert integrations["email_recovery"]["mode"].startswith("Administrator-assisted")
    assert integrations["public_alert_delivery"]["activation_variables"] == [
        "ALERT_DELIVERY_WEBHOOK_URL",
        "ALERT_DELIVERY_WEBHOOK_SECRET",
    ]
    serialized = response.get_data(as_text=True)
    assert "DemoPassword123!" not in serialized
    assert "test-secret-key" not in serialized


def test_integration_readiness_reports_configured_providers(client, app):
    app.config.update(
        ALERT_DELIVERY_WEBHOOK_URL="https://alerts.example/provider",
        ALERT_DELIVERY_WEBHOOK_SECRET="approved-provider-webhook-secret-32-bytes",
        DONATION_PAYMENT_URL="https://payments.example/checkout",
        OLLAMA_BASE_URL="https://private-ai.example",
        RATELIMIT_STORAGE_URI="rediss://redis.example/0",
        PUBLIC_BASE_URL="https://resq.example",
        SMTP_HOST="smtp.example",
        SMTP_FROM_EMAIL="security@resq.example",
        SMTP_USERNAME="mailer",
        SMTP_PASSWORD="private-mail-password",
        SMTP_USE_TLS=True,
        SMTP_USE_SSL=False,
    )
    admin_headers = role_headers(client, app, "Admin")
    response = client.get("/api/v1/admin/integrations", headers=admin_headers)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["summary"] == {
        "active": 7,
        "fallback": 0,
        "total": 7,
        "external_activation_complete": True,
    }
    assert all(item["status"] == "active" for item in payload["integrations"])
    serialized = response.get_data(as_text=True)
    assert "alerts.example" not in serialized
    assert "payments.example" not in serialized
    assert "private-ai.example" not in serialized
    assert "private-mail-password" not in serialized
