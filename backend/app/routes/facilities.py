from flask import Blueprint, jsonify, request

from ..auth import login_required
from ..extensions import db
from ..models import (
    Ambulance,
    Hospital,
    HospitalCapacityLog,
    ResourceDistribution,
    Shelter,
    ShelterCapacityLog,
    VolunteerAssignment,
)

facilities_bp = Blueprint("facilities", __name__)


@facilities_bp.get("/hospitals/<int:hospital_id>/capacity")
@login_required()
def get_hospital_capacity(hospital_id):
    return jsonify({"hospital": Hospital.query.get_or_404(hospital_id).to_dict()})


@facilities_bp.patch("/hospitals/<int:hospital_id>/capacity")
@login_required(roles=["Admin", "Hospital"])
def update_hospital_capacity(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    data = request.get_json() or {}
    for field in ["available_beds", "icu_beds", "emergency_capacity"]:
        if field in data:
            setattr(hospital, field, int(data[field]))
    db.session.add(HospitalCapacityLog(hospital_id=hospital.id, available_beds=hospital.available_beds, icu_beds=hospital.icu_beds, emergency_capacity=hospital.emergency_capacity))
    db.session.commit()
    return jsonify({"hospital": hospital.to_dict()})


@facilities_bp.get("/shelters/<int:shelter_id>/capacity")
@login_required()
def get_shelter_capacity(shelter_id):
    return jsonify({"shelter": Shelter.query.get_or_404(shelter_id).to_dict()})


@facilities_bp.patch("/shelters/<int:shelter_id>/capacity")
@login_required(roles=["Admin", "Shelter", "NGO"])
def update_shelter_capacity(shelter_id):
    shelter = Shelter.query.get_or_404(shelter_id)
    data = request.get_json() or {}
    if "available_capacity" in data:
        shelter.available_capacity = int(data["available_capacity"])
    if "food_available" in data:
        shelter.food_available = bool(data["food_available"])
    if "medical_support" in data:
        shelter.medical_support = bool(data["medical_support"])
    db.session.add(ShelterCapacityLog(shelter_id=shelter.id, available_capacity=shelter.available_capacity))
    db.session.commit()
    return jsonify({"shelter": shelter.to_dict()})


@facilities_bp.get("/ambulances/<int:ambulance_id>/status")
@login_required()
def get_ambulance_status(ambulance_id):
    return jsonify({"ambulance": Ambulance.query.get_or_404(ambulance_id).to_dict()})


@facilities_bp.patch("/ambulances/<int:ambulance_id>/status")
@login_required(roles=["Admin", "Ambulance", "Hospital"])
def update_ambulance_status(ambulance_id):
    ambulance = Ambulance.query.get_or_404(ambulance_id)
    data = request.get_json() or {}
    for field in ["status", "latitude", "longitude"]:
        if field in data:
            setattr(ambulance, field, data[field])
    db.session.commit()
    return jsonify({"ambulance": ambulance.to_dict()})


@facilities_bp.post("/distributions")
@login_required(roles=["Admin", "NGO", "Shelter"])
def create_distribution():
    data = request.get_json() or {}
    distribution = ResourceDistribution(
        resource_id=int(data["resource_id"]),
        disaster_id=int(data["disaster_id"]),
        quantity=int(data["quantity"]),
        destination=data["destination"],
        status=data.get("status", "planned"),
    )
    db.session.add(distribution)
    db.session.commit()
    return jsonify({"distribution": distribution.to_dict()}), 201


@facilities_bp.post("/volunteer-assignments")
@login_required(roles=["Admin", "NGO"])
def create_volunteer_assignment():
    data = request.get_json() or {}
    assignment = VolunteerAssignment(
        volunteer_id=int(data["volunteer_id"]),
        disaster_id=int(data["disaster_id"]),
        task=data["task"],
        status=data.get("status", "assigned"),
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({"assignment": assignment.to_dict()}), 201
