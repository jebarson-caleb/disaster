from math import asin, cos, radians, sin, sqrt

from ..extensions import db
from ..models import (
    Ambulance,
    AmbulanceDispatch,
    Hospital,
    HospitalNotification,
    Notification,
    ResponderUnit,
    ResponseDispatch,
    User,
    Volunteer,
    VolunteerAssignment,
)


def distance_km(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    value = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(value))


def auto_dispatch_rescue(rescue, disaster):
    """Reserve the nearest available field assets and notify a receiving hospital."""
    result = {"rescue_unit": None, "volunteer": None, "ambulance": None, "hospital": None}
    assigned_names = []

    responder_units = ResponderUnit.query.filter_by(availability_status="available").all()
    if responder_units:
        unit = min(responder_units, key=lambda item: distance_km(rescue.latitude, rescue.longitude, item.latitude, item.longitude))
        unit_distance = round(distance_km(rescue.latitude, rescue.longitude, unit.latitude, unit.longitude), 1)
        unit.availability_status = "dispatched"
        db.session.add(ResponseDispatch(rescue_request_id=rescue.id, responder_type="rescue_unit", responder_id=unit.id, responder_name=unit.name, distance_km=unit_distance))
        assigned_names.append(unit.name)
        result["rescue_unit"] = {"id": unit.id, "name": unit.name, "unit_type": unit.unit_type, "phone": unit.contact_phone, "distance_km": unit_distance, "skills": unit.skills}

    volunteers = Volunteer.query.filter_by(availability_status="available").filter(Volunteer.latitude.is_not(None), Volunteer.longitude.is_not(None)).all()
    if volunteers:
        volunteer = min(volunteers, key=lambda item: distance_km(rescue.latitude, rescue.longitude, item.latitude, item.longitude))
        volunteer_user = db.session.get(User, volunteer.user_id)
        volunteer_distance = round(distance_km(rescue.latitude, rescue.longitude, volunteer.latitude, volunteer.longitude), 1)
        responder_name = volunteer_user.name if volunteer_user else f"Volunteer #{volunteer.id}"
        volunteer.availability_status = "assigned"
        assignment = VolunteerAssignment(
            volunteer_id=volunteer.id,
            disaster_id=disaster.id,
            task=f"Automatic nearby dispatch for rescue #{rescue.id}: assist {rescue.victim_name}",
        )
        db.session.add(assignment)
        db.session.add(ResponseDispatch(rescue_request_id=rescue.id, responder_type="volunteer", responder_id=volunteer.id, responder_name=responder_name, distance_km=volunteer_distance))
        assigned_names.append(responder_name)
        result["volunteer"] = {"id": volunteer.id, "name": responder_name, "distance_km": volunteer_distance, "skills": volunteer.skills}

    needs_ambulance = rescue.priority_score >= 60 or rescue.condition in {"injured", "critical", "unconscious", "bleeding"}
    ambulances = Ambulance.query.filter_by(status="available").all() if needs_ambulance else []
    if ambulances:
        ambulance = min(ambulances, key=lambda item: distance_km(rescue.latitude, rescue.longitude, item.latitude, item.longitude))
        ambulance_distance = round(distance_km(rescue.latitude, rescue.longitude, ambulance.latitude, ambulance.longitude), 1)
        ambulance.status = "dispatched"
        db.session.add(AmbulanceDispatch(ambulance_id=ambulance.id, rescue_request_id=rescue.id))
        db.session.add(ResponseDispatch(rescue_request_id=rescue.id, responder_type="ambulance", responder_id=ambulance.id, responder_name=ambulance.vehicle_number, distance_km=ambulance_distance))
        assigned_names.append(ambulance.vehicle_number)
        result["ambulance"] = {"id": ambulance.id, "vehicle_number": ambulance.vehicle_number, "phone": ambulance.phone, "distance_km": ambulance_distance}

    hospitals = Hospital.query.filter(Hospital.available_beds > 0).all()
    if hospitals:
        hospital = min(hospitals, key=lambda item: distance_km(rescue.latitude, rescue.longitude, item.latitude, item.longitude))
        hospital_distance = round(distance_km(rescue.latitude, rescue.longitude, hospital.latitude, hospital.longitude), 1)
        notification = HospitalNotification(
            hospital_id=hospital.id,
            disaster_id=disaster.id,
            rescue_request_id=rescue.id,
            expected_patients=rescue.people_count,
            priority=rescue.priority_label,
            message=f"Prepare for {rescue.people_count} incoming patient(s) from {disaster.title}. Condition: {rescue.condition}.",
        )
        db.session.add(notification)
        db.session.add(Notification(role="Hospital", message=f"{hospital.name}: {notification.message}"))
        result["hospital"] = {"id": hospital.id, "name": hospital.name, "phone": hospital.contact_phone, "distance_km": hospital_distance, "available_beds": hospital.available_beds}

    if assigned_names:
        rescue.assigned_unit = " + ".join(assigned_names)
        rescue.status = "assigned"
    return result
