import pytest

from app.models import RescueRequest
from app.seed import seed_demo_data
from tests.support import bearer


@pytest.fixture()
def seeded(app):
    with app.app_context():
        seed_demo_data()


def first_disaster_id(client, headers):
    return client.get("/api/v1/operations/bootstrap", headers=headers).get_json()["disasters"][0]["id"]


def test_incident_reports_reject_oversized_and_out_of_range_values(client, seeded):
    headers = bearer(client, "Citizen")
    base = {
        "title": "Road collapse",
        "disaster_type": "landslide",
        "description": "Retaining wall failed after rain.",
        "address": "Coonoor",
        "latitude": 11.35,
        "longitude": 76.79,
    }
    assert client.post("/api/v1/disasters", headers=headers, json={**base, "title": "x" * 161}).status_code == 400
    assert client.post("/api/v1/disasters", headers=headers, json={**base, "latitude": 95}).status_code == 400
    assert client.post("/api/v1/disasters", headers=headers, json={**base, "latitude": "nan"}).status_code == 400
    assert client.post("/api/v1/disasters", headers=headers, json={**base, "disaster_type": "<script>"}).status_code == 400
    assert client.post("/api/v1/disasters", headers=headers, json={**base, "people_affected": -4}).status_code == 400
    assert client.post("/api/v1/disasters", headers=headers, json=base).status_code == 201


def test_rescue_requests_reject_invalid_condition_and_coordinates(client, seeded):
    headers = bearer(client, "Citizen")
    disaster_id = first_disaster_id(client, headers)
    base = {"disaster_id": disaster_id, "victim_name": "Asha", "latitude": 12.98, "longitude": 80.22}
    assert client.post("/api/v1/rescue-requests", headers=headers, json={**base, "condition": "fine"}).status_code == 400
    assert client.post("/api/v1/rescue-requests", headers=headers, json={**base, "longitude": 181}).status_code == 400
    assert client.post("/api/v1/rescue-requests", headers=headers, json={**base, "people_count": 0}).status_code == 400


def test_assignment_bound_roles_cannot_cancel_or_reopen_rescues(client, app, seeded):
    admin = bearer(client, "Admin")
    disaster_id = first_disaster_id(client, admin)
    created = client.post(
        "/api/v1/rescue-requests",
        headers=admin,
        json={
            "disaster_id": disaster_id,
            "victim_name": "Volunteer scope check",
            "condition": "injured",
            "latitude": 12.9821,
            "longitude": 80.2219,
        },
    ).get_json()["rescue_request"]
    volunteer = bearer(client, "Volunteer")
    endpoint = f"/api/v1/rescue-requests/{created['id']}/status"
    assert client.patch(endpoint, headers=volunteer, json={"status": "cancelled"}).status_code == 403
    assert client.patch(endpoint, headers=volunteer, json={"status": "pending"}).status_code == 403
    assert client.patch(endpoint, headers=volunteer, json={"status": "en route"}).status_code == 200

    hospital = bearer(client, "Hospital")
    assert client.patch(endpoint, headers=hospital, json={"status": "cancelled"}).status_code == 403
    assert client.patch(endpoint, headers=hospital, json={"status": "triage"}).status_code == 200


def test_shelter_accounts_see_nearby_stable_arrivals_only(client, app, seeded):
    shelter = bearer(client, "Shelter")
    rescues = client.get("/api/v1/operations/bootstrap", headers=shelter).get_json()["rescue_requests"]
    names = {item["victim_name"] for item in rescues}
    assert "Fathima Banu" in names
    with app.app_context():
        critical = RescueRequest.query.filter_by(victim_name="Meena Kumar").first()
        assert critical is not None
    assert "Meena Kumar" not in names
    assert all(item["condition"] == "stable" for item in rescues)

    blocked = client.patch(f"/api/v1/rescue-requests/{rescues[0]['id']}/status", headers=shelter, json={"status": "rescued"})
    assert blocked.status_code == 403


def test_location_pings_attach_only_to_the_callers_own_cases(client, app, seeded):
    with app.app_context():
        foreign_rescue_id = RescueRequest.query.filter_by(victim_name="Meena Kumar").first().id
    volunteer = bearer(client, "Volunteer")
    response = client.post(
        "/api/v1/location-pings",
        headers=volunteer,
        json={
            "consent_granted": True,
            "latitude": 12.98,
            "longitude": 80.22,
            "rescue_request_id": foreign_rescue_id,
        },
    )
    assert response.status_code == 400
    citizen = bearer(client, "Citizen")
    own = client.post(
        "/api/v1/location-pings",
        headers=citizen,
        json={"consent_granted": True, "latitude": 12.98, "longitude": 80.22, "rescue_request_id": foreign_rescue_id},
    )
    assert own.status_code == 201


def test_ambulance_location_and_status_values_are_validated(client, app, seeded):
    ambulance = bearer(client, "Ambulance")
    unit_id = client.get("/api/v1/operations/bootstrap", headers=ambulance).get_json()["facilities"]["ambulances"][0]["id"]
    endpoint = f"/api/v1/ambulances/{unit_id}/status"
    assert client.patch(endpoint, headers=ambulance, json={"status": "flying"}).status_code == 400
    assert client.patch(endpoint, headers=ambulance, json={"latitude": "north"}).status_code == 400
    assert client.patch(endpoint, headers=ambulance, json={"latitude": 13.0, "longitude": 500}).status_code == 400
    moved = client.patch(endpoint, headers=ambulance, json={"latitude": 13.01, "longitude": 80.25, "status": "offline"})
    assert moved.status_code == 200
    assert moved.get_json()["ambulance"]["status"] == "offline"


def test_shelter_service_flags_require_booleans(client, seeded):
    shelter = bearer(client, "Shelter")
    shelter_id = client.get("/api/v1/operations/bootstrap", headers=shelter).get_json()["facilities"]["shelters"][0]["id"]
    endpoint = f"/api/v1/shelters/{shelter_id}/capacity"
    assert client.patch(endpoint, headers=shelter, json={"food_available": "false"}).status_code == 400
    updated = client.patch(endpoint, headers=shelter, json={"food_available": False, "medical_support": True})
    assert updated.status_code == 200
    assert updated.get_json()["shelter"]["food_available"] is False


def test_distribution_status_is_constrained(client, app, seeded):
    ngo = bearer(client, "NGO")
    coordination = client.get("/api/v1/coordination", headers=ngo).get_json()
    disaster_id = first_disaster_id(client, ngo)
    payload = {
        "resource_id": coordination["resources"][0]["id"],
        "disaster_id": disaster_id,
        "quantity": 1,
        "destination": "Camp",
    }
    assert client.post("/api/v1/distributions", headers=ngo, json={**payload, "status": "stolen"}).status_code == 400
    assert client.post("/api/v1/distributions", headers=ngo, json={**payload, "quantity": 0}).status_code == 400
    assert client.post("/api/v1/distributions", headers=ngo, json=payload).status_code == 201


def test_incident_status_is_managed_by_command_roles(client, app, seeded):
    police = bearer(client, "Police")
    citizen = bearer(client, "Citizen")
    disaster_id = first_disaster_id(client, police)
    endpoint = f"/api/v1/disasters/{disaster_id}/status"
    assert client.patch(endpoint, headers=citizen, json={"status": "closed"}).status_code == 403
    assert client.patch(endpoint, headers=police, json={"status": "exploded"}).status_code == 400
    response = client.patch(endpoint, headers=police, json={"status": "contained"})
    assert response.status_code == 200
    assert response.get_json()["disaster"]["status"] == "contained"


def test_public_feeds_do_not_expose_account_identifiers(client, seeded):
    feed = client.get("/api/v1/national-alerts").get_json()
    assert feed["disasters"]
    assert all("reported_by_id" not in item for item in feed["disasters"])
    assert all("published_by_id" not in item for item in feed["news_updates"])
    news = client.get("/api/v1/news-updates").get_json()["news_updates"]
    assert all("published_by_id" not in item for item in news)
