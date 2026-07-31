import secrets
import smtplib
from datetime import timedelta
from math import isfinite

from flask import Blueprint, current_app, jsonify, request

from ..auth import (
    as_utc,
    audit_event,
    authenticated_rate_key,
    clear_session_cookies,
    digest,
    hash_password,
    login_required,
    security_state,
    session_response,
    utcnow,
    validate_password,
    verify_password,
)
from ..extensions import db, limiter
from ..models import (
    AccountSecurity,
    AuthSession,
    MfaChallenge,
    PasswordResetToken,
    RoleProfile,
    User,
    Volunteer,
)
from ..services.email_service import password_recovery_available, send_password_reset_email

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
    if not _valid_email(email):
        return jsonify({"error": "A valid email address is required"}), 400
    password_error = validate_password(data["password"])
    if password_error:
        return jsonify({"error": password_error}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    name = str(data["name"]).strip()
    phone = str(data["phone"]).strip()
    if not name:
        return jsonify({"error": "Name must not be blank"}), 400
    if not phone:
        return jsonify({"error": "Phone must not be blank"}), 400
    try:
        latitude = _optional_coordinate(data.get("latitude"), "latitude", -90, 90)
        longitude = _optional_coordinate(data.get("longitude"), "longitude", -180, 180)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if (latitude is None) != (longitude is None):
        return jsonify({"error": "Latitude and longitude must be supplied together"}), 400

    requires_verification = data["role"] == "Volunteer"
    user = User(
        name=name[:120],
        email=email,
        phone=phone[:30],
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
            latitude=latitude,
            longitude=longitude,
        )
    )
    security_state(user)
    if user.role == "Volunteer":
        db.session.add(
            Volunteer(
                user_id=user.id,
                skills=str(data.get("skills") or "general relief support")[:255],
                availability_status="pending verification",
                latitude=latitude,
                longitude=longitude,
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


@auth_bp.post("/password-reset/request")
@limiter.limit("3 per hour")
def request_password_reset():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    if not _valid_email(email):
        return jsonify({"error": "A valid email address is required"}), 400

    available = password_recovery_available()
    user = User.query.filter_by(email=email, is_active=True).first()
    if available and user is not None:
        now = utcnow()
        PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).update(
            {PasswordResetToken.consumed_at: now},
            synchronize_session=False,
        )
        raw_token = secrets.token_urlsafe(48)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=digest(raw_token),
            created_at=now,
            expires_at=now + timedelta(minutes=current_app.config["PASSWORD_RESET_MINUTES"]),
        )
        db.session.add(reset_token)
        audit_event("account.password_reset_request", "queued", user.id)
        db.session.commit()
        try:
            send_password_reset_email(user, raw_token)
        except (OSError, RuntimeError, ValueError, smtplib.SMTPException):
            current_app.logger.exception(
                "Password reset email delivery failed for user_id=%s",
                user.id,
            )
            reset_token.consumed_at = utcnow()
            audit_event("account.password_reset_request", "delivery_failed", user.id)
            db.session.commit()
        else:
            audit_event("account.password_reset_request", "delivered", user.id)
            db.session.commit()

    message = (
        "If an active account matches that email, a single-use reset link will be sent."
        if available
        else "Email recovery is not currently available. Ask a ResQ administrator to verify your identity and reset the account."
    )
    return jsonify({"message": message, "recovery_available": available}), 202


@auth_bp.post("/password-reset/complete")
@limiter.limit("10 per hour")
def complete_password_reset():
    data = request.get_json(silent=True) or {}
    raw_token = str(data.get("token") or "")
    new_password = str(data.get("new_password") or "")
    if not raw_token or not new_password:
        return jsonify({"error": "token and new_password are required"}), 400
    password_error = validate_password(new_password)
    if password_error:
        return jsonify({"error": password_error}), 400
    if len(raw_token) > 256:
        return jsonify({"error": "Invalid or expired password reset link"}), 400

    reset_token = PasswordResetToken.query.filter_by(token_hash=digest(raw_token)).first()
    now = utcnow()
    if reset_token is None or reset_token.consumed_at is not None or as_utc(reset_token.expires_at) <= now:
        return jsonify({"error": "Invalid or expired password reset link"}), 400
    user = db.session.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        reset_token.consumed_at = now
        db.session.commit()
        return jsonify({"error": "Invalid or expired password reset link"}), 400

    claimed = PasswordResetToken.query.filter(
        PasswordResetToken.id == reset_token.id,
        PasswordResetToken.consumed_at.is_(None),
        PasswordResetToken.expires_at > now,
    ).update(
        {PasswordResetToken.consumed_at: now},
        synchronize_session=False,
    )
    if claimed != 1:
        db.session.rollback()
        return jsonify({"error": "Invalid or expired password reset link"}), 400

    user.password_hash = hash_password(new_password)
    state = security_state(user)
    state.password_changed_at = now
    state.must_change_password = False
    state.failed_login_attempts = 0
    state.locked_until = None
    AuthSession.query.filter_by(user_id=user.id, revoked_at=None).update(
        {AuthSession.revoked_at: now},
        synchronize_session=False,
    )
    MfaChallenge.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    PasswordResetToken.query.filter_by(user_id=user.id, consumed_at=None).update(
        {PasswordResetToken.consumed_at: now},
        synchronize_session=False,
    )
    audit_event("account.password_reset_complete", "success", user.id)
    db.session.commit()
    return jsonify({"message": "Password reset. Sign in with the new password."})


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
    response = session_response(user)
    audit_event("account.login", "success", user.id)
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
@limiter.limit("5 per hour", key_func=authenticated_rate_key)
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
    MfaChallenge.query.filter_by(user_id=request.user.id).delete(synchronize_session=False)
    request.auth_session.revoked_at = utcnow()
    response = session_response(request.user)
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
        response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
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
        "password_change_required": bool(state and state.must_change_password),
        "managed_facility": managed_facility,
    }


def _optional_coordinate(value, name, minimum, maximum):
    if value in {None, ""}:
        return None
    try:
        coordinate = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number") from error
    if not isfinite(coordinate) or not minimum <= coordinate <= maximum:
        raise ValueError(f"{name} is outside valid bounds")
    return coordinate


def _valid_email(value):
    email = str(value or "")
    if len(email) > 160 or any(character.isspace() for character in email):
        return False
    local, separator, domain = email.rpartition("@")
    return bool(separator and local and "." in domain and not domain.startswith(".") and not domain.endswith("."))
