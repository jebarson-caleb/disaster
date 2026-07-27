from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func, or_

from ..auth import current_user, login_required
from ..extensions import db
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
    ResponseDispatch,
    SupplyRequest,
    User,
    WelfareCheck,
)
from ..services.dispatch_service import auto_dispatch_rescue

community_bp = Blueprint("community", __name__)
FIELD_ROLES = {"Admin", "Police", "Fire Service", "NGO", "Hospital", "Shelter", "Ambulance", "Volunteer"}
CASE_RESPONDER_ROLES = {"Admin", "Police", "Fire Service", "NGO", "Volunteer"}
SUPPLY_COORDINATOR_ROLES = {"Admin", "NGO", "Shelter", "Police", "Fire Service"}


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
            "alerts": [item.to_dict() for item in alerts],
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
    db.get_or_404(Disaster, int(data["disaster_id"]))
    stream_url = str(data.get("stream_url") or "").strip() or None
    if stream_url and not stream_url.startswith(("https://", "http://")):
        return jsonify({"error": "stream_url must start with http:// or https://"}), 400
    update = DisasterNewsUpdate(
        disaster_id=int(data["disaster_id"]),
        headline=str(data["headline"]).strip(),
        summary=str(data["summary"]).strip(),
        source_name=str(data["source_name"]).strip(),
        stream_url=stream_url,
        state=str(data["state"]).strip(),
        district=str(data["district"]).strip(),
        is_live=bool(data.get("is_live")),
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
    disaster_id = int(data["disaster_id"]) if data.get("disaster_id") else None
    if disaster_id:
        db.get_or_404(Disaster, disaster_id)
    item = WelfareCheck(
        requester_id=request.user.id,
        disaster_id=disaster_id,
        relative_name=str(data["relative_name"]).strip(),
        relative_phone=str(data.get("relative_phone") or "").strip() or None,
        relationship=str(data["relationship"]).strip(),
        last_known_location=str(data["last_known_location"]).strip(),
        latitude=float(data["latitude"]) if data.get("latitude") not in {None, ""} else None,
        longitude=float(data["longitude"]) if data.get("longitude") not in {None, ""} else None,
        requester_phone=str(data["requester_phone"]).strip(),
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
    if status not in {"requested", "assigned", "contacting", "located_safe", "needs_help", "closed"}:
        return jsonify({"error": "Invalid welfare-check status"}), 400
    item.status = status
    item.responder_id = request.user.id
    if "responder_notes" in data:
        item.responder_notes = str(data["responder_notes"])
    db.session.commit()
    return jsonify({"welfare_check": welfare_payload(item)})


@community_bp.get("/hospital-notifications")
@login_required(roles=["Admin", "Hospital", "Ambulance"])
def list_hospital_notifications():
    items = HospitalNotification.query.order_by(HospitalNotification.created_at.desc()).limit(200).all()
    hospitals = {item.id: item for item in Hospital.query.all()}
    return jsonify({"hospital_notifications": [{**item.to_dict(), "hospital_name": hospitals[item.hospital_id].name} for item in items]})


@community_bp.patch("/hospital-notifications/<int:notification_id>/acknowledge")
@login_required(roles=["Admin", "Hospital"])
def acknowledge_hospital_notification(notification_id):
    item = db.get_or_404(HospitalNotification, notification_id)
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
    disaster = db.get_or_404(Disaster, int(data["disaster_id"]))
    item = SupplyRequest(
        requester_id=request.user.id,
        disaster_id=disaster.id,
        category=str(data["category"]).strip().lower(),
        description=str(data["description"]).strip(),
        people_count=max(1, int(data.get("people_count") or 1)),
        urgency=str(data.get("urgency") or "high").lower(),
        contact_phone=str(data["contact_phone"]).strip(),
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        location_accuracy=float(data["location_accuracy"]) if data.get("location_accuracy") not in {None, ""} else None,
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
    if status not in {"requested", "assigned", "packing", "en route", "delivered", "cancelled"}:
        return jsonify({"error": "Invalid supply-request status"}), 400
    item.status = status
    if "assigned_unit" in data:
        item.assigned_unit = str(data["assigned_unit"]).strip()
    if "responder_notes" in data:
        item.responder_notes = str(data["responder_notes"]).strip()
    db.session.commit()
    return jsonify({"supply_request": item.to_dict()})


@community_bp.get("/donation-campaigns")
def list_donation_campaigns():
    campaigns = DonationCampaign.query.filter_by(status="active").order_by(DonationCampaign.created_at.desc()).all()
    return jsonify({"campaigns": [campaign_payload(item) for item in campaigns]})


@community_bp.post("/donations")
def create_donation():
    data = request.get_json() or {}
    required = ["campaign_id", "donor_name", "donor_email", "amount"]
    missing = [field for field in required if data.get(field) in {None, ""}]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400
    campaign = db.get_or_404(DonationCampaign, int(data["campaign_id"]))
    if campaign.status != "active":
        return jsonify({"error": "This campaign is not accepting donations"}), 409
    try:
        amount = Decimal(str(data["amount"]))
    except InvalidOperation:
        return jsonify({"error": "amount must be a number"}), 400
    if amount < Decimal("10") or amount > Decimal("10000000"):
        return jsonify({"error": "amount must be between 10 and 10000000"}), 400
    user = current_user()
    payment_base = current_app.config.get("DONATION_PAYMENT_URL", "")
    reference = f"DON-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:10].upper()}"
    item = Donation(
        campaign_id=campaign.id,
        donor_id=user.id if user else None,
        donor_name=str(data["donor_name"]).strip(),
        donor_email=str(data["donor_email"]).strip().lower(),
        amount=amount,
        currency=campaign.currency,
        anonymous=bool(data.get("anonymous")),
        message=str(data.get("message") or "").strip() or None,
        reference=reference,
        status="pending_payment" if payment_base else "pledged",
    )
    db.session.add(item)
    db.session.commit()
    checkout_url = None
    if payment_base:
        separator = "&" if "?" in payment_base else "?"
        checkout_url = f"{payment_base}{separator}{urlencode({'reference': reference, 'amount': str(amount), 'currency': campaign.currency})}"
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
    db.session.commit()
    return jsonify({"donation": {**item.to_dict(), "amount": float(item.amount)}})


@community_bp.post("/location-pings")
@login_required()
def create_location_ping():
    data = request.get_json() or {}
    if data.get("consent_granted") is not True:
        return jsonify({"error": "Explicit location consent is required"}), 400
    if data.get("latitude") in {None, ""} or data.get("longitude") in {None, ""}:
        return jsonify({"error": "latitude and longitude are required"}), 400
    ping = LocationPing(
        user_id=request.user.id,
        rescue_request_id=int(data["rescue_request_id"]) if data.get("rescue_request_id") else None,
        supply_request_id=int(data["supply_request_id"]) if data.get("supply_request_id") else None,
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
        accuracy_meters=float(data["accuracy_meters"]) if data.get("accuracy_meters") not in {None, ""} else None,
        source=str(data.get("source") or "device"),
        consent_granted=True,
    )
    db.session.add(ping)
    db.session.commit()
    return jsonify({"location_ping": ping.to_dict()}), 201


@community_bp.post("/rescue-requests/<int:request_id>/auto-dispatch")
@login_required(roles=["Admin", "Police", "Fire Service", "Ambulance", "NGO"])
def auto_dispatch(request_id):
    rescue = db.get_or_404(RescueRequest, request_id)
    existing = ResponseDispatch.query.filter_by(rescue_request_id=rescue.id).all()
    if existing:
        return jsonify({"rescue_request": rescue.to_dict(), "dispatches": [item.to_dict() for item in existing], "already_dispatched": True})
    disaster = db.get_or_404(Disaster, rescue.disaster_id)
    allocation = auto_dispatch_rescue(rescue, disaster)
    db.session.commit()
    return jsonify({"rescue_request": rescue.to_dict(), "allocation": allocation, "already_dispatched": False})
