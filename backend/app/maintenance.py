"""Guarded maintenance operations for production cutovers."""

from dataclasses import asdict, dataclass, field

from sqlalchemy import or_

from .extensions import db
from .models import (
    AccountSecurity,
    AlertAcknowledgement,
    Ambulance,
    AmbulanceDispatch,
    AuditEvent,
    AuthSession,
    Disaster,
    DisasterNewsUpdate,
    Donation,
    EmergencyAlert,
    Hospital,
    HospitalCapacityLog,
    HospitalNotification,
    LocationPing,
    MfaChallenge,
    MfaCredential,
    Notification,
    RescueRequest,
    RescueStatusHistory,
    ResponseDispatch,
    RoleProfile,
    Shelter,
    ShelterCapacityLog,
    SupplyRequest,
    User,
    Volunteer,
    VolunteerAssignment,
    WelfareCheck,
)

TRAINING_EMAILS = frozenset(
    {
        "citizen.training@resq-command.local",
        "volunteer.training@resq-command.local",
        "police.training@resq-command.local",
        "fire-service.training@resq-command.local",
        "hospital.training@resq-command.local",
        "shelter.training@resq-command.local",
        "ambulance.training@resq-command.local",
        "ngo.training@resq-command.local",
    }
)
TRAINING_EMAIL_SUFFIX = ".training@resq-command.local"
TRAINING_HOSPITAL_NAME = "Training Hospital - Not for Incident Use"
TRAINING_SHELTER_NAME = "Training Shelter - Not for Incident Use"
TRAINING_AMBULANCE_NUMBER = "TN-00-TRN-001"
PURGE_CONFIRMATION = "PURGE_TRAINING_DATA"


@dataclass
class TrainingCleanupPlan:
    state: str
    ready: bool
    users: list[str] = field(default_factory=list)
    records_to_remove: dict[str, int] = field(default_factory=dict)
    blockers: dict[str, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def _count(query):
    return query.count()


def _positive_counts(counts):
    return {name: count for name, count in counts.items() if count}


def build_training_cleanup_plan():
    """Inspect exact acceptance fixtures without changing data."""
    suffix_users = User.query.filter(User.email.endswith(TRAINING_EMAIL_SUFFIX)).order_by(User.email).all()
    users = [user for user in suffix_users if user.email in TRAINING_EMAILS]
    emails = {user.email for user in users}
    unexpected_emails = sorted({user.email for user in suffix_users} - TRAINING_EMAILS)

    hospitals = Hospital.query.filter_by(name=TRAINING_HOSPITAL_NAME).all()
    shelters = Shelter.query.filter_by(name=TRAINING_SHELTER_NAME).all()
    ambulances = Ambulance.query.filter_by(vehicle_number=TRAINING_AMBULANCE_NUMBER).all()
    marker_count = len(users) + len(hospitals) + len(shelters) + len(ambulances)
    if marker_count == 0:
        return TrainingCleanupPlan(state="already_clean", ready=True)

    problems = []
    missing_emails = sorted(TRAINING_EMAILS - emails)
    if missing_emails:
        problems.append(f"missing expected training accounts: {', '.join(missing_emails)}")
    if unexpected_emails:
        problems.append(f"unexpected training-suffix accounts: {', '.join(unexpected_emails)}")
    if len(hospitals) != 1:
        problems.append(f"expected one marked training hospital, found {len(hospitals)}")
    if len(shelters) != 1:
        problems.append(f"expected one marked training shelter, found {len(shelters)}")
    if len(ambulances) != 1:
        problems.append(f"expected one marked training ambulance, found {len(ambulances)}")

    user_ids = [user.id for user in users]
    profiles = RoleProfile.query.filter(RoleProfile.user_id.in_(user_ids)).all() if user_ids else []
    volunteers = Volunteer.query.filter(Volunteer.user_id.in_(user_ids)).all() if user_ids else []
    volunteer_ids = [volunteer.id for volunteer in volunteers]
    hospital_ids = [item.id for item in hospitals]
    shelter_ids = [item.id for item in shelters]
    ambulance_ids = [item.id for item in ambulances]

    if len(profiles) != len(users):
        problems.append(f"expected one role profile per training account, found {len(profiles)} for {len(users)} accounts")

    profile_by_role = {profile.user.role: profile for profile in profiles}
    expected_links = {
        "Hospital": ("hospital_id", hospital_ids[0] if len(hospital_ids) == 1 else None),
        "Shelter": ("shelter_id", shelter_ids[0] if len(shelter_ids) == 1 else None),
        "Ambulance": ("ambulance_id", ambulance_ids[0] if len(ambulance_ids) == 1 else None),
    }
    for role, (field_name, expected_id) in expected_links.items():
        profile = profile_by_role.get(role)
        if profile is None or expected_id is None or getattr(profile, field_name) != expected_id:
            problems.append(f"{role} training profile is not linked to the marked fixture")

    blockers = {}
    if user_ids:
        blockers.update(
            {
                "disasters_reported": _count(Disaster.query.filter(Disaster.reported_by_id.in_(user_ids))),
                "rescue_requests": _count(RescueRequest.query.filter(RescueRequest.requester_id.in_(user_ids))),
                "rescue_status_changes": _count(
                    RescueStatusHistory.query.filter(RescueStatusHistory.changed_by_id.in_(user_ids))
                ),
                "alerts_sent": _count(EmergencyAlert.query.filter(EmergencyAlert.sender_id.in_(user_ids))),
                "alert_acknowledgements": _count(
                    AlertAcknowledgement.query.filter(AlertAcknowledgement.user_id.in_(user_ids))
                ),
                "news_updates": _count(
                    DisasterNewsUpdate.query.filter(DisasterNewsUpdate.published_by_id.in_(user_ids))
                ),
                "welfare_checks": _count(
                    WelfareCheck.query.filter(
                        or_(WelfareCheck.requester_id.in_(user_ids), WelfareCheck.responder_id.in_(user_ids))
                    )
                ),
                "hospital_acknowledgements": _count(
                    HospitalNotification.query.filter(HospitalNotification.acknowledged_by_id.in_(user_ids))
                ),
                "supply_requests": _count(SupplyRequest.query.filter(SupplyRequest.requester_id.in_(user_ids))),
                "donations": _count(Donation.query.filter(Donation.donor_id.in_(user_ids))),
                "location_pings": _count(LocationPing.query.filter(LocationPing.user_id.in_(user_ids))),
            }
        )
    if volunteer_ids:
        blockers["volunteer_assignments"] = _count(
            VolunteerAssignment.query.filter(VolunteerAssignment.volunteer_id.in_(volunteer_ids))
        )
        blockers["volunteer_dispatches"] = _count(
            ResponseDispatch.query.filter(
                ResponseDispatch.responder_type == "volunteer", ResponseDispatch.responder_id.in_(volunteer_ids)
            )
        )
    if ambulance_ids:
        blockers["ambulance_dispatches"] = _count(
            AmbulanceDispatch.query.filter(AmbulanceDispatch.ambulance_id.in_(ambulance_ids))
        )
        blockers["response_ambulance_dispatches"] = _count(
            ResponseDispatch.query.filter(
                ResponseDispatch.responder_type == "ambulance", ResponseDispatch.responder_id.in_(ambulance_ids)
            )
        )
    if hospital_ids:
        blockers["hospital_notifications"] = _count(
            HospitalNotification.query.filter(HospitalNotification.hospital_id.in_(hospital_ids))
        )
        blockers["other_ambulances_linked_to_hospital"] = _count(
            Ambulance.query.filter(
                Ambulance.hospital_id.in_(hospital_ids),
                Ambulance.id.notin_(ambulance_ids or [-1]),
            )
        )

    target_user_ids = set(user_ids)
    for role, field_name, target_ids in (
        ("Hospital", RoleProfile.hospital_id, hospital_ids),
        ("Shelter", RoleProfile.shelter_id, shelter_ids),
        ("Ambulance", RoleProfile.ambulance_id, ambulance_ids),
    ):
        if target_ids:
            blockers[f"other_{role.lower()}_profiles"] = _count(
                RoleProfile.query.filter(field_name.in_(target_ids), RoleProfile.user_id.notin_(target_user_ids or {-1}))
            )

    records_to_remove = {
        "users": len(users),
        "role_profiles": len(profiles),
        "volunteers": len(volunteers),
        "hospitals": len(hospitals),
        "shelters": len(shelters),
        "ambulances": len(ambulances),
        "hospital_capacity_logs": _count(
            HospitalCapacityLog.query.filter(HospitalCapacityLog.hospital_id.in_(hospital_ids))
        )
        if hospital_ids
        else 0,
        "shelter_capacity_logs": _count(
            ShelterCapacityLog.query.filter(ShelterCapacityLog.shelter_id.in_(shelter_ids))
        )
        if shelter_ids
        else 0,
        "notifications": _count(Notification.query.filter(Notification.user_id.in_(user_ids))) if user_ids else 0,
        "auth_sessions": _count(AuthSession.query.filter(AuthSession.user_id.in_(user_ids))) if user_ids else 0,
        "account_security": _count(AccountSecurity.query.filter(AccountSecurity.user_id.in_(user_ids)))
        if user_ids
        else 0,
        "mfa_credentials": _count(MfaCredential.query.filter(MfaCredential.user_id.in_(user_ids))) if user_ids else 0,
        "mfa_challenges": _count(MfaChallenge.query.filter(MfaChallenge.user_id.in_(user_ids))) if user_ids else 0,
        "audit_events_anonymized": _count(AuditEvent.query.filter(AuditEvent.user_id.in_(user_ids)))
        if user_ids
        else 0,
    }
    blockers = _positive_counts(blockers)
    return TrainingCleanupPlan(
        state="ready" if not problems and not blockers else "blocked",
        ready=not problems and not blockers,
        users=sorted(emails),
        records_to_remove=records_to_remove,
        blockers=blockers,
        problems=problems,
    )


def purge_training_data(confirmation):
    """Delete only the known acceptance fixtures after a fresh dependency check."""
    if confirmation != PURGE_CONFIRMATION:
        raise ValueError(f"confirmation must be exactly {PURGE_CONFIRMATION}")

    plan = build_training_cleanup_plan()
    if plan.state == "already_clean":
        return plan
    if not plan.ready:
        raise RuntimeError(f"training-data purge blocked: {plan.to_dict()}")

    users = User.query.filter(User.email.in_(TRAINING_EMAILS)).all()
    user_ids = [user.id for user in users]
    volunteers = Volunteer.query.filter(Volunteer.user_id.in_(user_ids)).all()
    volunteer_ids = [volunteer.id for volunteer in volunteers]
    hospital_ids = [item.id for item in Hospital.query.filter_by(name=TRAINING_HOSPITAL_NAME).all()]
    shelter_ids = [item.id for item in Shelter.query.filter_by(name=TRAINING_SHELTER_NAME).all()]
    ambulance_ids = [item.id for item in Ambulance.query.filter_by(vehicle_number=TRAINING_AMBULANCE_NUMBER).all()]

    try:
        Notification.query.filter(Notification.user_id.in_(user_ids)).delete(synchronize_session=False)
        AuthSession.query.filter(AuthSession.user_id.in_(user_ids)).delete(synchronize_session=False)
        AccountSecurity.query.filter(AccountSecurity.user_id.in_(user_ids)).delete(synchronize_session=False)
        MfaChallenge.query.filter(MfaChallenge.user_id.in_(user_ids)).delete(synchronize_session=False)
        MfaCredential.query.filter(MfaCredential.user_id.in_(user_ids)).delete(synchronize_session=False)
        AuditEvent.query.filter(AuditEvent.user_id.in_(user_ids)).update(
            {AuditEvent.user_id: None}, synchronize_session=False
        )
        Volunteer.query.filter(Volunteer.id.in_(volunteer_ids)).delete(synchronize_session=False)
        RoleProfile.query.filter(RoleProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
        User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)

        HospitalCapacityLog.query.filter(HospitalCapacityLog.hospital_id.in_(hospital_ids)).delete(
            synchronize_session=False
        )
        ShelterCapacityLog.query.filter(ShelterCapacityLog.shelter_id.in_(shelter_ids)).delete(
            synchronize_session=False
        )
        Ambulance.query.filter(Ambulance.id.in_(ambulance_ids)).delete(synchronize_session=False)
        Shelter.query.filter(Shelter.id.in_(shelter_ids)).delete(synchronize_session=False)
        Hospital.query.filter(Hospital.id.in_(hospital_ids)).delete(synchronize_session=False)
        db.session.add(
            AuditEvent(
                event_type="production_training_data_purged",
                outcome="success",
                details=(
                    f"Removed {len(user_ids)} marked acceptance accounts and "
                    f"{len(hospital_ids) + len(shelter_ids) + len(ambulance_ids)} marked facilities"
                ),
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return TrainingCleanupPlan(
        state="purged",
        ready=True,
        users=plan.users,
        records_to_remove=plan.records_to_remove,
    )
