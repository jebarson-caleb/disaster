import pytest
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.maintenance import PURGE_CONFIRMATION, TRAINING_EMAILS, build_training_cleanup_plan, purge_training_data
from app.models import (
    AccountSecurity,
    Ambulance,
    AuditEvent,
    Disaster,
    Hospital,
    Notification,
    RoleProfile,
    Shelter,
    User,
    Volunteer,
)


def create_training_fixtures():
    hospital = Hospital(
        name="Training Hospital - Not for Incident Use",
        address="Training only",
        latitude=0,
        longitude=0,
        total_beds=1,
        available_beds=0,
        icu_beds=0,
        emergency_capacity=0,
        contact_phone="0000000000",
    )
    shelter = Shelter(
        name="Training Shelter - Not for Incident Use",
        address="Training only",
        latitude=0,
        longitude=0,
        total_capacity=1,
        available_capacity=0,
        food_available=False,
        medical_support=False,
        contact_phone="0000000000",
    )
    ambulance = Ambulance(
        vehicle_number="TN-00-TRN-001",
        driver_name="Training Driver",
        phone="0000000000",
        latitude=0,
        longitude=0,
        status="maintenance",
    )
    db.session.add_all([hospital, shelter, ambulance])
    db.session.flush()

    user_by_role = {}
    for email in sorted(TRAINING_EMAILS):
        role = {
            "ambulance": "Ambulance",
            "citizen": "Citizen",
            "fire-service": "Fire Service",
            "hospital": "Hospital",
            "ngo": "NGO",
            "police": "Police",
            "shelter": "Shelter",
            "volunteer": "Volunteer",
        }[email.split(".", 1)[0]]
        user = User(
            name=f"Training {role}",
            email=email,
            phone="0000000000",
            role=role,
            password_hash=generate_password_hash("TrainingPassword123!", method="scrypt"),
        )
        db.session.add(user)
        db.session.flush()
        profile = RoleProfile(user_id=user.id, verification_status="verified")
        if role == "Hospital":
            profile.hospital_id = hospital.id
        elif role == "Shelter":
            profile.shelter_id = shelter.id
        elif role == "Ambulance":
            profile.ambulance_id = ambulance.id
        db.session.add_all([profile, AccountSecurity(user_id=user.id), Notification(user_id=user.id, message="Training")])
        user_by_role[role] = user

    db.session.add(Volunteer(user_id=user_by_role["Volunteer"].id, skills="training", availability_status="available"))
    db.session.add(AuditEvent(event_type="training_login", user_id=user_by_role["Citizen"].id, outcome="success"))
    db.session.commit()
    return user_by_role


def test_training_cleanup_purges_only_exact_unreferenced_fixtures(app):
    with app.app_context():
        admin = User(
            name="Real Admin",
            email="admin@example.com",
            phone="112",
            role="Admin",
            password_hash=generate_password_hash("RealAdminPassword123!", method="scrypt"),
        )
        db.session.add(admin)
        create_training_fixtures()

        plan = build_training_cleanup_plan()
        assert plan.state == "ready"
        assert plan.records_to_remove["users"] == 8
        assert plan.records_to_remove["audit_events_anonymized"] == 1

        result = purge_training_data(PURGE_CONFIRMATION)
        assert result.state == "purged"
        assert User.query.all() == [admin]
        assert Hospital.query.count() == 0
        assert Shelter.query.count() == 0
        assert Ambulance.query.count() == 0
        assert AuditEvent.query.filter_by(event_type="training_login", user_id=None).count() == 1
        assert AuditEvent.query.filter_by(event_type="production_training_data_purged").count() == 1
        assert build_training_cleanup_plan().state == "already_clean"


def test_training_cleanup_refuses_operationally_referenced_accounts(app):
    with app.app_context():
        users = create_training_fixtures()
        db.session.add(
            Disaster(
                title="A real incident",
                disaster_type="flood",
                description="Operational record",
                address="Live location",
                latitude=10,
                longitude=80,
                reported_by_id=users["Citizen"].id,
            )
        )
        db.session.commit()

        plan = build_training_cleanup_plan()
        assert plan.state == "blocked"
        assert plan.blockers == {"disasters_reported": 1}
        with pytest.raises(RuntimeError, match="purge blocked"):
            purge_training_data(PURGE_CONFIRMATION)
        assert User.query.filter(User.email.in_(TRAINING_EMAILS)).count() == 8
