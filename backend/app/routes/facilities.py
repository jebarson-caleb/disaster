from flask import Blueprint, jsonify, request

from .. import validation
from ..auth import login_required
from ..extensions import db
from ..models import (
    Ambulance,
    Disaster,
    Hospital,
    HospitalCapacityLog,
    Resource,
    ResourceDistribution,
    RoleProfile,
    Shelter,
    ShelterCapacityLog,
    Volunteer,
    VolunteerAssignment,
)

facilities_bp = Blueprint("facilities", __name__)
AMBULANCE_STATUSES = {"available", "dispatched", "maintenance", "offline"}
DISTRIBUTION_STATUSES = {"planned", "in transit", "delivered"}


@facilities_bp.get("/hospitals/<int:hospital_id>/capacity")
@login_required()
def get_hospital_capacity(hospital_id):
    return jsonify({"hospital": db.get_or_404(Hospital, hospital_id).to_dict()})


@facilities_bp.patch("/hospitals/<int:hospital_id>/capacity")
@login_required(roles=["Admin", "Hospital"])
def update_hospital_capacity(hospital_id):
    if request.user.role == "Hospital" and not _manages(request.user.id, "hospital_id", hospital_id):
        return jsonify({"error": "You can update only your assigned hospital"}), 403
    hospital = db.get_or_404(Hospital, hospital_id)
    data = request.get_json() or {}
    for field in ["available_beds", "icu_beds", "emergency_capacity"]:
        if field in data:
            setattr(hospital, field, validation.whole_number(data[field], field))
    if not 0 <= hospital.available_beds <= hospital.total_beds or hospital.icu_beds < 0 or hospital.emergency_capacity < 0:
        return jsonify({"error": "Hospital capacity values are outside valid bounds"}), 400
    db.session.add(HospitalCapacityLog(hospital_id=hospital.id, available_beds=hospital.available_beds, icu_beds=hospital.icu_beds, emergency_capacity=hospital.emergency_capacity))
    db.session.commit()
    return jsonify({"hospital": hospital.to_dict()})


@facilities_bp.get("/shelters/<int:shelter_id>/capacity")
@login_required()
def get_shelter_capacity(shelter_id):
    return jsonify({"shelter": db.get_or_404(Shelter, shelter_id).to_dict()})


@facilities_bp.patch("/shelters/<int:shelter_id>/capacity")
@login_required(roles=["Admin", "Shelter"])
def update_shelter_capacity(shelter_id):
    if request.user.role == "Shelter" and not _manages(request.user.id, "shelter_id", shelter_id):
        return jsonify({"error": "You can update only your assigned shelter"}), 403
    shelter = db.get_or_404(Shelter, shelter_id)
    data = request.get_json() or {}
    if "available_capacity" in data:
        shelter.available_capacity = validation.whole_number(data["available_capacity"], "available_capacity")
    for field in ["food_available", "medical_support"]:
        if field in data:
            if not isinstance(data[field], bool):
                return jsonify({"error": f"{field} must be true or false"}), 400
            setattr(shelter, field, data[field])
    if not 0 <= shelter.available_capacity <= shelter.total_capacity:
        return jsonify({"error": "Shelter capacity is outside valid bounds"}), 400
    db.session.add(ShelterCapacityLog(shelter_id=shelter.id, available_capacity=shelter.available_capacity))
    db.session.commit()
    return jsonify({"shelter": shelter.to_dict()})


@facilities_bp.get("/ambulances/<int:ambulance_id>/status")
@login_required()
def get_ambulance_status(ambulance_id):
    return jsonify({"ambulance": db.get_or_404(Ambulance, ambulance_id).to_dict()})


@facilities_bp.patch("/ambulances/<int:ambulance_id>/status")
@login_required(roles=["Admin", "Ambulance"])
def update_ambulance_status(ambulance_id):
    if request.user.role == "Ambulance" and not _manages(request.user.id, "ambulance_id", ambulance_id):
        return jsonify({"error": "You can update only your assigned ambulance"}), 403
    ambulance = db.get_or_404(Ambulance, ambulance_id)
    data = request.get_json() or {}
    if "status" in data:
        if data["status"] not in AMBULANCE_STATUSES:
            return jsonify({"error": "Invalid ambulance status"}), 400
        ambulance.status = data["status"]
    if ("latitude" in data) != ("longitude" in data):
        return jsonify({"error": "latitude and longitude must be updated together"}), 400
    if "latitude" in data:
        ambulance.latitude = validation.latitude(data["latitude"])
        ambulance.longitude = validation.longitude(data["longitude"])
    db.session.commit()
    return jsonify({"ambulance": ambulance.to_dict()})


@facilities_bp.post("/distributions")
@login_required(roles=["Admin", "NGO", "Shelter"])
def create_distribution():
    data = request.get_json() or {}
    required = ["resource_id", "disaster_id", "quantity", "destination"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    resource = db.get_or_404(Resource, validation.whole_number(data["resource_id"], "resource_id", minimum=1, maximum=2**31 - 1))
    disaster_id = validation.whole_number(data["disaster_id"], "disaster_id", minimum=1, maximum=2**31 - 1)
    db.get_or_404(Disaster, disaster_id)
    quantity = validation.whole_number(data["quantity"], "quantity", minimum=1)
    if quantity > resource.available_quantity:
        return jsonify({"error": "Requested quantity exceeds available inventory"}), 400
    distribution = ResourceDistribution(
        resource_id=resource.id,
        disaster_id=disaster_id,
        quantity=quantity,
        destination=validation.text(data, "destination", 180),
        status=validation.choice(data, "status", DISTRIBUTION_STATUSES, default="planned"),
    )
    resource.available_quantity -= quantity
    db.session.add(distribution)
    db.session.commit()
    return jsonify({"distribution": distribution.to_dict()}), 201


@facilities_bp.post("/volunteer-assignments")
@login_required(roles=["Admin", "NGO"])
def create_volunteer_assignment():
    data = request.get_json() or {}
    required = ["volunteer_id", "disaster_id", "task"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    volunteer = db.get_or_404(Volunteer, validation.whole_number(data["volunteer_id"], "volunteer_id", minimum=1, maximum=2**31 - 1))
    disaster_id = validation.whole_number(data["disaster_id"], "disaster_id", minimum=1, maximum=2**31 - 1)
    db.get_or_404(Disaster, disaster_id)
    if volunteer.availability_status != "available":
        return jsonify({"error": "Volunteer is not currently available"}), 409
    assignment = VolunteerAssignment(
        volunteer_id=volunteer.id,
        disaster_id=disaster_id,
        task=validation.text(data, "task", 180),
        status="assigned",
    )
    volunteer.availability_status = "assigned"
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"assignment": assignment.to_dict(), "volunteer": volunteer.to_dict()}), 201


def _manages(user_id, field, entity_id):
    profile = RoleProfile.query.filter_by(user_id=user_id).first()
    return profile is not None and getattr(profile, field) == entity_id
