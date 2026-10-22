"""Department field operations: road access, readiness checklists, and volunteer duty."""

import json

from flask import Blueprint, jsonify, request

from .. import validation
from ..auth import authenticated_rate_key, login_required
from ..extensions import db, limiter
from ..models import Disaster, ReadinessCheck, RoadClosure, Volunteer, VolunteerAssignment

field_bp = Blueprint("field", __name__)

ROAD_ACCESS_ROLES = ["Admin", "Police", "Fire Service"]
ROAD_STATUSES = {"closed", "restricted", "reopened"}
READINESS_ROLES = ["Admin", "Police", "Fire Service", "Hospital", "Shelter", "Ambulance", "NGO", "Volunteer"]
MAX_CHECKLIST_ITEMS = 12
VOLUNTEER_SELF_STATUSES = {"available", "off duty"}
ASSIGNMENT_STATUSES = {"assigned", "in progress", "completed", "cancelled"}


def road_closures_payload(limit=100):
    items = (
        RoadClosure.query.order_by(RoadClosure.status == "reopened", RoadClosure.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [item.to_dict() for item in items]


def readiness_payload(user, limit=50):
    """Latest checklists visible to the caller: its own role, or every role for Admin."""
    query = ReadinessCheck.query.order_by(ReadinessCheck.created_at.desc())
    if user.role != "Admin":
        query = query.filter_by(role=user.role)
    return [_readiness_dict(item) for item in query.limit(limit).all()]


def volunteer_payload(user):
    volunteer = Volunteer.query.filter_by(user_id=user.id).first()
    if volunteer is None:
        return None
    assignments = (
        VolunteerAssignment.query.filter_by(volunteer_id=volunteer.id)
        .order_by(VolunteerAssignment.assigned_at.desc())
        .limit(20)
        .all()
    )
    return {**volunteer.to_dict(), "assignments": [item.to_dict() for item in assignments]}


def _readiness_dict(item):
    output = item.to_dict()
    try:
        output["items"] = json.loads(item.items or "{}")
    except ValueError:
        output["items"] = {}
    return output


@field_bp.get("/road-closures")
@login_required()
def list_road_closures():
    return jsonify({"road_closures": road_closures_payload()})


@field_bp.post("/road-closures")
@login_required(roles=ROAD_ACCESS_ROLES)
@limiter.limit("60 per hour", key_func=authenticated_rate_key)
def create_road_closure():
    data = request.get_json() or {}
    disaster_id = None
    if data.get("disaster_id") not in {None, ""}:
        disaster_id = validation.whole_number(data["disaster_id"], "disaster_id", minimum=1, maximum=2**31 - 1)
        db.get_or_404(Disaster, disaster_id)
    closure = RoadClosure(
        disaster_id=disaster_id,
        road_name=validation.text(data, "road_name", 160),
        location=validation.text(data, "location", 255),
        latitude=validation.latitude(data.get("latitude")),
        longitude=validation.longitude(data.get("longitude")),
        status=validation.choice(data, "status", ROAD_STATUSES - {"reopened"}, default="closed"),
        reason=validation.text(data, "reason", 500),
        diversion=validation.optional_text(data, "diversion", 255),
        reported_by_id=request.user.id,
    )
    db.session.add(closure)
    db.session.commit()
    return jsonify({"road_closure": closure.to_dict()}), 201


@field_bp.patch("/road-closures/<int:closure_id>")
@login_required(roles=ROAD_ACCESS_ROLES)
def update_road_closure(closure_id):
    closure = db.get_or_404(RoadClosure, closure_id)
    data = request.get_json() or {}
    if "status" in data:
        closure.status = validation.choice(data, "status", ROAD_STATUSES)
    if "reason" in data:
        closure.reason = validation.text(data, "reason", 500)
    if "diversion" in data:
        closure.diversion = validation.optional_text(data, "diversion", 255)
    db.session.commit()
    return jsonify({"road_closure": closure.to_dict()})


@field_bp.get("/readiness-checks")
@login_required(roles=READINESS_ROLES)
def list_readiness_checks():
    return jsonify({"readiness_checks": readiness_payload(request.user)})


@field_bp.post("/readiness-checks")
@login_required(roles=READINESS_ROLES)
@limiter.limit("60 per hour", key_func=authenticated_rate_key)
def create_readiness_check():
    data = request.get_json() or {}
    items = data.get("items")
    if not isinstance(items, dict) or not 1 <= len(items) <= MAX_CHECKLIST_ITEMS:
        raise ValueError(f"items must map 1 to {MAX_CHECKLIST_ITEMS} checklist labels to true or false")
    checklist = {}
    for label, done in items.items():
        label = str(label).strip()
        if not label or len(label) > 80:
            raise ValueError("Each checklist label must contain 1 to 80 characters")
        if not isinstance(done, bool):
            raise ValueError("Each checklist value must be true or false")
        checklist[label] = done
    check = ReadinessCheck(
        user_id=request.user.id,
        role=request.user.role,
        subject=validation.text(data, "subject", 160),
        items=json.dumps(checklist),
        ready_count=sum(checklist.values()),
        total_count=len(checklist),
        notes=validation.optional_text(data, "notes", 500),
    )
    db.session.add(check)
    db.session.commit()
    return jsonify({"readiness_check": _readiness_dict(check)}), 201


@field_bp.patch("/volunteers/me/availability")
@login_required(roles=["Volunteer"])
def update_own_volunteer_availability():
    volunteer = Volunteer.query.filter_by(user_id=request.user.id).first()
    if volunteer is None:
        return jsonify({"error": "No volunteer profile is linked to this account"}), 404
    status = validation.choice(request.get_json() or {}, "availability_status", VOLUNTEER_SELF_STATUSES)
    if volunteer.availability_status in {"assigned", "pending verification"}:
        return (
            jsonify({"error": f"Availability cannot change while the profile is {volunteer.availability_status}"}),
            409,
        )
    volunteer.availability_status = status
    db.session.commit()
    return jsonify({"volunteer": volunteer_payload(request.user)})


@field_bp.patch("/volunteer-assignments/<int:assignment_id>")
@login_required(roles=["Admin", "NGO", "Volunteer"])
def update_volunteer_assignment(assignment_id):
    assignment = db.get_or_404(VolunteerAssignment, assignment_id)
    volunteer = db.session.get(Volunteer, assignment.volunteer_id)
    if request.user.role == "Volunteer" and (volunteer is None or volunteer.user_id != request.user.id):
        return jsonify({"error": "You can update only your own assignments"}), 403
    status = validation.choice(request.get_json() or {}, "status", ASSIGNMENT_STATUSES)
    assignment.status = status
    if volunteer is not None and status in {"completed", "cancelled"}:
        still_open = VolunteerAssignment.query.filter(
            VolunteerAssignment.volunteer_id == volunteer.id,
            VolunteerAssignment.id != assignment.id,
            VolunteerAssignment.status.in_(["assigned", "in progress"]),
        ).count()
        if not still_open and volunteer.availability_status == "assigned":
            volunteer.availability_status = "available"
    db.session.commit()
    return jsonify(
        {
            "assignment": assignment.to_dict(),
            "volunteer": volunteer.to_dict() if volunteer is not None else None,
        }
    )
