from app.extensions import db
from app.models import Ambulance, Disaster, Hospital, HospitalNotification, RoleProfile, Shelter, User
from app.seed import seed_demo_data

TEMPORARY_PASSWORD = "Temporary-Access-Password-71"
PRIVATE_PASSWORD = "Private-Account-Password-83"
def csrf_headers(client):
    return {"X-CSRF-Token": client.get_cookie("resq_csrf").value}


def facility_payload(role, suffix):
    if role == "Hospital":
        return {
            "facility": {
                "name": f"Acceptance Hospital {suffix}",
                "address": "Hospital Road",
                "latitude": 13.01,
                "longitude": 80.21,
                "contact_phone": f"91000000{suffix:02d}",
                "total_beds": 100,
                "available_beds": 45,
                "icu_beds": 10,
                "emergency_capacity": 20,
            }
        }
    if role == "Shelter":
        return {
            "facility": {
                "name": f"Acceptance Shelter {suffix}",
                "address": "Relief Camp Road",
                "latitude": 13.02,
                "longitude": 80.22,
                "contact_phone": f"92000000{suffix:02d}",
                "total_capacity": 400,
                "available_capacity": 275,
                "food_available": True,
                "medical_support": True,
            }
        }
    if role == "Ambulance":
        return {
            "facility": {
                "vehicle_number": f"TN-00-TEST-{suffix:02d}",
                "driver_name": f"Acceptance Driver {suffix}",
                "latitude": 13.03,
                "longitude": 80.23,
                "contact_phone": f"93000000{suffix:02d}",
            }
        }
    return {}


def test_every_supported_role_changes_temporary_password_and_opens_workspace(client, auth_headers):
    roles = [
        "Citizen",
        "Volunteer",
        "Police",
        "Fire Service",
        "Hospital",
        "Shelter",
        "Ambulance",
        "NGO",
        "Admin",
    ]
    for index, role in enumerate(roles, start=1):
        email = f"{role.lower().replace(' ', '-')}-{index}@acceptance.example"
        provisioned = client.post(
            "/api/v1/admin/users",
            headers=auth_headers,
            json={
                "name": f"{role} Acceptance User",
                "email": email,
                "phone": f"94000000{index:02d}",
                "role": role,
                "password": TEMPORARY_PASSWORD,
                "organization_name": f"{role} Acceptance Operations",
                **facility_payload(role, index),
            },
        )
        assert provisioned.status_code == 201, provisioned.get_json()
        provisioned_payload = provisioned.get_json()
        assert provisioned_payload["user"]["password_change_required"] is True
        if role in {"Hospital", "Shelter", "Ambulance"}:
            assert provisioned_payload["facility"]["id"] == provisioned_payload["user"]["managed_facility"]["id"]

        signed_in = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": TEMPORARY_PASSWORD},
        )
        assert signed_in.status_code == 200
        assert signed_in.get_json()["password_change_required"] is True
        blocked = client.get("/api/v1/operations/bootstrap")
        assert blocked.status_code == 403
        assert blocked.get_json()["code"] == "password_change_required"

        changed = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": TEMPORARY_PASSWORD, "new_password": PRIVATE_PASSWORD},
            headers=csrf_headers(client),
        )
        assert changed.status_code == 200, changed.get_json()
        assert changed.get_json()["password_change_required"] is False

        workspace = client.get("/api/v1/operations/bootstrap")
        assert workspace.status_code == 200, workspace.get_json()
        snapshot = workspace.get_json()
        if role == "Hospital":
            assert [item["id"] for item in snapshot["facilities"]["hospitals"]] == [
                provisioned_payload["facility"]["id"]
            ]
        elif role == "Shelter":
            assert [item["id"] for item in snapshot["facilities"]["shelters"]] == [
                provisioned_payload["facility"]["id"]
            ]
        elif role == "Ambulance":
            assert [item["id"] for item in snapshot["facilities"]["ambulances"]] == [
                provisioned_payload["facility"]["id"]
            ]

        signed_out = client.post("/api/v1/auth/logout", json={}, headers=csrf_headers(client))
        assert signed_out.status_code == 200


def test_facility_accounts_can_mutate_only_their_assigned_record(client, app):
    with app.app_context():
        seed_demo_data()
        hospital_user_profile = RoleProfile.query.join(RoleProfile.user).filter(User.role == "Hospital").one()
        shelter_user_profile = RoleProfile.query.join(RoleProfile.user).filter(User.role == "Shelter").one()
        ambulance_user_profile = RoleProfile.query.join(RoleProfile.user).filter(User.role == "Ambulance").one()
        other_hospital = Hospital(
            name="Other Hospital",
            address="Other Road",
            latitude=11,
            longitude=77,
            total_beds=40,
            available_beds=20,
            icu_beds=4,
            emergency_capacity=10,
            contact_phone="9500000001",
        )
        other_shelter = Shelter(
            name="Other Shelter",
            address="Other School",
            latitude=11,
            longitude=77,
            total_capacity=200,
            available_capacity=150,
            contact_phone="9500000002",
        )
        other_ambulance = Ambulance(
            vehicle_number="TN-00-OTHER-01",
            driver_name="Other Driver",
            phone="9500000003",
            latitude=11,
            longitude=77,
        )
        db.session.add_all([other_hospital, other_shelter, other_ambulance])
        db.session.flush()
        own_notification = HospitalNotification.query.filter_by(
            hospital_id=hospital_user_profile.hospital_id
        ).one()
        db.session.add(
            HospitalNotification(
                hospital_id=other_hospital.id,
                disaster_id=own_notification.disaster_id,
                rescue_request_id=own_notification.rescue_request_id,
                expected_patients=2,
                priority="High",
                message="Other hospital only",
            )
        )
        db.session.commit()
        identifiers = {
            "hospital": (hospital_user_profile.hospital_id, other_hospital.id),
            "shelter": (shelter_user_profile.shelter_id, other_shelter.id),
            "ambulance": (ambulance_user_profile.ambulance_id, other_ambulance.id),
        }

    hospital_token = client.post("/api/v1/auth/demo-session", json={"role": "Hospital"}).get_json()["token"]
    hospital_headers = {"Authorization": f"Bearer {hospital_token}"}
    assert client.patch(
        f"/api/v1/hospitals/{identifiers['hospital'][0]}/capacity",
        headers=hospital_headers,
        json={"available_beds": 30},
    ).status_code == 200
    assert client.patch(
        f"/api/v1/hospitals/{identifiers['hospital'][1]}/capacity",
        headers=hospital_headers,
        json={"available_beds": 10},
    ).status_code == 403
    hospital_snapshot = client.get("/api/v1/operations/bootstrap", headers=hospital_headers).get_json()
    assert [item["id"] for item in hospital_snapshot["facilities"]["hospitals"]] == [
        identifiers["hospital"][0]
    ]
    assert all(
        item["hospital_id"] == identifiers["hospital"][0]
        for item in hospital_snapshot["response_hub"]["hospital_notifications"]
    )

    shelter_token = client.post("/api/v1/auth/demo-session", json={"role": "Shelter"}).get_json()["token"]
    shelter_headers = {"Authorization": f"Bearer {shelter_token}"}
    assert client.patch(
        f"/api/v1/shelters/{identifiers['shelter'][0]}/capacity",
        headers=shelter_headers,
        json={"available_capacity": 200},
    ).status_code == 200
    assert client.patch(
        f"/api/v1/shelters/{identifiers['shelter'][1]}/capacity",
        headers=shelter_headers,
        json={"available_capacity": 100},
    ).status_code == 403

    ambulance_token = client.post("/api/v1/auth/demo-session", json={"role": "Ambulance"}).get_json()["token"]
    ambulance_headers = {"Authorization": f"Bearer {ambulance_token}"}
    assert client.patch(
        f"/api/v1/ambulances/{identifiers['ambulance'][0]}/status",
        headers=ambulance_headers,
        json={"status": "dispatched"},
    ).status_code == 200
    assert client.patch(
        f"/api/v1/ambulances/{identifiers['ambulance'][1]}/status",
        headers=ambulance_headers,
        json={"status": "maintenance"},
    ).status_code == 403


def test_citizen_login_exposes_only_its_own_rescue_cases(client, app):
    with app.app_context():
        seed_demo_data()
        disaster_id = Disaster.query.first().id

    first = client.post(
        "/api/v1/auth/register",
        json={
            "name": "First Citizen",
            "email": "first-citizen@acceptance.example",
            "phone": "9700000001",
            "role": "Citizen",
            "password": "First-Citizen-Private-Password-91",
        },
    )
    first_user_id = first.get_json()["user"]["id"]
    first_case = client.post(
        "/api/v1/rescue-requests",
        json={
            "disaster_id": disaster_id,
            "victim_name": "First Citizen Case",
            "latitude": 13.01,
            "longitude": 80.21,
        },
        headers=csrf_headers(client),
    )
    assert first_case.status_code == 201
    assert client.post("/api/v1/auth/logout", json={}, headers=csrf_headers(client)).status_code == 200

    second = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Second Citizen",
            "email": "second-citizen@acceptance.example",
            "phone": "9700000002",
            "role": "Citizen",
            "password": "Second-Citizen-Private-Password-92",
        },
    )
    second_user_id = second.get_json()["user"]["id"]
    second_case = client.post(
        "/api/v1/rescue-requests",
        json={
            "disaster_id": disaster_id,
            "victim_name": "Second Citizen Case",
            "latitude": 13.02,
            "longitude": 80.22,
        },
        headers=csrf_headers(client),
    )
    assert second_case.status_code == 201

    bootstrap_cases = client.get("/api/v1/operations/bootstrap").get_json()["rescue_requests"]
    list_cases = client.get("/api/v1/rescue-requests").get_json()["rescue_requests"]
    assert {item["requester_id"] for item in bootstrap_cases} == {second_user_id}
    assert {item["requester_id"] for item in list_cases} == {second_user_id}
    assert first_user_id not in {item["requester_id"] for item in bootstrap_cases}


def test_administrator_can_create_live_operational_baseline(client, app, auth_headers):
    with app.app_context():
        seed_demo_data()
        disaster_id = Disaster.query.first().id

    resource = client.post(
        "/api/v1/admin/resources",
        headers=auth_headers,
        json={
            "name": "Acceptance Water Kits",
            "category": "water",
            "unit": "kits",
            "available_quantity": 250,
            "storage_location": "Acceptance Warehouse",
        },
    )
    assert resource.status_code == 201

    responder = client.post(
        "/api/v1/admin/responders",
        headers=auth_headers,
        json={
            "name": "Acceptance Rescue Unit",
            "unit_type": "professional rescue",
            "skills": "water rescue, first aid",
            "contact_phone": "9600000001",
            "latitude": 13.04,
            "longitude": 80.24,
        },
    )
    assert responder.status_code == 201

    campaign = client.post(
        "/api/v1/admin/donation-campaigns",
        headers=auth_headers,
        json={
            "disaster_id": disaster_id,
            "title": "Acceptance Relief Campaign",
            "description": "Verified acceptance-test relief campaign.",
            "goal_amount": 100000,
            "currency": "INR",
            "organizer": "Acceptance Relief Coalition",
        },
    )
    assert campaign.status_code == 201
