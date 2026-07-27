from datetime import UTC, datetime

from .extensions import db


def utcnow():
    return datetime.now(UTC)


class SerializerMixin:
    def to_dict(self):
        output = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            output[column.name] = value
        return output


class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    role = db.Column(db.String(40), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class RoleProfile(db.Model, SerializerMixin):
    __tablename__ = "role_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    organization_name = db.Column(db.String(160))
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), index=True)
    shelter_id = db.Column(db.Integer, db.ForeignKey("shelters.id"), index=True)
    ambulance_id = db.Column(db.Integer, db.ForeignKey("ambulances.id"), index=True)
    verification_status = db.Column(db.String(30), default="pending", nullable=False)
    user = db.relationship("User", backref=db.backref("profile", uselist=False))


class Disaster(db.Model, SerializerMixin):
    __tablename__ = "disasters"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    disaster_type = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    people_affected = db.Column(db.Integer, default=0, nullable=False)
    severity_hint = db.Column(db.String(30), default="medium", nullable=False)
    status = db.Column(db.String(30), default="active", index=True, nullable=False)
    image_url = db.Column(db.String(500))
    reported_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class RescueRequest(db.Model, SerializerMixin):
    __tablename__ = "rescue_requests"

    id = db.Column(db.Integer, primary_key=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    victim_name = db.Column(db.String(120), nullable=False)
    victim_age = db.Column(db.Integer, default=0, nullable=False)
    people_count = db.Column(db.Integer, default=1, nullable=False)
    condition = db.Column(db.String(80), default="stable", nullable=False)
    trapped = db.Column(db.Boolean, default=False, nullable=False)
    vulnerable_people = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(40), default="pending", index=True, nullable=False)
    priority_score = db.Column(db.Integer, default=0, index=True, nullable=False)
    priority_label = db.Column(db.String(30), default="Low", nullable=False)
    assigned_unit = db.Column(db.String(120))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    disaster = db.relationship("Disaster", backref="rescue_requests")


class RescueStatusHistory(db.Model, SerializerMixin):
    __tablename__ = "rescue_status_history"

    id = db.Column(db.Integer, primary_key=True)
    rescue_request_id = db.Column(db.Integer, db.ForeignKey("rescue_requests.id"), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False)
    note = db.Column(db.Text)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Hospital(db.Model, SerializerMixin):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    total_beds = db.Column(db.Integer, nullable=False)
    available_beds = db.Column(db.Integer, nullable=False)
    icu_beds = db.Column(db.Integer, default=0, nullable=False)
    emergency_capacity = db.Column(db.Integer, default=0, nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class HospitalCapacityLog(db.Model, SerializerMixin):
    __tablename__ = "hospital_capacity_logs"

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    available_beds = db.Column(db.Integer, nullable=False)
    icu_beds = db.Column(db.Integer, nullable=False)
    emergency_capacity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Shelter(db.Model, SerializerMixin):
    __tablename__ = "shelters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    total_capacity = db.Column(db.Integer, nullable=False)
    available_capacity = db.Column(db.Integer, nullable=False)
    food_available = db.Column(db.Boolean, default=True, nullable=False)
    medical_support = db.Column(db.Boolean, default=False, nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ShelterCapacityLog(db.Model, SerializerMixin):
    __tablename__ = "shelter_capacity_logs"

    id = db.Column(db.Integer, primary_key=True)
    shelter_id = db.Column(db.Integer, db.ForeignKey("shelters.id"), nullable=False, index=True)
    available_capacity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Ambulance(db.Model, SerializerMixin):
    __tablename__ = "ambulances"

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(40), unique=True, nullable=False)
    driver_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="available", index=True, nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"))
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AmbulanceDispatch(db.Model, SerializerMixin):
    __tablename__ = "ambulance_dispatches"

    id = db.Column(db.Integer, primary_key=True)
    ambulance_id = db.Column(db.Integer, db.ForeignKey("ambulances.id"), nullable=False)
    rescue_request_id = db.Column(db.Integer, db.ForeignKey("rescue_requests.id"), nullable=False)
    status = db.Column(db.String(30), default="dispatched", nullable=False)
    dispatched_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Resource(db.Model, SerializerMixin):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)
    unit = db.Column(db.String(30), nullable=False)
    available_quantity = db.Column(db.Integer, default=0, nullable=False)
    storage_location = db.Column(db.String(160), nullable=False)


class ResourceDistribution(db.Model, SerializerMixin):
    __tablename__ = "resource_distribution"

    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=False)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    destination = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(30), default="planned", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Volunteer(db.Model, SerializerMixin):
    __tablename__ = "volunteers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skills = db.Column(db.String(255), nullable=False)
    availability_status = db.Column(db.String(30), default="available", index=True, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)


class VolunteerAssignment(db.Model, SerializerMixin):
    __tablename__ = "volunteer_assignments"

    id = db.Column(db.Integer, primary_key=True)
    volunteer_id = db.Column(db.Integer, db.ForeignKey("volunteers.id"), nullable=False)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False)
    task = db.Column(db.String(180), nullable=False)
    status = db.Column(db.String(30), default="assigned", nullable=False)
    assigned_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class AiAssessment(db.Model, SerializerMixin):
    __tablename__ = "ai_assessments"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(40), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    assessment_type = db.Column(db.String(60), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(40), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class Notification(db.Model, SerializerMixin):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    role = db.Column(db.String(40), index=True)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="unread", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class EmergencyAlert(db.Model, SerializerMixin):
    """CAP-inspired authoritative warning distributed over multiple channels."""

    __tablename__ = "emergency_alerts"

    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(80), unique=True, nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event = db.Column(db.String(100), nullable=False)
    audience = db.Column(db.String(180), nullable=False, index=True)
    channels = db.Column(db.String(180), nullable=False)
    urgency = db.Column(db.String(30), default="immediate", nullable=False)
    severity = db.Column(db.String(30), default="severe", nullable=False)
    certainty = db.Column(db.String(30), default="likely", nullable=False)
    message = db.Column(db.Text, nullable=False)
    instruction = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="active", nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True))


class AlertAcknowledgement(db.Model, SerializerMixin):
    __tablename__ = "alert_acknowledgements"
    __table_args__ = (db.UniqueConstraint("alert_id", "user_id", name="uq_alert_user_ack"),)

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("emergency_alerts.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    response = db.Column(db.String(30), default="received", nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class DisasterNewsUpdate(db.Model, SerializerMixin):
    """Verified field update or external live-news stream for an incident."""

    __tablename__ = "disaster_news_updates"

    id = db.Column(db.Integer, primary_key=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False, index=True)
    headline = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    source_name = db.Column(db.String(120), nullable=False)
    stream_url = db.Column(db.String(500))
    state = db.Column(db.String(100), nullable=False, index=True)
    district = db.Column(db.String(100), nullable=False, index=True)
    is_live = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_verified = db.Column(db.Boolean, default=True, nullable=False)
    published_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    published_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class WelfareCheck(db.Model, SerializerMixin):
    """Family tracing request handled by an authorized call responder."""

    __tablename__ = "welfare_checks"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), index=True)
    relative_name = db.Column(db.String(120), nullable=False, index=True)
    relative_phone = db.Column(db.String(30))
    relationship = db.Column(db.String(80), nullable=False)
    last_known_location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    requester_phone = db.Column(db.String(30), nullable=False)
    consent_to_contact = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(40), default="requested", nullable=False, index=True)
    responder_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    responder_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class HospitalNotification(db.Model, SerializerMixin):
    """Advance notice for a receiving hospital to prepare beds and triage."""

    __tablename__ = "hospital_notifications"

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False, index=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False, index=True)
    rescue_request_id = db.Column(db.Integer, db.ForeignKey("rescue_requests.id"), nullable=False, index=True)
    expected_patients = db.Column(db.Integer, default=1, nullable=False)
    priority = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="sent", nullable=False, index=True)
    acknowledged_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    acknowledged_at = db.Column(db.DateTime(timezone=True))


class SupplyRequest(db.Model, SerializerMixin):
    """Food, water, medicine, or essential-supply request from an isolated group."""

    __tablename__ = "supply_requests"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    people_count = db.Column(db.Integer, default=1, nullable=False)
    urgency = db.Column(db.String(30), default="high", nullable=False, index=True)
    contact_phone = db.Column(db.String(30), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_accuracy = db.Column(db.Float)
    status = db.Column(db.String(40), default="requested", nullable=False, index=True)
    assigned_unit = db.Column(db.String(160))
    responder_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class DonationCampaign(db.Model, SerializerMixin):
    __tablename__ = "donation_campaigns"

    id = db.Column(db.Integer, primary_key=True)
    disaster_id = db.Column(db.Integer, db.ForeignKey("disasters.id"), index=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal_amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), default="INR", nullable=False)
    status = db.Column(db.String(30), default="active", nullable=False, index=True)
    organizer = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True))


class Donation(db.Model, SerializerMixin):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("donation_campaigns.id"), nullable=False, index=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    donor_name = db.Column(db.String(120), nullable=False)
    donor_email = db.Column(db.String(160), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    currency = db.Column(db.String(10), default="INR", nullable=False)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)
    message = db.Column(db.String(500))
    reference = db.Column(db.String(80), unique=True, nullable=False, index=True)
    status = db.Column(db.String(30), default="pledged", nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class LocationPing(db.Model, SerializerMixin):
    """Consent-based device location shared with responders."""

    __tablename__ = "location_pings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rescue_request_id = db.Column(db.Integer, db.ForeignKey("rescue_requests.id"), index=True)
    supply_request_id = db.Column(db.Integer, db.ForeignKey("supply_requests.id"), index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy_meters = db.Column(db.Float)
    source = db.Column(db.String(30), default="device", nullable=False)
    consent_granted = db.Column(db.Boolean, nullable=False)
    recorded_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class ResponseDispatch(db.Model, SerializerMixin):
    """Auditable automatic proximity allocation for rescue responders."""

    __tablename__ = "response_dispatches"

    id = db.Column(db.Integer, primary_key=True)
    rescue_request_id = db.Column(db.Integer, db.ForeignKey("rescue_requests.id"), nullable=False, index=True)
    responder_type = db.Column(db.String(40), nullable=False, index=True)
    responder_id = db.Column(db.Integer, nullable=False)
    responder_name = db.Column(db.String(160), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default="assigned", nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class ResponderUnit(db.Model, SerializerMixin):
    """Registered professional rescue, fire, police, or medical field unit."""

    __tablename__ = "responder_units"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False)
    unit_type = db.Column(db.String(50), nullable=False, index=True)
    skills = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    availability_status = db.Column(db.String(30), default="available", nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AuthSession(db.Model, SerializerMixin):
    """Revocable server-side login session referenced by an opaque cookie."""

    __tablename__ = "auth_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    csrf_hash = db.Column(db.String(64), nullable=False)
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    idle_expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    absolute_expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime(timezone=True), index=True)
    mfa_state = db.Column(db.String(30), default="not_required", nullable=False, index=True)


class AccountSecurity(db.Model, SerializerMixin):
    """Authentication state kept separate from the legacy users table."""

    __tablename__ = "account_security"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True), index=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    password_changed_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)


class AuditEvent(db.Model, SerializerMixin):
    """Minimal security/operations audit trail without credentials or sensitive payloads."""

    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    outcome = db.Column(db.String(30), nullable=False, index=True)
    request_id = db.Column(db.String(64), index=True)
    details = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)


class MfaCredential(db.Model, SerializerMixin):
    """Encrypted TOTP seed and one-time recovery-code hashes."""

    __tablename__ = "mfa_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    secret_ciphertext = db.Column(db.String(500), nullable=False)
    recovery_code_hashes = db.Column(db.Text, nullable=False, default="[]")
    enabled_at = db.Column(db.DateTime(timezone=True), index=True)
    last_used_step = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)


class MfaChallenge(db.Model, SerializerMixin):
    """Short-lived, single-use proof that the password factor succeeded."""

    __tablename__ = "mfa_challenges"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    consumed_at = db.Column(db.DateTime(timezone=True), index=True)
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
