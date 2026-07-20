from flask import Blueprint, jsonify, request

from ..auth import create_token, hash_password, login_required, verify_password
from ..extensions import db
from ..models import RoleProfile, User, Volunteer

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


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    required = ["name", "email", "phone", "role", "password"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data["role"] not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400
    if data["role"] not in SELF_REGISTRATION_ROLES:
        return jsonify({"error": "This operational role requires administrator provisioning"}), 403
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
    profile = RoleProfile(
        user_id=user.id,
        organization_name=data.get("organization_name"),
        address=data.get("address"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
    )
    db.session.add(profile)
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
    db.session.commit()
    return jsonify({"user": public_user(user), "token": create_token(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=str(data.get("email", "")).lower()).first()
    if not user or not user.is_active or not verify_password(user.password_hash, data.get("password", "")):
        return jsonify({"error": "Invalid email or password"}), 401
    return jsonify({"user": public_user(user), "token": create_token(user)})


@auth_bp.get("/me")
@login_required()
def me():
    return jsonify({"user": public_user(request.user)})


def public_user(user):
    data = user.to_dict()
    data.pop("password_hash", None)
    return data
