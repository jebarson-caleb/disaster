import json
from datetime import timedelta

from flask import Blueprint, jsonify, request

from ..auth import (
    audit_event,
    clear_session_cookies,
    hash_password,
    login_required,
    security_state,
    session_response,
    utcnow,
    validate_password,
    verify_password,
)
from ..extensions import db, limiter
from ..mfa import (
    begin_setup,
    enabled_credential,
    generate_recovery_codes,
    issue_challenge,
    required_for,
    set_recovery_codes,
    verify_challenge,
    verify_factor,
    verify_totp,
)
from ..models import AccountSecurity, AuthSession, MfaCredential, RoleProfile, User, Volunteer

auth_bp = Blueprint("auth", __name__)

VALID_ROLES = {
    "Citizen",
    "NGO",
    "Volunteer",
    "Police",
    "Hospital",
    "Fire Service",
    "Shelter",
    "Ambulance",
    "Admin",
}
SELF_REGISTRATION_ROLES = {"Citizen", "Volunteer"}
DUMMY_PASSWORD_HASH = hash_password("TimingOnlyCredential-Not-A-Real-Login")


@auth_bp.post("/register")
@limiter.limit("5 per hour")
def register():
    data = request.get_json(silent=True) or {}
    required = ["name", "email", "phone", "role", "password"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data["role"] not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400
    if data["role"] not in SELF_REGISTRATION_ROLES:
        return jsonify({"error": "This operational role requires administrator provisioning"}), 403
    email = str(data["email"]).strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1] or len(email) > 160:
        return jsonify({"error": "A valid email address is required"}), 400
    password_error = validate_password(data["password"])
    if password_error:
        return jsonify({"error": password_error}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    requires_verification = data["role"] == "Volunteer"
    user = User(
        name=str(data["name"]).strip()[:120],
        email=email,
        phone=str(data["phone"]).strip()[:30],
        role=data["role"],
        password_hash=hash_password(data["password"]),
        is_active=not requires_verification,
    )
    db.session.add(user)
    db.session.flush()
    db.session.add(
        RoleProfile(
            user_id=user.id,
            organization_name=str(data.get("organization_name") or "")[:160] or None,
            address=str(data.get("address") or "")[:255] or None,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
    )
    security_state(user)
    if user.role == "Volunteer":
        db.session.add(
            Volunteer(
                user_id=user.id,
                skills=str(data.get("skills") or "general relief support")[:255],
                availability_status="pending verification",
                latitude=float(data["latitude"]) if data.get("latitude") not in {None, ""} else None,
                longitude=float(data["longitude"]) if data.get("longitude") not in {None, ""} else None,
            )
        )
    if requires_verification:
        audit_event("account.register", "pending_verification", user.id)
        db.session.commit()
        return (
            jsonify(
                {
                    "user": public_user(user),
                    "pending_verification": True,
                    "message": "Volunteer registration submitted for administrator verification.",
                }
            ),
            202,
        )
    response = session_response(user, 201)
    audit_event("account.register", "success", user.id)
    db.session.commit()
    return response


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    user = User.query.filter_by(email=email).first() if email else None

    # Perform a password hash operation even when the account does not exist.
    password_valid = verify_password(user.password_hash if user else DUMMY_PASSWORD_HASH, password)
    if user is None or not user.is_active:
        audit_event("account.login", "failure", details="invalid_credentials")
        db.session.commit()
        return jsonify({"error": "Invalid email or password"}), 401

    state = security_state(user)
    now = utcnow()
    locked_until = state.locked_until
    if locked_until is not None and (locked_until.replace(tzinfo=now.tzinfo) if locked_until.tzinfo is None else locked_until) > now:
        audit_event("account.login", "blocked", user.id, "account_locked")
        db.session.commit()
        return jsonify({"error": "Account temporarily locked. Try again later."}), 429

    if not password_valid:
        state.failed_login_attempts += 1
        if state.failed_login_attempts >= 5:
            state.locked_until = now + timedelta(minutes=15)
            state.failed_login_attempts = 0
        audit_event("account.login", "failure", user.id, "invalid_credentials")
        db.session.commit()
        return jsonify({"error": "Invalid email or password"}), 401

    state.failed_login_attempts = 0
    state.locked_until = None
    state.last_login_at = now
    if enabled_credential(user.id):
        _, challenge_token = issue_challenge(user)
        audit_event("account.login", "mfa_required", user.id)
        db.session.commit()
        return (
            jsonify(
                {
                    "mfa_required": True,
                    "challenge_token": challenge_token,
                    "message": "Enter a code from your authenticator or a recovery code.",
                }
            ),
            202,
        )

    mfa_state = "setup_required" if required_for(user) else "not_required"
    response = session_response(user, mfa_state=mfa_state)
    audit_event("account.login", "mfa_setup_required" if mfa_state == "setup_required" else "success", user.id)
    db.session.commit()
    return response


@auth_bp.post("/mfa/challenge")
@limiter.limit("10 per minute")
def complete_mfa_login():
    data = request.get_json(silent=True) or {}
    challenge, factor = verify_challenge(data.get("challenge_token"), data.get("code"))
    if challenge is None or factor is None:
        audit_event(
            "account.mfa_challenge",
            "failure",
            challenge.user_id if challenge else None,
            "invalid_or_expired_challenge",
        )
        db.session.commit()
        return jsonify({"error": "Invalid or expired verification code"}), 401

    user = db.session.get(User, challenge.user_id)
    if user is None or not user.is_active:
        audit_event("account.mfa_challenge", "failure", challenge.user_id, "inactive_account")
        db.session.commit()
        return jsonify({"error": "Invalid or expired verification code"}), 401

    response = session_response(user, mfa_state="verified")
    audit_event("account.login", "success", user.id, f"mfa_factor={factor}")
    db.session.commit()
    return response


@auth_bp.get("/me")
@login_required()
def me():
    user_payload = public_user(request.user)
    return jsonify(
        {
            "user": user_payload,
            "password_change_required": user_payload["password_change_required"],
            "mfa_setup_required": request.auth_session.mfa_state == "setup_required",
            "mfa_verified": request.auth_session.mfa_state == "verified",
        }
    )


@auth_bp.get("/mfa/status")
@login_required()
def mfa_status():
    credential = enabled_credential(request.user.id)
    recovery_count = len(json.loads(credential.recovery_code_hashes or "[]")) if credential else 0
    return jsonify(
        {
            "required": required_for(request.user),
            "enabled": credential is not None,
            "verified": request.auth_session.mfa_state == "verified",
            "setup_required": request.auth_session.mfa_state == "setup_required",
            "recovery_codes_remaining": recovery_count,
        }
    )


@auth_bp.post("/mfa/setup")
@login_required()
@limiter.limit("5 per hour")
def begin_mfa_setup():
    data = request.get_json(silent=True) or {}
    if not verify_password(request.user.password_hash, str(data.get("current_password", ""))):
        audit_event("account.mfa_setup", "failure", request.user.id, "invalid_current_password")
        db.session.commit()
        return jsonify({"error": "Current password is incorrect"}), 401
    try:
        _, secret, provisioning_uri = begin_setup(request.user)
    except ValueError as error:
        return jsonify({"error": str(error)}), 409
    audit_event("account.mfa_setup", "pending", request.user.id)
    db.session.commit()
    return jsonify({"secret": secret, "provisioning_uri": provisioning_uri})


@auth_bp.post("/mfa/confirm")
@login_required()
@limiter.limit("10 per hour")
def confirm_mfa_setup():
    credential = MfaCredential.query.filter_by(user_id=request.user.id, enabled_at=None).first()
    code = (request.get_json(silent=True) or {}).get("code")
    if credential is None or not verify_totp(credential, code):
        audit_event("account.mfa_setup", "failure", request.user.id, "invalid_confirmation_code")
        db.session.commit()
        return jsonify({"error": "Invalid verification code"}), 400

    recovery_codes = generate_recovery_codes()
    set_recovery_codes(credential, recovery_codes)
    credential.enabled_at = utcnow()
    request.auth_session.mfa_state = "verified"
    AuthSession.query.filter(
        AuthSession.user_id == request.user.id,
        AuthSession.id != request.auth_session.id,
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: utcnow()}, synchronize_session=False)
    audit_event("account.mfa_setup", "success", request.user.id)
    db.session.commit()
    return jsonify(
        {
            "message": "Multi-factor authentication enabled. Store these recovery codes securely.",
            "recovery_codes": recovery_codes,
        }
    )


@auth_bp.post("/mfa/recovery-codes")
@login_required()
@limiter.limit("3 per hour")
def regenerate_mfa_recovery_codes():
    data = request.get_json(silent=True) or {}
    credential = enabled_credential(request.user.id)
    if (
        credential is None
        or not verify_password(request.user.password_hash, str(data.get("current_password", "")))
        or verify_factor(credential, data.get("code")) is None
    ):
        audit_event("account.mfa_recovery_codes", "failure", request.user.id)
        db.session.commit()
        return jsonify({"error": "Password or verification code is incorrect"}), 401
    recovery_codes = generate_recovery_codes()
    set_recovery_codes(credential, recovery_codes)
    audit_event("account.mfa_recovery_codes", "success", request.user.id)
    db.session.commit()
    return jsonify({"recovery_codes": recovery_codes})


@auth_bp.post("/mfa/disable")
@login_required()
@limiter.limit("3 per hour")
def disable_mfa():
    data = request.get_json(silent=True) or {}
    credential = enabled_credential(request.user.id)
    if (
        credential is None
        or not verify_password(request.user.password_hash, str(data.get("current_password", "")))
        or verify_factor(credential, data.get("code")) is None
    ):
        audit_event("account.mfa_disable", "failure", request.user.id)
        db.session.commit()
        return jsonify({"error": "Password or verification code is incorrect"}), 401
    db.session.delete(credential)
    request.auth_session.mfa_state = "setup_required" if required_for(request.user) else "not_required"
    AuthSession.query.filter(
        AuthSession.user_id == request.user.id,
        AuthSession.id != request.auth_session.id,
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: utcnow()}, synchronize_session=False)
    audit_event("account.mfa_disable", "success", request.user.id)
    db.session.commit()
    return jsonify(
        {
            "message": "Multi-factor authentication disabled",
            "setup_required": request.auth_session.mfa_state == "setup_required",
        }
    )


@auth_bp.post("/logout")
@login_required()
def logout():
    request.auth_session.revoked_at = utcnow()
    audit_event("account.logout", "success", request.user.id)
    db.session.commit()
    response = jsonify({"message": "Signed out"})
    response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
    return clear_session_cookies(response)


@auth_bp.post("/change-password")
@login_required()
@limiter.limit("5 per hour")
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = str(data.get("current_password", ""))
    new_password = str(data.get("new_password", ""))
    if not verify_password(request.user.password_hash, current_password):
        audit_event("account.password_change", "failure", request.user.id, "invalid_current_password")
        db.session.commit()
        return jsonify({"error": "Current password is incorrect"}), 401
    password_error = validate_password(new_password)
    if password_error:
        return jsonify({"error": password_error}), 400
    if verify_password(request.user.password_hash, new_password):
        return jsonify({"error": "New password must be different from the current password"}), 400

    request.user.password_hash = hash_password(new_password)
    state = security_state(request.user)
    state.password_changed_at = utcnow()
    state.must_change_password = False
    AuthSession.query.filter(
        AuthSession.user_id == request.user.id,
        AuthSession.id != request.auth_session.id,
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: utcnow()}, synchronize_session=False)
    request.auth_session.revoked_at = utcnow()
    response = session_response(request.user, mfa_state=request.auth_session.mfa_state)
    audit_event("account.password_change", "success", request.user.id)
    db.session.commit()
    return response


@auth_bp.get("/sessions")
@login_required()
def sessions():
    now = utcnow()
    items = AuthSession.query.filter_by(user_id=request.user.id, revoked_at=None).order_by(AuthSession.created_at.desc()).all()
    return jsonify(
        {
            "sessions": [
                {
                    "id": item.id,
                    "created_at": item.created_at.isoformat(),
                    "last_seen_at": item.last_seen_at.isoformat(),
                    "expires_at": item.absolute_expires_at.isoformat(),
                    "user_agent": item.user_agent,
                    "current": item.id == request.auth_session.id,
                }
                for item in items
                if (item.absolute_expires_at.replace(tzinfo=now.tzinfo) if item.absolute_expires_at.tzinfo is None else item.absolute_expires_at) > now
            ]
        }
    )


@auth_bp.delete("/sessions/<int:session_id>")
@login_required()
def revoke_session(session_id):
    auth_session = AuthSession.query.filter_by(id=session_id, user_id=request.user.id).first_or_404()
    auth_session.revoked_at = utcnow()
    audit_event("account.session_revoke", "success", request.user.id, f"session_id={session_id}")
    db.session.commit()
    response = jsonify({"message": "Session revoked"})
    if auth_session.id == request.auth_session.id:
        clear_session_cookies(response)
    return response


def public_user(user):
    profile = RoleProfile.query.filter_by(user_id=user.id).first()
    state = AccountSecurity.query.filter_by(user_id=user.id).first()
    managed_facility = None
    if profile and profile.hospital_id:
        managed_facility = {"type": "hospital", "id": profile.hospital_id}
    elif profile and profile.shelter_id:
        managed_facility = {"type": "shelter", "id": profile.shelter_id}
    elif profile and profile.ambulance_id:
        managed_facility = {"type": "ambulance", "id": profile.ambulance_id}
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat(),
        "verification_status": profile.verification_status if profile else "verified",
        "mfa_enabled": enabled_credential(user.id) is not None,
        "mfa_required": required_for(user),
        "password_change_required": bool(state and state.must_change_password),
        "managed_facility": managed_facility,
    }
