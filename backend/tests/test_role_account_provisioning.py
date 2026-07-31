import pytest

from app.auth import verify_password
from app.extensions import db
from app.models import AccountSecurity, Ambulance, AuditEvent, Hospital, RoleProfile, Shelter, User, Volunteer
from app.role_account_provisioning import (
    PROVISION_CONFIRMATION,
    ROLE_ACCOUNT_SPECS,
    build_role_account_plan,
    provision_role_accounts,
    verify_role_accounts,
)

TEMPORARY_PASSWORDS = {
    spec["email"]: f"Temporary-{index}-Access!"
    for index, spec in enumerate(ROLE_ACCOUNT_SPECS, start=1)
}


def test_role_account_provisioning_is_guarded_and_idempotent(app):
    with app.app_context():
        preview = build_role_account_plan()
        assert preview["state"] == "ready"
        assert {item["status"] for item in preview["accounts"]} == {"create"}

        with pytest.raises(RuntimeError, match="confirmation must exactly equal"):
            provision_role_accounts(TEMPORARY_PASSWORDS, "wrong")
        invalid_passwords = {**TEMPORARY_PASSWORDS, "admin@local.test": "1234567890"}
        with pytest.raises(RuntimeError, match="temporary password for admin@local.test does not meet policy"):
            provision_role_accounts(invalid_passwords, PROVISION_CONFIRMATION)
        reused_passwords = dict.fromkeys(TEMPORARY_PASSWORDS, "Temporary-Shared-Access!")
        with pytest.raises(RuntimeError, match="unique temporary password"):
            provision_role_accounts(reused_passwords, PROVISION_CONFIRMATION)

        result = provision_role_accounts(TEMPORARY_PASSWORDS, PROVISION_CONFIRMATION)
        assert {item["status"] for item in result["accounts"]} == {"created"}
        verification = verify_role_accounts(TEMPORARY_PASSWORDS)
        assert verification["state"] == "verified"
        assert {item["status"] for item in verification["accounts"]} == {"verified"}
        assert User.query.count() == len(ROLE_ACCOUNT_SPECS)
        assert AccountSecurity.query.filter_by(must_change_password=False).count() == len(ROLE_ACCOUNT_SPECS)
        assert AuditEvent.query.filter_by(event_type="system.role_account_provision").count() == len(ROLE_ACCOUNT_SPECS)

        for spec in ROLE_ACCOUNT_SPECS:
            user = User.query.filter_by(email=spec["email"], role=spec["role"]).one()
            assert verify_password(user.password_hash, TEMPORARY_PASSWORDS[user.email])
            assert RoleProfile.query.filter_by(user_id=user.id, verification_status="verified").one()

        hospital = User.query.filter_by(role="Hospital").one()
        shelter = User.query.filter_by(role="Shelter").one()
        ambulance = User.query.filter_by(role="Ambulance").one()
        volunteer = User.query.filter_by(role="Volunteer").one()
        assert db.session.get(Hospital, RoleProfile.query.filter_by(user_id=hospital.id).one().hospital_id)
        assert db.session.get(Shelter, RoleProfile.query.filter_by(user_id=shelter.id).one().shelter_id)
        assert (
            db.session.get(Ambulance, RoleProfile.query.filter_by(user_id=ambulance.id).one().ambulance_id).status
            == "offline"
        )
        assert Volunteer.query.filter_by(user_id=volunteer.id).one().availability_status == "unavailable"

        repeated = provision_role_accounts(TEMPORARY_PASSWORDS, PROVISION_CONFIRMATION)
        assert {item["status"] for item in repeated["accounts"]} == {"already_exists"}
        assert User.query.count() == len(ROLE_ACCOUNT_SPECS)

        replacement_passwords = {
            email: password.replace("Temporary", "Replacement")
            for email, password in TEMPORARY_PASSWORDS.items()
        }
        reissued = provision_role_accounts(
            replacement_passwords,
            PROVISION_CONFIRMATION,
            reissue_managed=True,
        )
        assert {item["status"] for item in reissued["accounts"]} == {"credential_reissued"}
        for spec in ROLE_ACCOUNT_SPECS:
            user = User.query.filter_by(email=spec["email"]).one()
            assert verify_password(user.password_hash, replacement_passwords[user.email])
            assert not verify_password(user.password_hash, TEMPORARY_PASSWORDS[user.email])


def test_role_account_plan_blocks_an_email_role_collision(app):
    with app.app_context():
        db.session.add(
            User(
                name="Conflicting user",
                email="admin@local.test",
                phone="Not provided",
                role="Citizen",
                password_hash="not-used",
            )
        )
        db.session.commit()

        plan = build_role_account_plan()
        assert plan["state"] == "blocked"
        assert plan["accounts"][0]["status"] == "role_conflict"
        with pytest.raises(RuntimeError, match="provisioning is blocked"):
            provision_role_accounts(TEMPORARY_PASSWORDS, PROVISION_CONFIRMATION)
