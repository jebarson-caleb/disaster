from app.extensions import db
from app.models import Hospital, Shelter
from app.seed import seed_demo_data


def test_register_login_and_me(client):
    payload = {
        "name": "Citizen User",
        "email": "citizen@test.local",
        "phone": "9000000001",
        "role": "Citizen",
        "password": "LongTestPassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    token = response.get_json()["token"]

    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.get_json()["user"]["role"] == "Citizen"

    protected_registration = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "self-admin@test.local", "role": "Admin"},
    )
    assert protected_registration.status_code == 403


def test_disaster_and_rescue_flow(client, auth_headers):
    disaster_response = client.post(
        "/api/v1/disasters",
        headers=auth_headers,
        json={
            "title": "Warehouse fire",
            "disaster_type": "fire",
            "description": "Smoke and flames reported near market road.",
            "address": "Market Road",
            "latitude": 10.1,
            "longitude": 76.2,
            "people_affected": 80,
            "severity_hint": "high",
        },
    )
    assert disaster_response.status_code == 201
    disaster = disaster_response.get_json()["disaster"]
    assert disaster_response.get_json()["damage_estimation"]["label"] in {"High", "Critical"}

    rescue_response = client.post(
        "/api/v1/rescue-requests",
        headers=auth_headers,
        json={
            "disaster_id": disaster["id"],
            "victim_name": "Maya",
            "victim_age": 8,
            "people_count": 3,
            "condition": "critical",
            "trapped": True,
            "vulnerable_people": 1,
            "latitude": 10.11,
            "longitude": 76.21,
        },
    )
    assert rescue_response.status_code == 201
    assert rescue_response.get_json()["priority"]["label"] == "Critical"

    request_id = rescue_response.get_json()["rescue_request"]["id"]
    assign = client.patch(
        f"/api/v1/rescue-requests/{request_id}/assign",
        headers=auth_headers,
        json={"assigned_unit": "Fire Rescue Team 2"},
    )
    assert assign.status_code == 200
    assert assign.get_json()["rescue_request"]["status"] == "assigned"


def test_facility_capacity_updates(client, app, auth_headers):
    with app.app_context():
        hospital = Hospital(
            name="Test Hospital",
            address="Main Road",
            latitude=1,
            longitude=2,
            total_beds=100,
            available_beds=20,
            icu_beds=5,
            emergency_capacity=10,
            contact_phone="123",
        )
        shelter = Shelter(
            name="Test Shelter",
            address="School",
            latitude=1,
            longitude=2,
            total_capacity=300,
            available_capacity=100,
            contact_phone="456",
        )
        db.session.add_all([hospital, shelter])
        db.session.commit()
        hospital_id = hospital.id
        shelter_id = shelter.id

    hospital_response = client.patch(
        f"/api/v1/hospitals/{hospital_id}/capacity",
        headers=auth_headers,
        json={"available_beds": 35, "icu_beds": 7, "emergency_capacity": 18},
    )
    assert hospital_response.status_code == 200
    assert hospital_response.get_json()["hospital"]["available_beds"] == 35

    shelter_response = client.patch(
        f"/api/v1/shelters/{shelter_id}/capacity",
        headers=auth_headers,
        json={"available_capacity": 180, "medical_support": True},
    )
    assert shelter_response.status_code == 200
    assert shelter_response.get_json()["shelter"]["available_capacity"] == 180


def test_ai_endpoints(client, auth_headers):
    damage = client.post(
        "/api/v1/ai/damage-estimation",
        headers=auth_headers,
        json={"disaster_type": "earthquake", "people_affected": 500, "severity_hint": "critical"},
    )
    assert damage.status_code == 200
    assert damage.get_json()["label"] == "Critical"

    allocation = client.post(
        "/api/v1/ai/allocate-resources",
        headers=auth_headers,
        json={"severity": "Critical", "people_count": 120, "disaster_type": "flood"},
    )
    assert allocation.status_code == 200
    assert allocation.get_json()["recommendations"]["rescue_teams"] >= 2


def test_admin_can_provision_operational_user(client, auth_headers):
    response = client.post(
        "/api/v1/admin/users",
        headers=auth_headers,
        json={
            "name": "Hospital Commander",
            "email": "commander@hospital.local",
            "phone": "9000000011",
            "role": "Hospital",
            "password": "SecureHospitalPass123!",
            "organization_name": "District Hospital",
            "facility": {
                "name": "District Hospital",
                "address": "Medical College Road",
                "latitude": 12.97,
                "longitude": 80.22,
                "contact_phone": "9000000011",
                "total_beds": 120,
                "available_beds": 40,
                "icu_beds": 12,
                "emergency_capacity": 25,
            },
        },
    )
    assert response.status_code == 201
    assert response.get_json()["user"]["role"] == "Hospital"
    assert response.get_json()["user"]["password_change_required"] is True
    assert response.get_json()["user"]["managed_facility"]["id"] == response.get_json()["facility"]["id"]
    assert "password_hash" not in response.get_json()["user"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "commander@hospital.local", "password": "SecureHospitalPass123!"},
    )
    assert login_response.status_code == 200
    assert login_response.get_json()["password_change_required"] is True
    blocked = client.get("/api/v1/operations/bootstrap")
    assert blocked.status_code == 403
    assert blocked.get_json()["code"] == "password_change_required"

    changed = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "SecureHospitalPass123!",
            "new_password": "PrivateHospitalPassword456!",
        },
        headers={"X-CSRF-Token": client.get_cookie("resq_csrf").value},
    )
    assert changed.status_code == 200
    assert changed.get_json()["user"]["password_change_required"] is False
    assert changed.get_json()["mfa_setup_required"] is True


def test_bootstrap_alert_acknowledgement_and_safe_route(client, app):
    with app.app_context():
        seed_demo_data()

    citizen_session = client.post("/api/v1/auth/demo-session", json={"role": "Citizen"})
    assert citizen_session.status_code == 200
    citizen_headers = {"Authorization": f"Bearer {citizen_session.get_json()['token']}"}

    snapshot = client.get("/api/v1/operations/bootstrap", headers=citizen_headers)
    assert snapshot.status_code == 200
    assert snapshot.get_json()["facilities"]["shelters"]
    assert snapshot.get_json()["rescue_requests"]

    forbidden = client.post(
        "/api/v1/alerts",
        headers=citizen_headers,
        json={"audience": "Ward 1", "channels": "SMS", "message": "Test", "instruction": "Evacuate"},
    )
    assert forbidden.status_code == 403

    admin_session = client.post("/api/v1/auth/demo-session", json={"role": "Admin"})
    admin_headers = {"Authorization": f"Bearer {admin_session.get_json()['token']}"}
    created = client.post(
        "/api/v1/alerts",
        headers=admin_headers,
        json={
            "event": "Flash flood",
            "audience": "Ward 176",
            "channels": "SMS + radio",
            "message": "Water is rising.",
            "instruction": "Move to the school shelter.",
        },
    )
    assert created.status_code == 201
    alert = created.get_json()["alert"]
    assert alert["identifier"].startswith("RESQ-")

    acknowledgement = client.post(
        f"/api/v1/alerts/{alert['id']}/acknowledge",
        headers=citizen_headers,
        json={"response": "received", "latitude": 12.98, "longitude": 80.22},
    )
    assert acknowledgement.status_code == 200
    assert acknowledgement.get_json()["acknowledgement"]["response"] == "received"
    assert acknowledgement.get_json()["created"] is True
    repeated_acknowledgement = client.post(
        f"/api/v1/alerts/{alert['id']}/acknowledge",
        headers=citizen_headers,
        json={"response": "received"},
    )
    assert repeated_acknowledgement.get_json()["created"] is False

    refreshed_snapshot = client.get("/api/v1/operations/bootstrap", headers=citizen_headers).get_json()
    refreshed_alert = next(item for item in refreshed_snapshot["alerts"] if item["id"] == alert["id"])
    assert refreshed_alert["acknowledged"] is True
    assert refreshed_alert["acknowledgement_count"] == 1

    route = client.get(
        "/api/v1/safe-route?latitude=12.9806&longitude=80.2194&destination=shelter",
        headers=citizen_headers,
    )
    assert route.status_code == 200
    assert route.get_json()["destination"]["available_capacity"] > 0
    assert route.get_json()["navigation_url"].startswith("https://www.google.com/maps/dir/")


def test_demo_session_can_be_disabled(client, app):
    app.config["DEMO_MODE"] = False
    response = client.post("/api/v1/auth/demo-session", json={"role": "Admin"})
    assert response.status_code == 404


def test_resource_distribution_and_volunteer_assignment_are_transactional(client, app):
    with app.app_context():
        seed_demo_data()

    admin_session = client.post("/api/v1/auth/demo-session", json={"role": "Admin"}).get_json()
    headers = {"Authorization": f"Bearer {admin_session['token']}"}
    coordination = client.get("/api/v1/coordination", headers=headers).get_json()
    resource = coordination["resources"][0]
    volunteer = next(item for item in coordination["volunteers"] if item["availability_status"] == "available")
    disaster_id = client.get("/api/v1/operations/bootstrap", headers=headers).get_json()["disasters"][0]["id"]

    distribution = client.post(
        "/api/v1/distributions",
        headers=headers,
        json={"resource_id": resource["id"], "disaster_id": disaster_id, "quantity": 10, "destination": "Relief Camp A"},
    )
    assert distribution.status_code == 201
    refreshed = client.get("/api/v1/coordination", headers=headers).get_json()
    refreshed_resource = next(item for item in refreshed["resources"] if item["id"] == resource["id"])
    assert refreshed_resource["available_quantity"] == resource["available_quantity"] - 10

    assignment = client.post(
        "/api/v1/volunteer-assignments",
        headers=headers,
        json={"volunteer_id": volunteer["id"], "disaster_id": disaster_id, "task": "Evacuation support"},
    )
    assert assignment.status_code == 201
    assert assignment.get_json()["volunteer"]["availability_status"] == "assigned"

    duplicate_assignment = client.post(
        "/api/v1/volunteer-assignments",
        headers=headers,
        json={"volunteer_id": volunteer["id"], "disaster_id": disaster_id, "task": "Second task"},
    )
    assert duplicate_assignment.status_code == 409
