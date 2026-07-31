"""Guarded provisioning for the operator-requested live test role accounts."""

from .auth import hash_password, utcnow, validate_password, verify_password
from .extensions import db
from .models import (
    AccountSecurity,
    Ambulance,
    AuditEvent,
    AuthSession,
    Hospital,
    PasswordResetToken,
    RoleProfile,
    Shelter,
    User,
    Volunteer,
)

PROVISION_CONFIRMATION = "PROVISION_LIVE_ROLE_ACCOUNTS"

ROLE_ACCOUNT_SPECS = (
    {"role": "Admin", "email": "admin@local.test", "name": "Local Administrator"},
    {"role": "Citizen", "email": "citizen@local.test", "name": "Local Citizen"},
    {"role": "Volunteer", "email": "volunteer@local.test", "name": "Local Volunteer"},
    {"role": "Police", "email": "police@local.test", "name": "Local Police Officer"},
    {"role": "Fire Service", "email": "fire@local.test", "name": "Local Fire Officer"},
    {"role": "Hospital", "email": "hospital@local.test", "name": "Local Hospital Officer"},
    {"role": "Shelter", "email": "shelter@local.test", "name": "Local Shelter Officer"},
    {"role": "Ambulance", "email": "ambulance@local.test", "name": "Local Ambulance Officer"},
    {"role": "NGO", "email": "ngo@local.test", "name": "Local NGO Officer"},
)


def build_role_account_plan():
    """Return a credential-free preview of the exact accounts this command manages."""
    emails = [spec["email"] for spec in ROLE_ACCOUNT_SPECS]
    existing = {user.email: user for user in User.query.filter(User.email.in_(emails)).all()}
    accounts = []
    problems = []
    for spec in ROLE_ACCOUNT_SPECS:
        user = existing.get(spec["email"])
        status = "create"
        if user:
            status = "already_exists" if user.role == spec["role"] else "role_conflict"
            if status == "role_conflict":
                problems.append(
                    f"{spec['email']} is already assigned to {user.role}, not {spec['role']}"
                )
        accounts.append({"email": spec["email"], "role": spec["role"], "status": status})
    return {
        "state": "blocked" if problems else "ready",
        "ready": not problems,
        "problems": problems,
        "accounts": accounts,
        "password_change_required": False,
        "local_email_recovery_available": False,
    }


def provision_role_accounts(passwords, confirmation, *, reissue_managed=False):
    """Create each missing test account or reissue only accounts managed by this command."""
    if confirmation != PROVISION_CONFIRMATION:
        raise RuntimeError(f"confirmation must exactly equal {PROVISION_CONFIRMATION}")
    plan = build_role_account_plan()
    if not plan["ready"]:
        raise RuntimeError("role account provisioning is blocked: " + "; ".join(plan["problems"]))

    _validate_passwords(passwords)

    results = []
    for spec in ROLE_ACCOUNT_SPECS:
        existing = User.query.filter_by(email=spec["email"]).first()
        if existing:
            if reissue_managed:
                try:
                    _reissue_managed_credential(existing, passwords[spec["email"]])
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    raise
                status = "credential_reissued"
            else:
                status = "already_exists"
            results.append({"email": spec["email"], "role": spec["role"], "status": status})
            continue
        try:
            user = _create_role_account(spec, passwords[spec["email"]])
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        results.append({"email": user.email, "role": user.role, "status": "created"})

    return {
        "state": "provisioned",
        "accounts": results,
        "password_change_required": False,
        "local_email_recovery_available": False,
    }


def verify_role_accounts(passwords):
    """Verify credentials and required onboarding records without creating a login session."""
    _validate_passwords(passwords)
    results = []
    problems = []
    for spec in ROLE_ACCOUNT_SPECS:
        user = User.query.filter_by(email=spec["email"], role=spec["role"], is_active=True).one_or_none()
        if user is None:
            problems.append(f"missing active {spec['role']} account: {spec['email']}")
            continue
        state = AccountSecurity.query.filter_by(user_id=user.id).one_or_none()
        profile = RoleProfile.query.filter_by(user_id=user.id, verification_status="verified").one_or_none()
        checks = {
            "password_hash": bool(user.password_hash and verify_password(user.password_hash, passwords[user.email])),
            "direct_login": bool(state and not state.must_change_password),
            "verified_profile": profile is not None,
            "role_binding": _has_required_role_binding(user, profile),
        }
        failed = sorted(name for name, passed in checks.items() if not passed)
        if failed:
            problems.append(f"{user.email} failed: {', '.join(failed)}")
        results.append(
            {
                "email": user.email,
                "role": user.role,
                "status": "verified" if not failed else "invalid",
                "checks": checks,
            }
        )
    return {
        "state": "verified" if not problems else "blocked",
        "ready": not problems,
        "problems": problems,
        "accounts": results,
    }


def _validate_passwords(passwords):
    if not isinstance(passwords, dict):
        raise RuntimeError("temporary passwords must be supplied as an email-to-password object")
    expected_emails = {spec["email"] for spec in ROLE_ACCOUNT_SPECS}
    if set(passwords) != expected_emails:
        missing = sorted(expected_emails - set(passwords))
        unexpected = sorted(set(passwords) - expected_emails)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise RuntimeError("temporary password mapping does not match managed accounts (" + "; ".join(details) + ")")
    if len(set(passwords.values())) != len(passwords):
        raise RuntimeError("every role account requires a unique temporary password")
    for email, password in passwords.items():
        password_error = validate_password(password)
        if password_error:
            raise RuntimeError(f"temporary password for {email} does not meet policy: {password_error}")


def _has_required_role_binding(user, profile):
    if profile is None:
        return False
    if user.role == "Hospital":
        return profile.hospital_id is not None and db.session.get(Hospital, profile.hospital_id) is not None
    if user.role == "Shelter":
        return profile.shelter_id is not None and db.session.get(Shelter, profile.shelter_id) is not None
    if user.role == "Ambulance":
        return profile.ambulance_id is not None and db.session.get(Ambulance, profile.ambulance_id) is not None
    if user.role == "Volunteer":
        return Volunteer.query.filter_by(user_id=user.id).count() == 1
    return True


def _create_role_account(spec, password):
    user = User(
        name=spec["name"],
        email=spec["email"],
        phone="Not provided",
        role=spec["role"],
        password_hash=hash_password(password),
        is_active=True,
    )
    db.session.add(user)
    db.session.flush()

    db.session.add(AccountSecurity(user_id=user.id, must_change_password=False))
    profile = RoleProfile(
        user_id=user.id,
        organization_name="ResQ Command local access",
        address="Operational details must be configured before field use",
        verification_status="verified",
    )
    db.session.add(profile)

    if user.role == "Hospital":
        facility = Hospital(
            name="Unconfigured Hospital - Not Operational",
            address="Administrator configuration required",
            latitude=0,
            longitude=0,
            total_beds=0,
            available_beds=0,
            icu_beds=0,
            emergency_capacity=0,
            contact_phone="Not provided",
        )
        db.session.add(facility)
        db.session.flush()
        profile.hospital_id = facility.id
    elif user.role == "Shelter":
        facility = Shelter(
            name="Unconfigured Shelter - Not Operational",
            address="Administrator configuration required",
            latitude=0,
            longitude=0,
            total_capacity=0,
            available_capacity=0,
            food_available=False,
            medical_support=False,
            contact_phone="Not provided",
        )
        db.session.add(facility)
        db.session.flush()
        profile.shelter_id = facility.id
    elif user.role == "Ambulance":
        facility = Ambulance(
            vehicle_number="SETUP-REQUIRED-01",
            driver_name="Administrator configuration required",
            phone="Not provided",
            latitude=0,
            longitude=0,
            status="offline",
        )
        db.session.add(facility)
        db.session.flush()
        profile.ambulance_id = facility.id
    elif user.role == "Volunteer":
        db.session.add(
            Volunteer(
                user_id=user.id,
                skills="Profile setup required before assignment",
                availability_status="unavailable",
            )
        )

    db.session.add(
        AuditEvent(
            event_type="system.role_account_provision",
            user_id=user.id,
            outcome="success",
            details=f"role={user.role};test_account=true;direct_login=true",
        )
    )
    return user


def _reissue_managed_credential(user, password):
    state = AccountSecurity.query.filter_by(user_id=user.id).one_or_none()
    provision_events = AuditEvent.query.filter_by(
        event_type="system.role_account_provision",
        user_id=user.id,
        outcome="success",
    ).count()
    unsafe_state = state is None or provision_events != 1
    if unsafe_state:
        raise RuntimeError(
            f"refusing to reissue {user.email}: account is not a managed test provisioning record"
        )

    now = utcnow()
    user.password_hash = hash_password(password)
    state.failed_login_attempts = 0
    state.locked_until = None
    state.password_changed_at = now
    state.must_change_password = False
    AuthSession.query.filter_by(user_id=user.id, revoked_at=None).update(
        {AuthSession.revoked_at: now}, synchronize_session=False
    )
    PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).update(
        {PasswordResetToken.consumed_at: now}, synchronize_session=False
    )
    db.session.add(
        AuditEvent(
            event_type="system.role_account_credential_reissue",
            user_id=user.id,
            outcome="success",
            details=f"role={user.role};test_account=true;direct_login=true",
        )
    )
