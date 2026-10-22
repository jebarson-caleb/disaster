"""Server-side record scoping for facility- and assignment-bound roles."""

from .extensions import db
from .models import (
    HospitalNotification,
    RescueRequest,
    ResponseDispatch,
    RoleProfile,
    Shelter,
    Volunteer,
)
from .services.dispatch_service import distance_km

COMMAND_ROLES = {"Admin", "Police", "Fire Service", "NGO"}
SHELTER_ARRIVAL_RADIUS_KM = 30
SHELTER_ARRIVAL_STATUSES = ("assigned", "en route")


def role_profile(user):
    return RoleProfile.query.filter_by(user_id=user.id).first()


def assigned_rescue_ids(user, profile=None):
    """Rescue IDs a facility- or assignment-bound account may see."""
    profile = profile or role_profile(user)
    if user.role == "Hospital":
        if profile is None or not profile.hospital_id:
            return []
        return [
            rescue_id
            for (rescue_id,) in HospitalNotification.query.with_entities(HospitalNotification.rescue_request_id)
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
    if user.role == "Shelter":
        return shelter_arrival_ids(profile)
    return []


def shelter_arrival_ids(profile):
    """Stable evacuees being moved within reach of the assigned shelter."""
    if profile is None or not profile.shelter_id:
        return []
    shelter = db.session.get(Shelter, profile.shelter_id)
    if shelter is None:
        return []
    candidates = RescueRequest.query.filter(
        RescueRequest.status.in_(SHELTER_ARRIVAL_STATUSES),
        RescueRequest.condition == "stable",
    ).all()
    return [
        item.id
        for item in candidates
        if distance_km(item.latitude, item.longitude, shelter.latitude, shelter.longitude) <= SHELTER_ARRIVAL_RADIUS_KM
    ]


def scoped_rescue_query(query, user, profile=None):
    if user.role in COMMAND_ROLES:
        return query
    if user.role == "Citizen":
        return query.filter_by(requester_id=user.id)
    return query.filter(RescueRequest.id.in_(assigned_rescue_ids(user, profile)))


def can_update_rescue(rescue_id, user):
    """Assignment-bound roles may change only rescues assigned to them."""
    if user.role in COMMAND_ROLES:
        return True
    if user.role in {"Hospital", "Ambulance", "Volunteer"}:
        return rescue_id in set(assigned_rescue_ids(user))
    return False
