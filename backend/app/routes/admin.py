from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..auth import (
    audit_event,
    authenticated_rate_key,
    hash_password,
    login_required,
    security_state,
    utcnow,
    validate_password,
    verify_password,
)
from ..extensions import db, limiter
from ..mfa import enabled_credential, required_for
from ..models import (
    Ambulance,
    AuthSession,
    Disaster,
    DonationCampaign,
    Hospital,
    MfaChallenge,
    MfaCredential,
    RescueRequest,
    Resource,
    ResponderUnit,
    RoleProfile,
    Shelter,
    User,
    Volunteer,
)
from .auth import VALID_ROLES, public_user

admin_bp = Blueprint("admin", __name__)
FACILITY_ROLE_MODELS = {
    "Hospital": Hospital,
    "Shelter": Shelter,
    "Ambulance": Ambulance,
}


@admin_bp.post("/users")
@login_required(roles=["Admin"])
@limiter.limit("30 per hour", key_func=authenticated_rate_key)
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
    try:
        profile_latitude = _optional_float(data.get("latitude"), "latitude")
        profile_longitude = _optional_float(data.get("longitude"), "longitude")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    user = User(
        name=str(data["name"]).strip()[:120],
        email=email,
        phone=str(data["phone"]).strip()[:30],
        role=data["role"],
        password_hash=hash_password(data["password"]),
    )
    db.session.add(user)
    db.session.flush()
    security_state(user).must_change_password = True
    profile = RoleProfile(
        user_id=user.id,
        organization_name=str(data.get("organization_name") or "").strip()[:160] or None,
        address=str(data.get("address") or "").strip()[:255] or None,
        latitude=profile_latitude,
        longitude=profile_longitude,
        verification_status="verified",
    )
    db.session.add(profile)
    facility = None
    if user.role in FACILITY_ROLE_MODELS:
        try:
            facility = _assign_or_create_facility(user.role, data)
        except ValueError as error:
            db.session.rollback()
            return jsonify({"error": str(error)}), 400
        if user.role == "Hospital":
            profile.hospital_id = facility.id
        elif user.role == "Shelter":
            profile.shelter_id = facility.id
        else:
            profile.ambulance_id = facility.id
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
    return jsonify({"user": managed_user(user), "facility": facility.to_dict() if facility else None}), 201


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
@limiter.limit("10 per hour", key_func=authenticated_rate_key)
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
    state.must_change_password = True
    state.failed_login_attempts = 0
    state.locked_until = None
    AuthSession.query.filter_by(user_id=target.id, revoked_at=None).update(
        {AuthSession.revoked_at: utcnow()}, synchronize_session=False
    )
    audit_event("admin.password_reset", "success", request.user.id, f"target_user_id={target.id}")
    db.session.commit()
    return jsonify({"message": "Password reset and active sessions revoked"})


@admin_bp.post("/users/<int:user_id>/reset-mfa")
@login_required(roles=["Admin"])
@limiter.limit("10 per hour", key_func=authenticated_rate_key)
def reset_user_mfa(user_id):
    target = db.get_or_404(User, user_id)
    data = request.get_json(silent=True) or {}
    if target.id == request.user.id:
        return jsonify({"error": "Use the account security panel to manage your own MFA"}), 400
    if not verify_password(request.user.password_hash, str(data.get("admin_password", ""))):
        audit_event("admin.mfa_reset", "failure", request.user.id, f"target_user_id={target.id}")
        db.session.commit()
        return jsonify({"error": "Administrator password is incorrect"}), 401

    credential = MfaCredential.query.filter_by(user_id=target.id).first()
    MfaChallenge.query.filter_by(user_id=target.id).delete(synchronize_session=False)
    if credential is not None:
        db.session.delete(credential)
    AuthSession.query.filter_by(user_id=target.id, revoked_at=None).update(
        {AuthSession.revoked_at: utcnow()}, synchronize_session=False
    )
    audit_event(
        "admin.mfa_reset",
        "success",
        request.user.id,
        f"target_user_id={target.id};credential_removed={credential is not None}",
    )
    db.session.commit()
    return jsonify(
        {
            "message": "MFA reset and active sessions revoked",
            "mfa_reset": credential is not None,
            "mfa_setup_required": required_for(target),
            "user": managed_user(target),
        }
    )


@admin_bp.post("/resources")
@login_required(roles=["Admin"])
@limiter.limit("60 per hour", key_func=authenticated_rate_key)
def create_resource():
    data = request.get_json(silent=True) or {}
    missing = [
        field
        for field in ["name", "category", "unit", "available_quantity", "storage_location"]
        if data.get(field) in {None, ""}
    ]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    try:
        quantity = int(data["available_quantity"])
    except (TypeError, ValueError):
        return jsonify({"error": "available_quantity must be a whole number"}), 400
    if quantity < 0:
        return jsonify({"error": "available_quantity must not be negative"}), 400
    resource = Resource(
        name=str(data["name"]).strip()[:120],
        category=str(data["category"]).strip().lower()[:60],
        unit=str(data["unit"]).strip()[:30],
        available_quantity=quantity,
        storage_location=str(data["storage_location"]).strip()[:160],
    )
    db.session.add(resource)
    audit_event("admin.resource_create", "success", request.user.id)
    db.session.commit()
    return jsonify({"resource": resource.to_dict()}), 201


@admin_bp.post("/responders")
@login_required(roles=["Admin"])
@limiter.limit("60 per hour", key_func=authenticated_rate_key)
def create_responder():
    data = request.get_json(silent=True) or {}
    required = ["name", "unit_type", "skills", "contact_phone", "latitude", "longitude"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    name = str(data["name"]).strip()[:160]
    if ResponderUnit.query.filter_by(name=name).first():
        return jsonify({"error": "A responder unit with this name already exists"}), 409
    try:
        latitude = _coordinate(data["latitude"], "latitude", -90, 90)
        longitude = _coordinate(data["longitude"], "longitude", -180, 180)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    responder = ResponderUnit(
        name=name,
        unit_type=str(data["unit_type"]).strip()[:50],
        skills=str(data["skills"]).strip()[:255],
        contact_phone=str(data["contact_phone"]).strip()[:30],
        latitude=latitude,
        longitude=longitude,
        availability_status="available",
    )
    db.session.add(responder)
    audit_event("admin.responder_create", "success", request.user.id)
    db.session.commit()
    return jsonify({"responder": responder.to_dict()}), 201


@admin_bp.post("/donation-campaigns")
@login_required(roles=["Admin"])
@limiter.limit("30 per hour", key_func=authenticated_rate_key)
def create_donation_campaign():
    data = request.get_json(silent=True) or {}
    required = ["title", "description", "goal_amount", "organizer"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    disaster_id = int(data["disaster_id"]) if data.get("disaster_id") not in {None, ""} else None
    if disaster_id is not None:
        db.get_or_404(Disaster, disaster_id)
    try:
        goal_amount = Decimal(str(data["goal_amount"]))
    except InvalidOperation:
        return jsonify({"error": "goal_amount must be a number"}), 400
    if not goal_amount.is_finite() or goal_amount <= 0:
        return jsonify({"error": "goal_amount must be greater than zero"}), 400
    campaign = DonationCampaign(
        disaster_id=disaster_id,
        title=str(data["title"]).strip()[:180],
        description=str(data["description"]).strip(),
        goal_amount=goal_amount,
        currency=str(data.get("currency") or "INR").strip().upper()[:10],
        status="active",
        organizer=str(data["organizer"]).strip()[:160],
    )
    db.session.add(campaign)
    audit_event("admin.donation_campaign_create", "success", request.user.id)
    db.session.commit()
    return jsonify({"campaign": {**campaign.to_dict(), "goal_amount": float(campaign.goal_amount)}}), 201


def managed_user(user):
    profile = RoleProfile.query.filter_by(user_id=user.id).first()
    return {
        **public_user(user),
        "organization_name": profile.organization_name if profile else None,
        "verification_status": profile.verification_status if profile else "verified",
        "mfa_enabled": enabled_credential(user.id) is not None,
        "mfa_required": required_for(user),
    }


def _assign_or_create_facility(role, data):
    model = FACILITY_ROLE_MODELS[role]
    facility_id = data.get("facility_id")
    if facility_id not in {None, "", "new"}:
        try:
            return db.get_or_404(model, int(facility_id))
        except (TypeError, ValueError) as error:
            raise ValueError("facility_id must be a whole number") from error

    facility = data.get("facility") or {}
    if not isinstance(facility, dict):
        raise ValueError("facility must be an object")
    common = ["name", "address", "latitude", "longitude", "contact_phone"]
    role_fields = {
        "Hospital": ["total_beds", "available_beds", "icu_beds", "emergency_capacity"],
        "Shelter": ["total_capacity", "available_capacity"],
        "Ambulance": ["vehicle_number", "driver_name"],
    }
    required = common + role_fields[role]
    if role == "Ambulance":
        required.remove("name")
        required.remove("address")
    missing = [field for field in required if facility.get(field) in {None, ""}]
    if missing:
        raise ValueError(f"Missing facility fields: {', '.join(missing)}")
    latitude = _coordinate(facility["latitude"], "facility latitude", -90, 90)
    longitude = _coordinate(facility["longitude"], "facility longitude", -180, 180)

    if role == "Hospital":
        total_beds = _nonnegative_int(facility["total_beds"], "total_beds")
        available_beds = _nonnegative_int(facility["available_beds"], "available_beds")
        icu_beds = _nonnegative_int(facility["icu_beds"], "icu_beds")
        emergency_capacity = _nonnegative_int(facility["emergency_capacity"], "emergency_capacity")
        if available_beds > total_beds:
            raise ValueError("available_beds must not exceed total_beds")
        item = Hospital(
            name=str(facility["name"]).strip()[:160],
            address=str(facility["address"]).strip()[:255],
            latitude=latitude,
            longitude=longitude,
            total_beds=total_beds,
            available_beds=available_beds,
            icu_beds=icu_beds,
            emergency_capacity=emergency_capacity,
            contact_phone=str(facility["contact_phone"]).strip()[:30],
        )
    elif role == "Shelter":
        total_capacity = _nonnegative_int(facility["total_capacity"], "total_capacity")
        available_capacity = _nonnegative_int(facility["available_capacity"], "available_capacity")
        if available_capacity > total_capacity:
            raise ValueError("available_capacity must not exceed total_capacity")
        item = Shelter(
            name=str(facility["name"]).strip()[:160],
            address=str(facility["address"]).strip()[:255],
            latitude=latitude,
            longitude=longitude,
            total_capacity=total_capacity,
            available_capacity=available_capacity,
            food_available=bool(facility.get("food_available", True)),
            medical_support=bool(facility.get("medical_support", False)),
            contact_phone=str(facility["contact_phone"]).strip()[:30],
        )
    else:
        vehicle_number = str(facility["vehicle_number"]).strip().upper()[:40]
        if Ambulance.query.filter_by(vehicle_number=vehicle_number).first():
            raise ValueError("An ambulance with this vehicle number already exists")
        item = Ambulance(
            vehicle_number=vehicle_number,
            driver_name=str(facility["driver_name"]).strip()[:120],
            phone=str(facility["contact_phone"]).strip()[:30],
            latitude=latitude,
            longitude=longitude,
            status="available",
            hospital_id=int(facility["hospital_id"]) if facility.get("hospital_id") not in {None, ""} else None,
        )
        if item.hospital_id is not None:
            db.get_or_404(Hospital, item.hospital_id)
    db.session.add(item)
    db.session.flush()
    return item


def _nonnegative_int(value, name):
    try:
        output = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a whole number") from error
    if output < 0:
        raise ValueError(f"{name} must not be negative")
    return output


def _coordinate(value, name, minimum, maximum):
    try:
        output = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number") from error
    if not minimum <= output <= maximum:
        raise ValueError(f"{name} is outside valid bounds")
    return output


def _optional_float(value, name):
    if value in {None, ""}:
        return None
    return _coordinate(value, name, -180 if name == "longitude" else -90, 180 if name == "longitude" else 90)


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
