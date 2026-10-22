from app.extensions import db
from app.models import Volunteer
from tests.test_hardening import bearer, first_disaster_id, seeded  # noqa: F401


def closure_payload(**overrides):
    return {
        "road_name": "Velachery Main Road",
        "location": "Lake bund service road junction",
        "latitude": 12.9801,
        "longitude": 80.2205,
        "reason": "Knee-deep water and a collapsed drain cover.",
        "diversion": "Use 100 Feet Road via Guindy",
        **overrides,
    }


def test_police_publish_and_reopen_road_closures_visible_to_citizens(client, seeded):  # noqa: F811
    police = bearer(client, "Police")
    disaster_id = first_disaster_id(client, police)
    created = client.post("/api/v1/road-closures", headers=police, json=closure_payload(disaster_id=disaster_id))
    assert created.status_code == 201
    closure = created.get_json()["road_closure"]
    assert closure["status"] == "closed"

    citizen = bearer(client, "Citizen")
    snapshot = client.get("/api/v1/operations/bootstrap", headers=citizen).get_json()
    assert [item["road_name"] for item in snapshot["field"]["road_closures"]] == ["Velachery Main Road"]
    assert client.post("/api/v1/road-closures", headers=citizen, json=closure_payload()).status_code == 403

    fire = bearer(client, "Fire Service")
    reopened = client.patch(f"/api/v1/road-closures/{closure['id']}", headers=fire, json={"status": "reopened"})
    assert reopened.status_code == 200
    assert reopened.get_json()["road_closure"]["status"] == "reopened"


def test_road_closures_validate_status_and_location(client, seeded):  # noqa: F811
    police = bearer(client, "Police")
    assert client.post("/api/v1/road-closures", headers=police, json=closure_payload(status="reopened")).status_code == 400
    assert client.post("/api/v1/road-closures", headers=police, json=closure_payload(latitude=200)).status_code == 400
    assert client.post("/api/v1/road-closures", headers=police, json=closure_payload(reason="")).status_code == 400
    assert client.post("/api/v1/road-closures", headers=police, json=closure_payload(disaster_id=999999)).status_code == 404


def test_readiness_checklists_are_recorded_and_scoped_by_role(client, seeded):  # noqa: F811
    fire = bearer(client, "Fire Service")
    created = client.post(
        "/api/v1/readiness-checks",
        headers=fire,
        json={
            "subject": "Rescue Tender 3",
            "items": {"Breathing apparatus": True, "Rescue boat": True, "Hydraulic cutter": False},
            "notes": "Cutter hose replacement due",
        },
    )
    assert created.status_code == 201
    check = created.get_json()["readiness_check"]
    assert (check["ready_count"], check["total_count"]) == (2, 3)
    assert check["items"]["Hydraulic cutter"] is False

    fire_view = client.get("/api/v1/operations/bootstrap", headers=fire).get_json()["field"]["readiness_checks"]
    assert [item["subject"] for item in fire_view] == ["Rescue Tender 3"]
    police_view = client.get("/api/v1/readiness-checks", headers=bearer(client, "Police")).get_json()["readiness_checks"]
    assert police_view == []
    admin_view = client.get("/api/v1/readiness-checks", headers=bearer(client, "Admin")).get_json()["readiness_checks"]
    assert [item["role"] for item in admin_view] == ["Fire Service"]

    citizen = bearer(client, "Citizen")
    assert client.post("/api/v1/readiness-checks", headers=citizen, json={"subject": "x", "items": {"a": True}}).status_code == 403


def test_readiness_checklists_reject_malformed_items(client, seeded):  # noqa: F811
    volunteer = bearer(client, "Volunteer")
    endpoint = "/api/v1/readiness-checks"
    assert client.post(endpoint, headers=volunteer, json={"subject": "Shift", "items": []}).status_code == 400
    assert client.post(endpoint, headers=volunteer, json={"subject": "Shift", "items": {}}).status_code == 400
    assert client.post(endpoint, headers=volunteer, json={"subject": "Shift", "items": {"PPE": "yes"}}).status_code == 400
    too_many = {f"Item {index}": True for index in range(13)}
    assert client.post(endpoint, headers=volunteer, json={"subject": "Shift", "items": too_many}).status_code == 400


def test_volunteers_manage_their_own_duty_status_and_assignments(client, app, seeded):  # noqa: F811
    volunteer = bearer(client, "Volunteer")
    snapshot = client.get("/api/v1/operations/bootstrap", headers=volunteer).get_json()["field"]["volunteer"]
    assert snapshot["availability_status"] == "available"

    off_duty = client.patch("/api/v1/volunteers/me/availability", headers=volunteer, json={"availability_status": "off duty"})
    assert off_duty.status_code == 200
    assert off_duty.get_json()["volunteer"]["availability_status"] == "off duty"
    assert client.patch(
        "/api/v1/volunteers/me/availability", headers=volunteer, json={"availability_status": "assigned"}
    ).status_code == 400
    client.patch("/api/v1/volunteers/me/availability", headers=volunteer, json={"availability_status": "available"})

    ngo = bearer(client, "NGO")
    with app.app_context():
        volunteer_id = Volunteer.query.first().id
    assignment = client.post(
        "/api/v1/volunteer-assignments",
        headers=ngo,
        json={"volunteer_id": volunteer_id, "disaster_id": first_disaster_id(client, ngo), "task": "Shelter intake desk"},
    ).get_json()["assignment"]
    blocked = client.patch("/api/v1/volunteers/me/availability", headers=volunteer, json={"availability_status": "off duty"})
    assert blocked.status_code == 409

    police = bearer(client, "Police")
    assert client.patch(
        f"/api/v1/volunteer-assignments/{assignment['id']}", headers=police, json={"status": "completed"}
    ).status_code == 403
    completed = client.patch(
        f"/api/v1/volunteer-assignments/{assignment['id']}", headers=volunteer, json={"status": "completed"}
    )
    assert completed.status_code == 200
    with app.app_context():
        assert db.session.get(Volunteer, volunteer_id).availability_status == "available"
