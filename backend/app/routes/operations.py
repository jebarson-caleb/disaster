from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, or_

from ..auth import create_token, login_required
from ..extensions import db
from ..models import (
    AlertAcknowledgement,
    Ambulance,
    Disaster,
    EmergencyAlert,
    Hospital,
    RescueRequest,
    Resource,
    ResourceDistribution,
    Shelter,
    User,
    Volunteer,
    VolunteerAssignment,
)

operations_bp = Blueprint("operations", __name__)


@operations_bp.get("/operations/bootstrap")
@login_required()
def bootstrap():
    """One round-trip snapshot for low-bandwidth field clients."""
    now = datetime.now(timezone.utc)
    alerts = (
        EmergencyAlert.query.filter_by(status="active")
        .filter(or_(EmergencyAlert.expires_at.is_(None), EmergencyAlert.expires_at > now))
        .order_by(EmergencyAlert.created_at.desc())
        .limit(50)
        .all()
    )
    acknowledged_ids = {
        alert_id
        for (alert_id,) in AlertAcknowledgement.query.with_entities(AlertAcknowledgement.alert_id)
        .filter_by(user_id=request.user.id)
        .all()
    }
    acknowledgement_counts = dict(
        db.session.query(AlertAcknowledgement.alert_id, func.count(AlertAcknowledgement.id))
        .group_by(AlertAcknowledgement.alert_id)
        .all()
    )
    return jsonify(
        {
            "disasters": [item.to_dict() for item in Disaster.query.order_by(Disaster.created_at.desc()).limit(200).all()],
            "rescue_requests": [item.to_dict() for item in RescueRequest.query.order_by(RescueRequest.priority_score.desc(), RescueRequest.created_at.asc()).limit(300).all()],
            "facilities": {
                "hospitals": [item.to_dict() for item in Hospital.query.order_by(Hospital.name).all()],
                "shelters": [item.to_dict() for item in Shelter.query.order_by(Shelter.name).all()],
                "ambulances": [item.to_dict() for item in Ambulance.query.order_by(Ambulance.vehicle_number).all()],
            },
            "resources": [item.to_dict() for item in Resource.query.order_by(Resource.category, Resource.name).all()],
            "alerts": [
                {
                    **item.to_dict(),
                    "acknowledgement_count": acknowledgement_counts.get(item.id, 0),
                    "acknowledged": item.id in acknowledged_ids,
                }
                for item in alerts
            ],
            "server_time": datetime.now(timezone.utc).isoformat(),
        }
    )


@operations_bp.post("/alerts")
@login_required(roles=["Admin", "Police", "Fire Service", "NGO"])
def create_alert():
    data = request.get_json() or {}
    missing = [field for field in ["audience", "channels", "message", "instruction"] if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    expires_in_hours = int(data.get("expires_in_hours", 6))
    if not 1 <= expires_in_hours <= 72:
        return jsonify({"error": "expires_in_hours must be between 1 and 72"}), 400
    alert = EmergencyAlert(
        identifier=f"RESQ-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:6].upper()}",
        sender_id=request.user.id,
        event=data.get("event", "All-hazard emergency warning"),
        audience=data["audience"],
        channels=data["channels"],
        urgency=data.get("urgency", "immediate"),
        severity=data.get("severity", "severe"),
        certainty=data.get("certainty", "likely"),
        message=data["message"],
        instruction=data["instruction"],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({"alert": {**alert.to_dict(), "acknowledgement_count": 0}}), 201


@operations_bp.post("/alerts/<int:alert_id>/acknowledge")
@login_required()
def acknowledge_alert(alert_id):
    db.get_or_404(EmergencyAlert, alert_id)
    data = request.get_json() or {}
    acknowledgement = AlertAcknowledgement.query.filter_by(alert_id=alert_id, user_id=request.user.id).first()
    created = acknowledgement is None
    if created:
        acknowledgement = AlertAcknowledgement(alert_id=alert_id, user_id=request.user.id)
        db.session.add(acknowledgement)
    acknowledgement.response = data.get("response", "received")
    acknowledgement.latitude = data.get("latitude")
    acknowledgement.longitude = data.get("longitude")
    db.session.commit()
    return jsonify({"acknowledgement": acknowledgement.to_dict(), "created": created})


@operations_bp.get("/safe-route")
@login_required()
def safe_route():
    try:
        latitude = float(request.args["latitude"])
        longitude = float(request.args["longitude"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "latitude and longitude are required"}), 400

    destination_type = request.args.get("destination", "shelter")
    candidates = Shelter.query.filter(Shelter.available_capacity > 0).all() if destination_type == "shelter" else Hospital.query.filter(Hospital.available_beds > 0).all()
    if not candidates:
        return jsonify({"error": f"No available {destination_type} found"}), 404
    destination = min(candidates, key=lambda item: distance_km(latitude, longitude, item.latitude, item.longitude))
    distance = distance_km(latitude, longitude, destination.latitude, destination.longitude)
    active_hazards = Disaster.query.filter_by(status="active").all()
    nearby_hazards = [item for item in active_hazards if distance_km(latitude, longitude, item.latitude, item.longitude) < 5]
    return jsonify(
        {
            "destination_type": destination_type,
            "destination": destination.to_dict(),
            "distance_km": round(distance, 1),
            "nearby_hazards": [item.to_dict() for item in nearby_hazards],
            "guidance": "Follow official road closures and field-team instructions; the route link is advisory, not a guarantee of road safety.",
            "navigation_url": f"https://www.google.com/maps/dir/?api=1&origin={latitude},{longitude}&destination={destination.latitude},{destination.longitude}&travelmode=driving",
        }
    )


@operations_bp.get("/coordination")
@login_required(roles=["Admin", "NGO", "Police", "Fire Service"])
def coordination():
    volunteers = Volunteer.query.order_by(Volunteer.availability_status).all()
    return jsonify(
        {
            "resources": [item.to_dict() for item in Resource.query.order_by(Resource.category, Resource.name).all()],
            "distributions": [item.to_dict() for item in ResourceDistribution.query.order_by(ResourceDistribution.created_at.desc()).limit(100).all()],
            "volunteers": [
                {**item.to_dict(), "name": db.session.get(User, item.user_id).name}
                for item in volunteers
            ],
            "assignments": [item.to_dict() for item in VolunteerAssignment.query.order_by(VolunteerAssignment.assigned_at.desc()).limit(100).all()],
        }
    )


@operations_bp.post("/auth/demo-session")
def demo_session():
    if not current_app.config.get("DEMO_MODE"):
        return jsonify({"error": "Demo sessions are disabled"}), 404
    role = (request.get_json() or {}).get("role", "Citizen")
    user = User.query.filter_by(role=role).order_by(User.id).first()
    if user is None:
        return jsonify({"error": f"No demo user is configured for {role}"}), 404
    return jsonify({"user": public_user(user), "token": create_token(user)})


def public_user(user):
    output = user.to_dict()
    output.pop("password_hash", None)
    return output


def distance_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    value = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(value))
