from flask import Blueprint, jsonify
from sqlalchemy import func

from ..auth import login_required
from ..models import Ambulance, Disaster, Hospital, RescueRequest, Resource, Shelter, Volunteer

admin_bp = Blueprint("admin", __name__)


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
