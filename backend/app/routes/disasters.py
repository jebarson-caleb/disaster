from flask import Blueprint, jsonify, request

from ..auth import login_required
from ..extensions import db
from ..models import (
    AiAssessment,
    Ambulance,
    Disaster,
    HospitalNotification,
    LocationPing,
    RescueRequest,
    RescueStatusHistory,
    ResponderUnit,
    ResponseDispatch,
    RoleProfile,
    Volunteer,
)
from ..services.ai_service import damage_estimation, relief_prioritization
from ..services.dispatch_service import auto_dispatch_rescue

disasters_bp = Blueprint("disasters", __name__)
VALID_RESCUE_STATUSES = {"pending", "assigned", "en route", "triage", "rescued", "cancelled"}


@disasters_bp.post("/disasters")
@login_required()
def create_disaster():
    data = request.get_json() or {}
    required = ["title", "disaster_type", "description", "address", "latitude", "longitude"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    disaster = Disaster(
        title=data["title"],
        disaster_type=data["disaster_type"],
        description=data["description"],
        address=data["address"],
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        people_affected=int(data.get("people_affected") or 0),
        severity_hint=data.get("severity_hint", "medium"),
        image_url=data.get("image_url"),
        reported_by_id=request.user.id,
    )
    db.session.add(disaster)
    db.session.flush()
    assessment = damage_estimation(disaster.to_dict())
    db.session.add(
        AiAssessment(
            entity_type="disaster",
            entity_id=disaster.id,
            assessment_type="damage_estimation",
            score=assessment["score"],
            label=assessment["label"],
            explanation=assessment["explanation"],
        )
    )
    db.session.commit()
    return jsonify({"disaster": disaster.to_dict(), "damage_estimation": assessment}), 201


@disasters_bp.get("/disasters")
@login_required()
def list_disasters():
    status = request.args.get("status")
    query = Disaster.query.order_by(Disaster.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return jsonify({"disasters": [item.to_dict() for item in query.limit(200).all()]})


@disasters_bp.get("/disasters/<int:disaster_id>")
@login_required()
def get_disaster(disaster_id):
    disaster = db.get_or_404(Disaster, disaster_id)
    requests = _scoped_rescue_query(
        RescueRequest.query.filter_by(disaster_id=disaster_id),
        request.user,
    ).order_by(RescueRequest.priority_score.desc()).all()
    return jsonify({"disaster": disaster.to_dict(), "rescue_requests": [item.to_dict() for item in requests]})


@disasters_bp.post("/rescue-requests")
@login_required()
def create_rescue_request():
    data = request.get_json() or {}
    required = ["disaster_id", "victim_name", "latitude", "longitude"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    disaster = db.get_or_404(Disaster, int(data["disaster_id"]))
    ai_payload = {**data, "disaster_type": disaster.disaster_type}
    priority = relief_prioritization(ai_payload)
    rescue = RescueRequest(
        disaster_id=disaster.id,
        requester_id=request.user.id,
        victim_name=data["victim_name"],
        victim_age=int(data.get("victim_age") or 0),
        people_count=int(data.get("people_count") or 1),
        condition=data.get("condition", "stable"),
        trapped=bool(data.get("trapped")),
        vulnerable_people=int(data.get("vulnerable_people") or 0),
        notes=data.get("notes"),
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        priority_score=priority["score"],
        priority_label=priority["label"],
    )
    db.session.add(rescue)
    db.session.flush()
    db.session.add(RescueStatusHistory(rescue_request_id=rescue.id, status="pending", note="Request created", changed_by_id=request.user.id))
    db.session.add(AiAssessment(entity_type="rescue_request", entity_id=rescue.id, assessment_type="relief_prioritization", score=priority["score"], label=priority["label"], explanation=priority["explanation"]))
    if data.get("location_consent") is True:
        db.session.add(
            LocationPing(
                user_id=request.user.id,
                rescue_request_id=rescue.id,
                latitude=rescue.latitude,
                longitude=rescue.longitude,
                accuracy_meters=float(data["location_accuracy"]) if data.get("location_accuracy") not in {None, ""} else None,
                consent_granted=True,
            )
        )
    allocation = auto_dispatch_rescue(rescue, disaster)
    if rescue.status == "assigned":
        db.session.add(RescueStatusHistory(rescue_request_id=rescue.id, status="assigned", note=f"Automatically allocated to {rescue.assigned_unit}", changed_by_id=request.user.id))
    db.session.commit()
    return jsonify({"rescue_request": rescue.to_dict(), "priority": priority, "automatic_allocation": allocation}), 201


@disasters_bp.get("/rescue-requests")
@login_required()
def list_rescue_requests():
    status = request.args.get("status")
    query = _scoped_rescue_query(RescueRequest.query, request.user).order_by(
        RescueRequest.priority_score.desc(),
        RescueRequest.created_at.asc(),
    )
    if status:
        query = query.filter_by(status=status)
    return jsonify({"rescue_requests": [item.to_dict() for item in query.limit(300).all()]})


@disasters_bp.patch("/rescue-requests/<int:request_id>/status")
@login_required(roles=["Admin", "Police", "Fire Service", "Ambulance", "NGO", "Hospital", "Volunteer"])
def update_rescue_status(request_id):
    rescue = db.get_or_404(RescueRequest, request_id)
    if request.user.role in {"Hospital", "Ambulance", "Volunteer"} and not _assigned_to_user(
        rescue.id,
        request.user,
    ):
        return jsonify({"error": "This rescue request is not assigned to your account"}), 403
    data = request.get_json() or {}
    status = data.get("status")
    if not status:
        return jsonify({"error": "status is required"}), 400
    if status not in VALID_RESCUE_STATUSES:
        return jsonify({"error": "Invalid rescue status"}), 400
    rescue.status = status
    if data.get("assigned_unit"):
        rescue.assigned_unit = data["assigned_unit"]
    if status in {"rescued", "cancelled"}:
        final_dispatch_status = "completed" if status == "rescued" else "cancelled"
        for dispatch in ResponseDispatch.query.filter_by(rescue_request_id=rescue.id).all():
            dispatch.status = final_dispatch_status
            if dispatch.responder_type == "rescue_unit":
                unit = db.session.get(ResponderUnit, dispatch.responder_id)
                if unit:
                    unit.availability_status = "available"
            elif dispatch.responder_type == "volunteer":
                volunteer = db.session.get(Volunteer, dispatch.responder_id)
                if volunteer:
                    volunteer.availability_status = "available"
            elif dispatch.responder_type == "ambulance":
                ambulance = db.session.get(Ambulance, dispatch.responder_id)
                if ambulance:
                    ambulance.status = "available"
    db.session.add(RescueStatusHistory(rescue_request_id=rescue.id, status=status, note=data.get("note"), changed_by_id=request.user.id))
    db.session.commit()
    return jsonify({"rescue_request": rescue.to_dict()})


@disasters_bp.patch("/rescue-requests/<int:request_id>/assign")
@login_required(roles=["Admin", "Police", "Fire Service", "NGO"])
def assign_rescue_request(request_id):
    rescue = db.get_or_404(RescueRequest, request_id)
    data = request.get_json() or {}
    if not data.get("assigned_unit"):
        return jsonify({"error": "assigned_unit is required"}), 400
    rescue.assigned_unit = data["assigned_unit"]
    rescue.status = data.get("status", "assigned")
    if rescue.status not in VALID_RESCUE_STATUSES:
        return jsonify({"error": "Invalid rescue status"}), 400
    db.session.add(RescueStatusHistory(rescue_request_id=rescue.id, status=rescue.status, note=f"Assigned to {rescue.assigned_unit}", changed_by_id=request.user.id))
    db.session.commit()
    return jsonify({"rescue_request": rescue.to_dict()})


def _scoped_rescue_query(query, user):
    if user.role in {"Admin", "Police", "Fire Service", "NGO"}:
        return query
    if user.role == "Citizen":
        return query.filter_by(requester_id=user.id)
    if user.role in {"Hospital", "Ambulance", "Volunteer"}:
        return query.filter(RescueRequest.id.in_(_assigned_rescue_ids(user)))
    return query.filter(RescueRequest.id.in_([]))


def _assigned_to_user(rescue_id, user):
    return rescue_id in set(_assigned_rescue_ids(user))


def _assigned_rescue_ids(user):
    profile = RoleProfile.query.filter_by(user_id=user.id).first()
    if user.role == "Hospital":
        if profile is None or not profile.hospital_id:
            return []
        return [
            rescue_id
            for (rescue_id,) in HospitalNotification.query.with_entities(
                HospitalNotification.rescue_request_id
            )
            .filter_by(hospital_id=profile.hospital_id)
            .all()
        ]
    if user.role == "Ambulance":
        if profile is None or not profile.ambulance_id:
            return []
        return [
            rescue_id
            for (rescue_id,) in ResponseDispatch.query.with_entities(ResponseDispatch.rescue_request_id)
            .filter_by(responder_type="ambulance", responder_id=profile.ambulance_id)
            .all()
        ]
    if user.role == "Volunteer":
        volunteer = Volunteer.query.filter_by(user_id=user.id).first()
        if volunteer is None:
            return []
        return [
            rescue_id
            for (rescue_id,) in ResponseDispatch.query.with_entities(ResponseDispatch.rescue_request_id)
            .filter_by(responder_type="volunteer", responder_id=volunteer.id)
            .all()
        ]
    return []
