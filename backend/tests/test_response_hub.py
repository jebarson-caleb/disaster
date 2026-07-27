from app.extensions import db
from app.models import Ambulance, HospitalNotification, LocationPing, ResponderUnit, ResponseDispatch, Volunteer
from app.seed import seed_demo_data


def demo_headers(client, role):
    response = client.post("/api/v1/auth/demo-session", json={"role": role})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


def test_countrywide_alerts_and_live_news_are_public(client, app):
    with app.app_context():
        seed_demo_data()

    response = client.get("/api/v1/national-alerts")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["country"] == "India"
    assert len(payload["disasters"]) >= 4
    assert len({item["state"] for item in payload["news_updates"]}) >= 3
    assert any(item["is_live"] and item["stream_url"] for item in payload["news_updates"])
    disaster_ids = {item["id"] for item in payload["disasters"]}
    live_disaster_ids = {item["disaster_id"] for item in payload["news_updates"] if item["is_live"] and item["stream_url"]}
    assert disaster_ids <= live_disaster_ids


def test_rescue_auto_dispatch_location_and_hospital_prep(client, app):
    with app.app_context():
        seed_demo_data()
    headers = demo_headers(client, "Admin")
    disaster_id = client.get("/api/v1/operations/bootstrap", headers=headers).get_json()["disasters"][0]["id"]

    response = client.post(
        "/api/v1/rescue-requests",
        headers=headers,
        json={
            "disaster_id": disaster_id,
            "victim_name": "Remote flood survivor",
            "people_count": 4,
            "condition": "critical",
            "trapped": True,
            "latitude": 12.981,
            "longitude": 80.22,
            "location_accuracy": 12,
            "location_consent": True,
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    rescue_id = payload["rescue_request"]["id"]
    assert payload["rescue_request"]["status"] == "assigned"
    assert payload["automatic_allocation"]["rescue_unit"]
    assert payload["automatic_allocation"]["volunteer"]
    assert payload["automatic_allocation"]["ambulance"]
    assert payload["automatic_allocation"]["hospital"]

    with app.app_context():
        assert ResponseDispatch.query.filter_by(rescue_request_id=rescue_id).count() == 3
        assert HospitalNotification.query.filter_by(rescue_request_id=rescue_id).count() == 1
        assert LocationPing.query.filter_by(rescue_request_id=rescue_id, consent_granted=True).count() == 1

    hospital_headers = demo_headers(client, "Hospital")
    notices = client.get("/api/v1/hospital-notifications", headers=hospital_headers).get_json()["hospital_notifications"]
    notice = next(item for item in notices if item["rescue_request_id"] == rescue_id)
    acknowledged = client.patch(f"/api/v1/hospital-notifications/{notice['id']}/acknowledge", headers=hospital_headers)
    assert acknowledged.status_code == 200
    assert acknowledged.get_json()["hospital_notification"]["status"] == "acknowledged"

    completed = client.patch(f"/api/v1/rescue-requests/{rescue_id}/status", headers=headers, json={"status": "rescued"})
    assert completed.status_code == 200
    with app.app_context():
        dispatches = ResponseDispatch.query.filter_by(rescue_request_id=rescue_id).all()
        assert {item.status for item in dispatches} == {"completed"}
        assert db.session.get(ResponderUnit, payload["automatic_allocation"]["rescue_unit"]["id"]).availability_status == "available"
        assert db.session.get(Volunteer, payload["automatic_allocation"]["volunteer"]["id"]).availability_status == "available"
        assert db.session.get(Ambulance, payload["automatic_allocation"]["ambulance"]["id"]).status == "available"


def test_family_welfare_check_call_responder_flow(client, app):
    with app.app_context():
        seed_demo_data()
    citizen_headers = demo_headers(client, "Citizen")
    disaster_id = client.get("/api/v1/operations/bootstrap", headers=citizen_headers).get_json()["disasters"][0]["id"]
    created = client.post(
        "/api/v1/welfare-checks",
        headers=citizen_headers,
        json={
            "disaster_id": disaster_id,
            "relative_name": "Sanjay Rao",
            "relationship": "Father",
            "last_known_location": "Flood shelter intake gate",
            "requester_phone": "9000000999",
            "consent_to_contact": True,
        },
    )
    assert created.status_code == 201
    case = created.get_json()["welfare_check"]
    assert case["call_url"] == "tel:112"
    assert case["status"] == "requested"

    admin_headers = demo_headers(client, "Admin")
    updated = client.patch(
        f"/api/v1/welfare-checks/{case['id']}",
        headers=admin_headers,
        json={"status": "located_safe", "responder_notes": "Matched at verified shelter intake."},
    )
    assert updated.status_code == 200
    assert updated.get_json()["welfare_check"]["status"] == "located_safe"


def test_isolated_survivor_supply_request_and_device_location(client, app):
    with app.app_context():
        seed_demo_data()
    citizen_headers = demo_headers(client, "Citizen")
    disaster_id = client.get("/api/v1/operations/bootstrap", headers=citizen_headers).get_json()["disasters"][0]["id"]
    created = client.post(
        "/api/v1/supply-requests",
        headers=citizen_headers,
        json={
            "disaster_id": disaster_id,
            "category": "food and medicine",
            "description": "Diabetic resident isolated with no food access.",
            "people_count": 2,
            "urgency": "critical",
            "contact_phone": "9000000888",
            "latitude": 12.982,
            "longitude": 80.221,
            "location_accuracy": 9,
            "location_consent": True,
        },
    )
    assert created.status_code == 201
    supply = created.get_json()["supply_request"]
    assert supply["status"] == "requested"

    ngo_headers = demo_headers(client, "NGO")
    updated = client.patch(
        f"/api/v1/supply-requests/{supply['id']}",
        headers=ngo_headers,
        json={"status": "en route", "assigned_unit": "Relief Bike Team 3"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["supply_request"]["assigned_unit"] == "Relief Bike Team 3"

    denied = client.post("/api/v1/location-pings", headers=citizen_headers, json={"latitude": 1, "longitude": 2})
    assert denied.status_code == 400
    shared = client.post(
        "/api/v1/location-pings",
        headers=citizen_headers,
        json={"latitude": 12.982, "longitude": 80.221, "accuracy_meters": 8, "consent_granted": True},
    )
    assert shared.status_code == 201


def test_donation_campaign_pledge_and_confirmation(client, app):
    with app.app_context():
        seed_demo_data()
    campaign = client.get("/api/v1/donation-campaigns").get_json()["campaigns"][0]
    created = client.post(
        "/api/v1/donations",
        json={
            "campaign_id": campaign["id"],
            "donor_name": "Asha Donor",
            "donor_email": "asha@example.com",
            "amount": 1500,
            "message": "For emergency food supplies",
        },
    )
    assert created.status_code == 201
    donation = created.get_json()["donation"]
    assert donation["status"] == "pledged"
    assert donation["reference"].startswith("DON-")

    admin_headers = demo_headers(client, "Admin")
    confirmed = client.patch(f"/api/v1/donations/{donation['id']}/status", headers=admin_headers, json={"status": "confirmed"})
    assert confirmed.status_code == 200
    refreshed = client.get("/api/v1/donation-campaigns").get_json()["campaigns"][0]
    assert refreshed["confirmed_amount"] == 1500.0
