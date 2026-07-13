from app.extensions import db
from app.models import Disaster, Hospital, Shelter


def test_register_login_and_me(client):
    payload = {
        "name": "Citizen User",
        "email": "citizen@test.local",
        "phone": "9000000001",
        "role": "Citizen",
        "password": "password123",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    token = response.get_json()["token"]

    login = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.get_json()["user"]["role"] == "Citizen"


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
