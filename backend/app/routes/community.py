from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, or_

from .. import validation
from ..auth import audit_event, authenticated_rate_key, current_user, login_required
from ..extensions import db, limiter
from ..models import (
    Disaster,
    DisasterNewsUpdate,
    Donation,
    DonationCampaign,
    EmergencyAlert,
    Hospital,
    HospitalNotification,
    LocationPing,
    Notification,
    RescueRequest,
    ResponderUnit,
    ResponseDispatch,
    RoleProfile,
    SupplyRequest,
    User,
    WelfareCheck,
)
from ..services.dispatch_service import auto_dispatch_rescue

community_bp = Blueprint("community", __name__)
FIELD_ROLES = {"Admin", "Police", "Fire Service", "NGO", "Hospital", "Shelter", "Ambulance", "Volunteer"}
CASE_RESPONDER_ROLES = {"Admin", "Police", "Fire Service", "NGO", "Volunteer"}
SUPPLY_COORDINATOR_ROLES = {"Admin", "NGO", "Shelter", "Police", "Fire Service"}
WELFARE_STATUSES = {"requested", "assigned", "contacting", "located_safe", "needs_help", "closed"}
SUPPLY_STATUSES = {"requested", "assigned", "packing", "en route", "delivered", "cancelled"}
SUPPLY_URGENCIES = {"medium", "high", "critical"}


def campaign_payload(campaign):
    totals = dict(
        db.session.query(Donation.status, func.coalesce(func.sum(Donation.amount), 0))
        .filter_by(campaign_id=campaign.id)
        .group_by(Donation.status)
        .all()
    )
    confirmed = float(totals.get("confirmed", 0) or 0)
    pledged = float(totals.get("pledged", 0) or 0) + float(totals.get("pending_payment", 0) or 0)
    goal = float(campaign.goal_amount)
    return {
        **campaign.to_dict(),
        "goal_amount": goal,
        "confirmed_amount": confirmed,
        "pledged_amount": pledged,
        "progress_percent": round(min(100, confirmed / goal * 100), 1) if goal else 0,
        "donor_count": Donation.query.filter_by(campaign_id=campaign.id).count(),
    }


def welfare_payload(item):
    responder = db.session.get(User, item.responder_id) if item.responder_id else None
    return {
        **item.to_dict(),
        "responder_name": responder.name if responder else None,
        "hotline": current_app.config.get("EMERGENCY_HOTLINE", "112"),
        "call_url": f"tel:{current_app.config.get('EMERGENCY_HOTLINE', '112')}",
    }


@community_bp.get("/national-alerts")
def national_alerts():
    """Public country-wide incident, warning, and verified-news feed."""
    now = datetime.now(UTC)
    alerts = (
        EmergencyAlert.query.filter_by(status="active")
        .filter(or_(EmergencyAlert.expires_at.is_(None), EmergencyAlert.expires_at > now))
        .order_by(EmergencyAlert.created_at.desc())
        .limit(100)
        .all()
    )
    disasters = Disaster.query.filter(Disaster.status.in_(["active", "monitoring"])).order_by(Disaster.created_at.desc()).limit(200).all()
    news = DisasterNewsUpdate.query.order_by(DisasterNewsUpdate.is_live.desc(), DisasterNewsUpdate.published_at.desc()).limit(100).all()
    return jsonify(
        {
            "country": "India",
            "alerts": [item.public_dict() for item in alerts],
            "disasters": [item.to_dict() for item in disasters],
            "news_updates": [item.to_dict() for item in news],
            "generated_at": now.isoformat(),
        }
    )


@community_bp.get("/news-updates")
def list_news_updates():
    query = DisasterNewsUpdate.query.order_by(DisasterNewsUpdate.is_live.desc(), DisasterNewsUpdate.published_at.desc())
    disaster_id = request.args.get("disaster_id", type=int)
    if disaster_id:
        query = query.filter_by(disaster_id=disaster_id)
    return jsonify({"news_updates": [item.to_dict() for item in query.limit(100).all()]})


@community_bp.post("/news-updates")
@login_required(roles=list(FIELD_ROLES))
def create_news_update():
    data = request.get_json() or {}
    missing = [field for field in ["disaster_id", "headline", "summary", "source_name", "state", "district"] if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    disaster_id = validation.whole_number(data["disaster_id"], "disaster_id", minimum=1, maximum=2**31 - 1)
    db.get_or_404(Disaster, disaster_id)
    update = DisasterNewsUpdate(
        disaster_id=disaster_id,
        headline=validation.text(data, "headline", 200),
        summary=validation.text(data, "summary", 4000),
        source_name=validation.text(data, "source_name", 120),
        stream_url=validation.http_url(data.get("stream_url"), "stream_url"),
        state=validation.text(data, "state", 100),
        district=validation.text(data, "district", 100),
        is_live=data.get("is_live") is True,
        is_verified=True,
        published_by_id=request.user.id,
    )
    db.session.add(update)
    db.session.commit()
    return jsonify({"news_update": update.to_dict()}), 201


@community_bp.get("/welfare-checks")
@login_required()
def list_welfare_checks():
    query = WelfareCheck.query.order_by(WelfareCheck.created_at.desc())
    if request.user.role not in CASE_RESPONDER_ROLES:
        query = query.filter_by(requester_id=request.user.id)
    return jsonify({"welfare_checks": [welfare_payload(item) for item in query.limit(200).all()]})


@community_bp.post("/welfare-checks")
@login_required()
def create_welfare_check():
    data = request.get_json() or {}
    required = ["relative_name", "relationship", "last_known_location", "requester_phone"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    if data.get("consent_to_contact") is not True:
        return jsonify({"error": "Consent to contact is required"}), 400
    disaster_id = (
        validation.whole_number(data["disaster_id"], "disaster_id", minimum=1, maximum=2**31 - 1)
        if data.get("disaster_id")
        else None
    )
    if disaster_id:
        db.get_or_404(Disaster, disaster_id)
    item = WelfareCheck(
        requester_id=request.user.id,
        disaster_id=disaster_id,
        relative_name=validation.text(data, "relative_name", 120),
        relative_phone=validation.optional_text(data, "relative_phone", 30),
        relationship=validation.text(data, "relationship", 80),
        last_known_location=validation.text(data, "last_known_location", 255),
        latitude=validation.optional_latitude(data.get("latitude")),
        longitude=validation.optional_longitude(data.get("longitude")),
        requester_phone=validation.text(data, "requester_phone", 30),
        consent_to_contact=True,
    )
    db.session.add(item)
    db.session.add(Notification(role="Police", message=f"New family welfare check for {item.relative_name} at {item.last_known_location}"))
    db.session.commit()
    return jsonify({"welfare_check": welfare_payload(item)}), 201


@community_bp.patch("/welfare-checks/<int:check_id>")
@login_required(roles=list(CASE_RESPONDER_ROLES))
def update_welfare_check(check_id):
    item = db.get_or_404(WelfareCheck, check_id)
    data = request.get_json() or {}
    status = data.get("status", item.status)
    if status not in WELFARE_STATUSES:
        return jsonify({"error": "Invalid welfare-check status"}), 400
    item.status = status
    item.responder_id = request.user.id
    if "responder_notes" in data:
        item.responder_notes = validation.optional_text(data, "responder_notes", 2000)
    db.session.commit()
    return jsonify({"welfare_check": welfare_payload(item)})


@community_bp.get("/hospital-notifications")
@login_required(roles=["Admin", "Hospital", "Ambulance"])
def list_hospital_notifications():
    query = HospitalNotification.query.order_by(HospitalNotification.created_at.desc())
    profile = RoleProfile.query.filter_by(user_id=request.user.id).first()
    if request.user.role == "Hospital":
        query = query.filter_by(hospital_id=profile.hospital_id if profile else None)
    elif request.user.role == "Ambulance":
        rescue_ids = ResponseDispatch.query.with_entities(ResponseDispatch.rescue_request_id).filter_by(
            responder_type="ambulance",
            responder_id=profile.ambulance_id if profile else None,
        )
        query = query.filter(HospitalNotification.rescue_request_id.in_(rescue_ids))
    items = query.limit(200).all()
    hospitals = {item.id: item for item in Hospital.query.all()}
    return jsonify({"hospital_notifications": [{**item.to_dict(), "hospital_name": hospitals[item.hospital_id].name} for item in items]})


@community_bp.patch("/hospital-notifications/<int:notification_id>/acknowledge")
@login_required(roles=["Admin", "Hospital"])
def acknowledge_hospital_notification(notification_id):
    item = db.get_or_404(HospitalNotification, notification_id)
    if request.user.role == "Hospital":
        profile = RoleProfile.query.filter_by(user_id=request.user.id).first()
        if profile is None or profile.hospital_id != item.hospital_id:
            return jsonify({"error": "You can acknowledge only notifications for your assigned hospital"}), 403
    item.status = "acknowledged"
    item.acknowledged_by_id = request.user.id
    item.acknowledged_at = datetime.now(UTC)
    db.session.commit()
    return jsonify({"hospital_notification": item.to_dict()})


@community_bp.get("/supply-requests")
@login_required()
def list_supply_requests():
    query = SupplyRequest.query.order_by(SupplyRequest.created_at.desc())
    if request.user.role not in SUPPLY_COORDINATOR_ROLES:
        query = query.filter_by(requester_id=request.user.id)
    return jsonify({"supply_requests": [item.to_dict() for item in query.limit(200).all()]})


@community_bp.post("/supply-requests")
@login_required()
def create_supply_request():
    data = request.get_json() or {}
    required = ["disaster_id", "category", "description", "contact_phone", "latitude", "longitude"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    disaster = db.get_or_404(
        Disaster, validation.whole_number(data["disaster_id"], "disaster_id", minimum=1, maximum=2**31 - 1)
    )
    item = SupplyRequest(
        requester_id=request.user.id,
        disaster_id=disaster.id,
        category=validation.text(data, "category", 60).lower(),
        description=validation.text(data, "description", 2000),
        people_count=validation.optional_whole_number(data.get("people_count"), "people_count", minimum=1, maximum=100_000, default=1),
        urgency=validation.choice(data, "urgency", SUPPLY_URGENCIES, default="high"),
        contact_phone=validation.text(data, "contact_phone", 30),
        latitude=validation.latitude(data["latitude"]),
        longitude=validation.longitude(data["longitude"]),
        location_accuracy=validation.coordinate(data["location_accuracy"], "location_accuracy", 0, 100_000)
        if data.get("location_accuracy") not in {None, ""}
        else None,
    )
    db.session.add(item)
    db.session.flush()
    if data.get("location_consent") is True:
        db.session.add(LocationPing(user_id=request.user.id, supply_request_id=item.id, latitude=item.latitude, longitude=item.longitude, accuracy_meters=item.location_accuracy, consent_granted=True))
    db.session.add(Notification(role="NGO", message=f"Urgent {item.category} request for {item.people_count} people near {disaster.address}"))
    db.session.add(Notification(role="Shelter", message=f"Supply support requested near {disaster.title}: {item.description}"))
    db.session.commit()
    return jsonify({"supply_request": item.to_dict(), "hotline": current_app.config.get("EMERGENCY_HOTLINE", "112")}), 201


@community_bp.patch("/supply-requests/<int:supply_id>")
@login_required(roles=list(SUPPLY_COORDINATOR_ROLES))
def update_supply_request(supply_id):
    item = db.get_or_404(SupplyRequest, supply_id)
    data = request.get_json() or {}
    status = data.get("status", item.status)
    if status not in SUPPLY_STATUSES:
        return jsonify({"error": "Invalid supply-request status"}), 400
    assigned_unit = item.assigned_unit
    selected_unit = ResponderUnit.query.filter_by(name=assigned_unit).first() if assigned_unit else None
    if "assigned_unit" in data:
        assigned_unit = str(data["assigned_unit"]).strip()
        if not assigned_unit:
            return jsonify({"error": "assigned_unit must not be blank"}), 400
        candidate = ResponderUnit.query.filter_by(name=assigned_unit).first()
        if candidate is None:
            return jsonify({"error": "assigned_unit must match a registered responder unit"}), 400
        if item.assigned_unit != assigned_unit and candidate.availability_status != "available":
            return jsonify({"error": "The selected responder unit is not available"}), 409
        if selected_unit is not None and selected_unit.id != candidate.id:
            selected_unit.availability_status = "available"
        selected_unit = candidate
    if status in {"assigned", "packing", "en route", "delivered"} and not assigned_unit:
        return jsonify({"error": "Assign a registered responder unit before advancing this request"}), 400
    if selected_unit is not None:
        selected_unit.availability_status = "available" if status in {"delivered", "cancelled"} else "dispatched"
    item.status = status
    item.assigned_unit = assigned_unit
    if "responder_notes" in data:
        item.responder_notes = validation.optional_text(data, "responder_notes", 2000)
    db.session.commit()
    return jsonify(
        {
            "supply_request": item.to_dict(),
            "responder_unit": selected_unit.to_dict() if selected_unit is not None else None,
        }
    )


@community_bp.get("/donation-campaigns")
def list_donation_campaigns():
    campaigns = DonationCampaign.query.filter_by(status="active").order_by(DonationCampaign.created_at.desc()).all()
    return jsonify({"campaigns": [campaign_payload(item) for item in campaigns]})


@community_bp.post("/donations")
@limiter.limit("10 per hour")
def create_donation():
    data = request.get_json() or {}
    required = ["campaign_id", "donor_name", "donor_email", "amount"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    campaign = db.get_or_404(
        DonationCampaign, validation.whole_number(data["campaign_id"], "campaign_id", minimum=1, maximum=2**31 - 1)
    )
    if campaign.status != "active":
        return jsonify({"error": "This campaign is not accepting donations"}), 409
    try:
        amount = Decimal(str(data["amount"]))
    except (InvalidOperation, ValueError):
        return jsonify({"error": "amount must be a number"}), 400
    if not amount.is_finite() or amount < Decimal("10") or amount > Decimal("10000000"):
        return jsonify({"error": "amount must be between 10 and 10000000"}), 400
    donor_name = str(data["donor_name"]).strip()
    donor_email = str(data["donor_email"]).strip().lower()
    if not donor_name or len(donor_name) > 120:
        return jsonify({"error": "A donor name of 120 characters or fewer is required"}), 400
    if not _valid_email(donor_email):
        return jsonify({"error": "A valid donor email is required"}), 400
    user = current_user()
    payment_base = current_app.config.get("DONATION_PAYMENT_URL", "")
    reference = f"DON-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:10].upper()}"
    item = Donation(
        campaign_id=campaign.id,
        donor_id=user.id if user else None,
        donor_name=donor_name,
        donor_email=donor_email,
        amount=amount,
        currency=campaign.currency,
        anonymous=bool(data.get("anonymous")),
        message=validation.optional_text(data, "message", 500),
        reference=reference,
        status="pending_payment" if payment_base else "pledged",
    )
    db.session.add(item)
    db.session.commit()
    checkout_url = None
    if payment_base:
        checkout_url = _checkout_url(
            payment_base,
            {
                "reference": reference,
                "amount": str(amount),
                "currency": campaign.currency,
            },
        )
    return jsonify(
        {
            "donation": {**item.to_dict(), "amount": float(item.amount)},
            "checkout_url": checkout_url,
            "payment_required": bool(payment_base),
            "message": "Pledge recorded. Complete payment using the checkout link." if payment_base else "Pledge recorded. Configure DONATION_PAYMENT_URL to collect online payment.",
        }
    ), 201


@community_bp.patch("/donations/<int:donation_id>/status")
@login_required(roles=["Admin"])
def update_donation_status(donation_id):
    item = db.get_or_404(Donation, donation_id)
    status = (request.get_json() or {}).get("status")
    if status not in {"pledged", "pending_payment", "confirmed", "failed", "refunded"}:
        return jsonify({"error": "Invalid donation status"}), 400
    item.status = status
    audit_event(
        "donation.status_update",
        "success",
        request.user.id,
        f"donation_id={item.id};status={status}",
    )
    db.session.commit()
    return jsonify({"donation": {**item.to_dict(), "amount": float(item.amount)}})


@community_bp.post("/location-pings")
@login_required()
@limiter.limit("120 per hour", key_func=authenticated_rate_key)
def create_location_ping():
    data = request.get_json() or {}
    if data.get("consent_granted") is not True:
        return jsonify({"error": "Explicit location consent is required"}), 400
    if data.get("latitude") in {None, ""} or data.get("longitude") in {None, ""}:
        return jsonify({"error": "latitude and longitude are required"}), 400
    rescue_request_id = _owned_case_id(RescueRequest, data.get("rescue_request_id"))
    supply_request_id = _owned_case_id(SupplyRequest, data.get("supply_request_id"))
    ping = LocationPing(
        user_id=request.user.id,
        rescue_request_id=rescue_request_id,
        supply_request_id=supply_request_id,
        latitude=validation.latitude(data["latitude"]),
        longitude=validation.longitude(data["longitude"]),
        accuracy_meters=validation.coordinate(data["accuracy_meters"], "accuracy_meters", 0, 100_000)
        if data.get("accuracy_meters") not in {None, ""}
        else None,
        source=validation.choice(data, "source", {"device", "manual"}, default="device"),
        consent_granted=True,
    )
    db.session.add(ping)
    db.session.commit()
    return jsonify({"location_ping": ping.to_dict()}), 201


@community_bp.post("/rescue-requests/<int:request_id>/auto-dispatch")
@login_required(roles=["Admin", "Police", "Fire Service", "NGO"])
def auto_dispatch(request_id):
    rescue = db.get_or_404(RescueRequest, request_id)
    existing = ResponseDispatch.query.filter_by(rescue_request_id=rescue.id).all()
    if existing:
        return jsonify({"rescue_request": rescue.to_dict(), "dispatches": [item.to_dict() for item in existing], "already_dispatched": True})
    disaster = db.get_or_404(Disaster, rescue.disaster_id)
    allocation = auto_dispatch_rescue(rescue, disaster)
    db.session.commit()
    return jsonify({"rescue_request": rescue.to_dict(), "allocation": allocation, "already_dispatched": False})


def _owned_case_id(model, value):
    if value in {None, ""}:
        return None
    item = db.get_or_404(model, validation.whole_number(value, "case id", minimum=1, maximum=2**31 - 1))
    if item.requester_id != request.user.id:
        raise ValueError("Location can be attached only to your own request")
    return item.id


def _checkout_url(base_url, parameters):
    parsed = urlsplit(base_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(parameters)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def _valid_email(value):
    email = str(value or "")
    if len(email) > 160 or any(character.isspace() for character in email):
        return False
    local, separator, domain = email.rpartition("@")
    return bool(separator and local and "." in domain and not domain.startswith(".") and not domain.endswith("."))
