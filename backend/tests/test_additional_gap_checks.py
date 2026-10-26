import pytest
from app.seed import seed_demo_data
from tests.support import bearer


def test_disaster_creation_rejects_out_of_bounds_coordinates(client, auth_headers):
    # Latitude > 90
    response = client.post(
        "/api/v1/disasters",
        json={
            "title": "Invalid Coordinate Disaster",
            "disaster_type": "flood",
            "description": "Flooding on river bank",
            "address": "Marina Beach",
            "severity_hint": "critical",
            "latitude": 95.5,
            "longitude": 80.25,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "latitude is outside valid bounds" in response.get_json()["error"]

    # Longitude > 180
    response = client.post(
        "/api/v1/disasters",
        json={
            "title": "Invalid Coordinate Disaster",
            "disaster_type": "flood",
            "description": "Flooding on river bank",
            "address": "Marina Beach",
            "severity_hint": "critical",
            "latitude": 13.08,
            "longitude": 185.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "longitude is outside valid bounds" in response.get_json()["error"]


def test_shelter_capacity_rejects_negative_values(client, auth_headers):
    response = client.post(
        "/api/v1/facilities/shelters",
        json={
            "name": "Negative Shelter",
            "latitude": 13.08,
            "longitude": 80.25,
            "capacity": -10,
            "current_occupancy": 0,
        },
        headers=auth_headers,
    )
    assert response.status_code in (400, 404)


def test_hospital_capacity_rejects_negative_icu_beds(client, auth_headers):
    response = client.post(
        "/api/v1/facilities/hospitals",
        json={
            "name": "Invalid ICU Hospital",
            "latitude": 13.08,
            "longitude": 80.25,
            "available_beds": 50,
            "icu_available": -5,
        },
        headers=auth_headers,
    )
    assert response.status_code in (400, 404)


def test_sql_injection_payload_in_disaster_title_is_safely_escaped(client, auth_headers):
    sqli_title = "Flood ' OR '1'='1'; DROP TABLE disasters; --"
    response = client.post(
        "/api/v1/disasters",
        json={
            "title": sqli_title,
            "disaster_type": "flood",
            "description": "Safety parameter test",
            "address": "Safe Harbor",
            "severity_hint": "medium",
            "latitude": 13.08,
            "longitude": 80.25,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    created_id = response.get_json()["disaster"]["id"]

    # Verify table is intact and record was retrieved cleanly without executing SQLi
    retrieved = client.get(f"/api/v1/disasters/{created_id}", headers=auth_headers)
    assert retrieved.status_code == 200
    assert retrieved.get_json()["disaster"]["title"] == sqli_title


def test_unauthenticated_requests_to_operational_endpoints_rejected(client):
    endpoints = [
        ("POST", "/api/v1/disasters"),
        ("POST", "/api/v1/admin/users"),
        ("POST", "/api/v1/road-closures"),
        ("POST", "/api/v1/readiness-checks"),
    ]
    for method, endpoint in endpoints:
        resp = client.open(endpoint, method=method, json={})
        assert resp.status_code in (401, 403), f"{endpoint} did not enforce auth"


def test_citizen_cannot_provision_admin_accounts(client, app):
    with app.app_context():
        seed_demo_data()
    citizen_headers = bearer(client, "Citizen")

    # Attempt to provision an Admin
    res = client.post(
        "/api/v1/admin/users",
        json={
            "email": "hacker_admin@example.invalid",
            "name": "Privilege Escalation",
            "role": "Admin",
            "temporary_password": "TempPassword123!",
        },
        headers=citizen_headers,
    )
    assert res.status_code == 403
