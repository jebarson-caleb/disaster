from flask import Blueprint, jsonify, request

from ..auth import create_token, hash_password, login_required, verify_password
from ..extensions import db
from ..models import RoleProfile, User

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


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    required = ["name", "email", "phone", "role", "password"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data["role"] not in VALID_ROLES:
        return jsonify({"error": "Invalid role"}), 400
    if User.query.filter_by(email=data["email"].lower()).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        name=data["name"],
        email=data["email"].lower(),
        phone=data["phone"],
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
    db.session.commit()
    return jsonify({"user": public_user(user), "token": create_token(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=str(data.get("email", "")).lower()).first()
    if not user or not verify_password(user.password_hash, data.get("password", "")):
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
