from flask import Blueprint, jsonify, request

from ..auth import login_required
from ..extensions import db
from ..models import (
    Ambulance,
    Disaster,
    Hospital,
    HospitalCapacityLog,
    Resource,
    ResourceDistribution,
    Shelter,
    ShelterCapacityLog,
    Volunteer,
    VolunteerAssignment,
)

facilities_bp = Blueprint("facilities", __name__)


@facilities_bp.get("/hospitals/<int:hospital_id>/capacity")
@login_required()
def get_hospital_capacity(hospital_id):
    return jsonify({"hospital": db.get_or_404(Hospital, hospital_id).to_dict()})


@facilities_bp.patch("/hospitals/<int:hospital_id>/capacity")
@login_required(roles=["Admin", "Hospital"])
def update_hospital_capacity(hospital_id):
    hospital = db.get_or_404(Hospital, hospital_id)
    data = request.get_json() or {}
    for field in ["available_beds", "icu_beds", "emergency_capacity"]:
        if field in data:
            setattr(hospital, field, int(data[field]))
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
@login_required(roles=["Admin", "Shelter", "NGO"])
def update_shelter_capacity(shelter_id):
    shelter = db.get_or_404(Shelter, shelter_id)
    data = request.get_json() or {}
    if "available_capacity" in data:
        shelter.available_capacity = int(data["available_capacity"])
    if "food_available" in data:
        shelter.food_available = bool(data["food_available"])
    if "medical_support" in data:
        shelter.medical_support = bool(data["medical_support"])
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
@login_required(roles=["Admin", "Ambulance", "Hospital"])
def update_ambulance_status(ambulance_id):
    ambulance = db.get_or_404(Ambulance, ambulance_id)
    data = request.get_json() or {}
    for field in ["status", "latitude", "longitude"]:
        if field in data:
            setattr(ambulance, field, data[field])
    if ambulance.status not in {"available", "dispatched", "maintenance", "offline"}:
        return jsonify({"error": "Invalid ambulance status"}), 400
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
    resource = db.get_or_404(Resource, int(data["resource_id"]))
    db.get_or_404(Disaster, int(data["disaster_id"]))
    quantity = int(data["quantity"])
    if quantity <= 0 or quantity > resource.available_quantity:
        return jsonify({"error": "Requested quantity exceeds available inventory"}), 400
    distribution = ResourceDistribution(
        resource_id=resource.id,
        disaster_id=int(data["disaster_id"]),
        quantity=quantity,
        destination=data["destination"],
        status=data.get("status", "planned"),
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
    volunteer = db.get_or_404(Volunteer, int(data["volunteer_id"]))
    db.get_or_404(Disaster, int(data["disaster_id"]))
    if volunteer.availability_status != "available":
        return jsonify({"error": "Volunteer is not currently available"}), 409
    assignment = VolunteerAssignment(
        volunteer_id=volunteer.id,
        disaster_id=int(data["disaster_id"]),
        task=data["task"],
        status=data.get("status", "assigned"),
    )
    volunteer.availability_status = "assigned"
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"assignment": assignment.to_dict(), "volunteer": volunteer.to_dict()}), 201
