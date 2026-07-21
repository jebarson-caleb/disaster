from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..auth import audit_event, hash_password, login_required, security_state, utcnow, validate_password, verify_password
from ..extensions import db, limiter
from ..models import AuthSession, Ambulance, Disaster, Hospital, RescueRequest, Resource, RoleProfile, Shelter, User, Volunteer
from .auth import VALID_ROLES, public_user

admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/users")
@login_required(roles=["Admin"])
@limiter.limit("30 per hour")
def provision_user():
    data = request.get_json() or {}
    required = ["name", "email", "phone", "role", "password"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data["role"] not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400
    email = str(data["email"]).strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return jsonify({"error": "A valid email address is required"}), 400
    password_error = validate_password(data["password"])
    if password_error:
        return jsonify({"error": password_error}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=str(data["name"]).strip(),
        email=email,
        phone=str(data["phone"]).strip(),
        role=data["role"],
        password_hash=hash_password(data["password"]),
    )
    db.session.add(user)
    db.session.flush()
    security_state(user)
    db.session.add(
        RoleProfile(
            user_id=user.id,
            organization_name=data.get("organization_name"),
            address=data.get("address"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            verification_status="verified",
        )
    )
    if user.role == "Volunteer":
        db.session.add(
            Volunteer(
                user_id=user.id,
                skills=str(data.get("skills") or "general relief support"),
                availability_status="available",
                latitude=float(data["latitude"]) if data.get("latitude") not in {None, ""} else None,
                longitude=float(data["longitude"]) if data.get("longitude") not in {None, ""} else None,
            )
        )
    audit_event("admin.user_provision", "success", request.user.id, f"target_user_id={user.id};role={user.role}")
    db.session.commit()
    return jsonify({"user": managed_user(user)}), 201


@admin_bp.get("/users")
@login_required(roles=["Admin"])
def list_users():
    users = User.query.order_by(User.created_at.desc()).limit(500).all()
    return jsonify({"users": [managed_user(user) for user in users]})


@admin_bp.patch("/users/<int:user_id>")
@login_required(roles=["Admin"])
def update_user_access(user_id):
    target = db.get_or_404(User, user_id)
    data = request.get_json(silent=True) or {}
    if target.id == request.user.id and (
        data.get("is_active") is False or str(data.get("verification_status", "")).lower() in {"pending", "rejected"}
    ):
        return jsonify({"error": "You cannot deactivate your own administrator account"}), 400

    profile = RoleProfile.query.filter_by(user_id=target.id).first()
    if profile is None:
        profile = RoleProfile(user_id=target.id, verification_status="verified")
        db.session.add(profile)
    if "verification_status" in data:
        status = str(data["verification_status"]).strip().lower()
        if status not in {"pending", "verified", "rejected"}:
            return jsonify({"error": "verification_status must be pending, verified, or rejected"}), 400
        profile.verification_status = status
        if status == "verified":
            target.is_active = True
            volunteer = Volunteer.query.filter_by(user_id=target.id).first()
            if volunteer and volunteer.availability_status == "pending verification":
                volunteer.availability_status = "available"
        elif status == "rejected":
            target.is_active = False
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        target.is_active = data["is_active"]

    if not target.is_active:
        AuthSession.query.filter_by(user_id=target.id, revoked_at=None).update(
            {AuthSession.revoked_at: utcnow()}, synchronize_session=False
        )
    audit_event("admin.user_access_update", "success", request.user.id, f"target_user_id={target.id}")
    db.session.commit()
    return jsonify({"user": managed_user(target)})


@admin_bp.post("/users/<int:user_id>/reset-password")
@login_required(roles=["Admin"])
@limiter.limit("10 per hour")
def reset_user_password(user_id):
    target = db.get_or_404(User, user_id)
    data = request.get_json(silent=True) or {}
    if target.id == request.user.id:
        return jsonify({"error": "Use the account password-change form for your own password"}), 400
    if not verify_password(request.user.password_hash, str(data.get("admin_password", ""))):
        audit_event("admin.password_reset", "failure", request.user.id, f"target_user_id={target.id}")
        db.session.commit()
        return jsonify({"error": "Administrator password is incorrect"}), 401
    password_error = validate_password(data.get("new_password"))
    if password_error:
        return jsonify({"error": password_error}), 400

    target.password_hash = hash_password(str(data["new_password"]))
    state = security_state(target)
    state.password_changed_at = utcnow()
    state.failed_login_attempts = 0
    state.locked_until = None
    AuthSession.query.filter_by(user_id=target.id, revoked_at=None).update(
        {AuthSession.revoked_at: utcnow()}, synchronize_session=False
    )
    audit_event("admin.password_reset", "success", request.user.id, f"target_user_id={target.id}")
    db.session.commit()
    return jsonify({"message": "Password reset and active sessions revoked"})


def managed_user(user):
    profile = RoleProfile.query.filter_by(user_id=user.id).first()
    return {
        **public_user(user),
        "organization_name": profile.organization_name if profile else None,
        "verification_status": profile.verification_status if profile else "verified",
    }


@admin_bp.get("/dashboard")
@login_required(roles=["Admin", "Police", "Fire Service", "NGO"])
def dashboard():
    metrics = {
        "active_disasters": Disaster.query.filter_by(status="active").count(),
        "pending_rescues": RescueRequest.query.filter_by(status="pending").count(),
        "available_ambulances": Ambulance.query.filter_by(status="available").count(),
        "available_hospital_beds": sum(value or 0 for (value,) in Hospital.query.with_entities(Hospital.available_beds).all()),
        "available_shelter_capacity": sum(value or 0 for (value,) in Shelter.query.with_entities(Shelter.available_capacity).all()),
        "available_volunteers": Volunteer.query.filter_by(availability_status="available").count(),
        "resource_units": sum(value or 0 for (value,) in Resource.query.with_entities(Resource.available_quantity).all()),
    }
    recent_disasters = Disaster.query.order_by(Disaster.created_at.desc()).limit(10).all()
    urgent_requests = RescueRequest.query.order_by(RescueRequest.priority_score.desc()).limit(10).all()
    return jsonify(
        {
            "metrics": metrics,
            "recent_disasters": [item.to_dict() for item in recent_disasters],
            "urgent_requests": [item.to_dict() for item in urgent_requests],
        }
    )


@admin_bp.get("/analytics")
@login_required(roles=["Admin", "Police", "Fire Service", "NGO"])
def analytics():
    disasters_by_type = Disaster.query.with_entities(Disaster.disaster_type, func.count(Disaster.id)).group_by(Disaster.disaster_type).all()
    rescues_by_status = RescueRequest.query.with_entities(RescueRequest.status, func.count(RescueRequest.id)).group_by(RescueRequest.status).all()
    rescues_by_priority = RescueRequest.query.with_entities(RescueRequest.priority_label, func.count(RescueRequest.id)).group_by(RescueRequest.priority_label).all()
    return jsonify(
        {
            "disasters_by_type": dict(disasters_by_type),
            "rescues_by_status": dict(rescues_by_status),
            "rescues_by_priority": dict(rescues_by_priority),
        }
    )
