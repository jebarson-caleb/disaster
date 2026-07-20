from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..auth import hash_password, login_required
from ..extensions import db
from ..models import Ambulance, Disaster, Hospital, RescueRequest, Resource, RoleProfile, Shelter, User, Volunteer
from .auth import VALID_ROLES

admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/users")
@login_required(roles=["Admin"])
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
    if len(str(data["password"])) < 8:
        return jsonify({"error": "Password must contain at least 8 characters"}), 400
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
    db.session.commit()
    output = user.to_dict()
    output.pop("password_hash", None)
    return jsonify({"user": output}), 201


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
