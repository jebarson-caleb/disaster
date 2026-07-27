import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from functools import wraps
from uuid import uuid4

import jwt
from flask import current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import AccountSecurity, AuditEvent, AuthSession, User

COMMON_PASSWORDS = {
    "123456789",
    "admin123456789",
    "password123",
    "password1234",
    "qwerty123456",
}


def utcnow():
    return datetime.now(UTC)


def as_utc(value):
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_password(password):
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash, password):
    try:
        return check_password_hash(password_hash, password)
    except (TypeError, ValueError):
        return False


def validate_password(password):
    password = str(password or "")
    if len(password) < 15:
        return "Password must contain at least 15 characters"
    if len(password) > 128:
        return "Password must not exceed 128 characters"
    if password.casefold() in COMMON_PASSWORDS:
        return "Choose a less common password"
    return None


def create_token(user, auth_session):
    now = utcnow()
    payload = {
        "sub": str(user.id),
        "sid": str(auth_session.id),
        "role": user.role,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=current_app.config["ACCESS_TOKEN_MINUTES"]),
        "iss": current_app.config["JWT_ISSUER"],
        "aud": current_app.config["JWT_AUDIENCE"],
        "jti": uuid4().hex,
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def create_session(user, mfa_state=None):
    from .mfa import required_for

    now = utcnow()
    raw_token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=digest(raw_token),
        csrf_hash=digest(csrf_token),
        user_agent=request.user_agent.string[:255] if request.user_agent else None,
        created_at=now,
        last_seen_at=now,
        idle_expires_at=now + timedelta(minutes=current_app.config["SESSION_IDLE_MINUTES"]),
        absolute_expires_at=now + timedelta(hours=current_app.config["SESSION_ABSOLUTE_HOURS"]),
        mfa_state=mfa_state or ("setup_required" if required_for(user) else "not_required"),
    )
    db.session.add(auth_session)
    db.session.flush()
    return auth_session, raw_token, csrf_token, create_token(user, auth_session)


def set_session_cookies(response, raw_token, csrf_token):
    common = {
        "secure": current_app.config["SESSION_COOKIE_SECURE"],
        "samesite": current_app.config["SESSION_COOKIE_SAMESITE"],
        "path": "/",
        "max_age": current_app.config["SESSION_ABSOLUTE_HOURS"] * 3600,
    }
    response.set_cookie(current_app.config["SESSION_COOKIE_NAME"], raw_token, httponly=True, **common)
    response.set_cookie(current_app.config["CSRF_COOKIE_NAME"], csrf_token, httponly=False, **common)
    return response


def clear_session_cookies(response):
    for name in (current_app.config["SESSION_COOKIE_NAME"], current_app.config["CSRF_COOKIE_NAME"]):
        response.delete_cookie(
            name,
            path="/",
            secure=current_app.config["SESSION_COOKIE_SECURE"],
            samesite=current_app.config["SESSION_COOKIE_SAMESITE"],
        )
    return response


def session_response(user, status=200, mfa_state=None):
    from .routes.auth import public_user

    auth_session, raw_token, csrf_token, access_token = create_session(user, mfa_state=mfa_state)
    user_payload = public_user(user)
    response = jsonify(
        {
            "user": user_payload,
            "token": access_token,
            "password_change_required": user_payload["password_change_required"],
            "mfa_setup_required": auth_session.mfa_state == "setup_required",
            "mfa_verified": auth_session.mfa_state == "verified",
        }
    )
    response.status_code = status
    return set_session_cookies(response, raw_token, csrf_token)


def _active_session_from_request():
    cached = request.environ.get("resq.auth_context")
    if cached is not None:
        return cached

    auth_session = None
    user_id = None
    method = None
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        token = header.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
                issuer=current_app.config["JWT_ISSUER"],
                audience=current_app.config["JWT_AUDIENCE"],
                options={"require": ["sub", "sid", "iat", "nbf", "exp", "iss", "aud", "jti"]},
            )
            auth_session = db.session.get(AuthSession, int(payload["sid"]))
            user_id = int(payload["sub"])
            method = "bearer"
        except (jwt.PyJWTError, TypeError, ValueError):
            auth_session = None
    else:
        raw_token = request.cookies.get(current_app.config["SESSION_COOKIE_NAME"], "")
        if raw_token:
            auth_session = AuthSession.query.filter_by(token_hash=digest(raw_token)).first()
            user_id = auth_session.user_id if auth_session else None
            method = "cookie"

    now = utcnow()
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.user_id != user_id
        or as_utc(auth_session.idle_expires_at) <= now
        or as_utc(auth_session.absolute_expires_at) <= now
    ):
        request.environ["resq.auth_context"] = (None, None, method)
        return request.environ["resq.auth_context"]

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        request.environ["resq.auth_context"] = (None, None, method)
        return request.environ["resq.auth_context"]

    last_seen = as_utc(auth_session.last_seen_at)
    if now - last_seen >= timedelta(minutes=5):
        auth_session.last_seen_at = now
        auth_session.idle_expires_at = min(
            now + timedelta(minutes=current_app.config["SESSION_IDLE_MINUTES"]),
            as_utc(auth_session.absolute_expires_at),
        )
        db.session.commit()
    request.environ["resq.auth_context"] = (user, auth_session, method)
    return request.environ["resq.auth_context"]


def current_user():
    return _active_session_from_request()[0]


def current_auth_session():
    return _active_session_from_request()[1]


def enforce_csrf():
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return None
    if request.endpoint in {"auth.login", "auth.register", "auth.complete_mfa_login", "operations.demo_session"}:
        return None
    if request.headers.get("Authorization", "").startswith("Bearer "):
        return None
    if not request.cookies.get(current_app.config["SESSION_COOKIE_NAME"]):
        return None
    _, auth_session, method = _active_session_from_request()
    if method != "cookie" or auth_session is None:
        return jsonify({"error": "Authentication required"}), 401
    cookie_token = request.cookies.get(current_app.config["CSRF_COOKIE_NAME"], "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        return jsonify({"error": "CSRF validation failed"}), 403
    if not hmac.compare_digest(auth_session.csrf_hash, digest(header_token)):
        return jsonify({"error": "CSRF validation failed"}), 403
    return None


def audit_event(event_type, outcome, user_id=None, details=None):
    db.session.add(
        AuditEvent(
            event_type=event_type,
            user_id=user_id,
            outcome=outcome,
            request_id=getattr(g, "request_id", None),
            details=str(details)[:500] if details else None,
        )
    )


def security_state(user):
    state = AccountSecurity.query.filter_by(user_id=user.id).first()
    if state is None:
        state = AccountSecurity(user_id=user.id)
        db.session.add(state)
        db.session.flush()
    return state


def login_required(roles=None):
    allowed = set(roles or [])

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                return jsonify({"error": "Authentication required"}), 401
            if allowed and user.role not in allowed:
                return jsonify({"error": "Forbidden for this role"}), 403
            request.user = user
            request.auth_session = current_auth_session()
            password_change_endpoints = {
                "auth.me",
                "auth.logout",
                "auth.change_password",
            }
            state = AccountSecurity.query.filter_by(user_id=user.id).first()
            if state and state.must_change_password and request.endpoint not in password_change_endpoints:
                return (
                    jsonify(
                        {
                            "error": "A password change is required before operational access",
                            "code": "password_change_required",
                        }
                    ),
                    403,
                )
            enrollment_endpoints = {
                "auth.me",
                "auth.logout",
                "auth.change_password",
                "auth.mfa_status",
                "auth.begin_mfa_setup",
                "auth.confirm_mfa_setup",
            }
            if request.auth_session.mfa_state == "setup_required" and request.endpoint not in enrollment_endpoints:
                return (
                    jsonify(
                        {
                            "error": "Multi-factor authentication setup is required",
                            "code": "mfa_setup_required",
                        }
                    ),
                    403,
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
