from datetime import datetime, timezone

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


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
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    organization_name = db.Column(db.String(160))
    address = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    verification_status = db.Column(db.String(30), default="pending", nullable=False)
    user = db.relationship("User", backref="profile", uselist=False)


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
