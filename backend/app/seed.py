from .auth import hash_password
from .extensions import db
from .models import (
    Ambulance,
    Disaster,
    DisasterNewsUpdate,
    DonationCampaign,
    EmergencyAlert,
    Hospital,
    HospitalNotification,
    RescueRequest,
    Resource,
    ResponderUnit,
    Shelter,
    SupplyRequest,
    User,
    Volunteer,
    WelfareCheck,
)


def seed_demo_data():
    if User.query.first():
        seed_extended_demo_data()
        return

    admin = User(
        name="Incident Commander",
        email="admin@rescue.local",
        phone="9000000000",
        role="Admin",
        password_hash=hash_password("password123"),
    )
    citizen = User(
        name="Kavya Raman",
        email="citizen@rescue.local",
        phone="9000000001",
        role="Citizen",
        password_hash=hash_password("password123"),
    )
    demo_users = {
        "Volunteer": User(name="Ravi Kumar", email="volunteer@rescue.local", phone="9000000002", role="Volunteer", password_hash=hash_password("password123")),
        "Hospital": User(name="Hospital Duty Officer", email="hospital@rescue.local", phone="9000000003", role="Hospital", password_hash=hash_password("password123")),
        "Shelter": User(name="Shelter Coordinator", email="shelter@rescue.local", phone="9000000004", role="Shelter", password_hash=hash_password("password123")),
        "Ambulance": User(name="108 Dispatcher", email="ambulance@rescue.local", phone="9000000005", role="Ambulance", password_hash=hash_password("password123")),
        "NGO": User(name="Relief NGO Lead", email="ngo@rescue.local", phone="9000000006", role="NGO", password_hash=hash_password("password123")),
        "Police": User(name="Police Control Room", email="police@rescue.local", phone="9000000007", role="Police", password_hash=hash_password("password123")),
        "Fire Service": User(name="Fire Control Officer", email="fire@rescue.local", phone="9000000008", role="Fire Service", password_hash=hash_password("password123")),
    }
    volunteer_user = demo_users["Volunteer"]
    db.session.add_all([admin, citizen, *demo_users.values()])
    db.session.flush()

    disaster = Disaster(
        title="Flooding near Velachery lake bund",
        disaster_type="flood",
        description="Water level rising rapidly near low-lying streets and canals.",
        address="Velachery, Chennai",
        latitude=12.9798,
        longitude=80.2209,
        people_affected=320,
        severity_hint="high",
        reported_by_id=citizen.id,
    )
    hospital = Hospital(
        name="Rajiv Gandhi Govt General Hospital",
        address="Park Town, Chennai",
        latitude=13.0816,
        longitude=80.2761,
        total_beds=220,
        available_beds=52,
        icu_beds=10,
        emergency_capacity=36,
        contact_phone="0440000001",
    )
    shelter = Shelter(
        name="Velachery Govt School Relief Camp",
        address="Velachery, Chennai",
        latitude=12.9822,
        longitude=80.2218,
        total_capacity=700,
        available_capacity=420,
        food_available=True,
        medical_support=True,
        contact_phone="0440000002",
    )
    ambulance = Ambulance(
        vehicle_number="TN-01-ER-108",
        driver_name="Karthik Raj",
        phone="9000000108",
        latitude=13.0816,
        longitude=80.2761,
        status="available",
    )
    volunteer = Volunteer(
        user_id=volunteer_user.id,
        skills="first aid, evacuation, logistics",
        availability_status="available",
        latitude=12.982,
        longitude=80.222,
    )
    resources = [
        Resource(name="Rice Meal Packets", category="food", unit="packet", available_quantity=3200, storage_location="Chennai Corporation Warehouse"),
        Resource(name="ORS Sachets", category="medicine", unit="box", available_quantity=960, storage_location="Rajiv Gandhi Medical Depot"),
        Resource(name="Rescue Boats", category="rescue", unit="boat", available_quantity=14, storage_location="TNDRF Boat Yard"),
    ]
    db.session.add_all([disaster, hospital, shelter, ambulance, volunteer, *resources])
    db.session.flush()
    rescues = [
        RescueRequest(
            disaster_id=disaster.id,
            requester_id=citizen.id,
            victim_name="Meena Kumar",
            victim_age=8,
            people_count=3,
            condition="critical",
            trapped=True,
            vulnerable_people=1,
            latitude=12.9806,
            longitude=80.2194,
            priority_score=97,
            priority_label="Critical",
            status="assigned",
            assigned_unit="TNDRF Boat Unit 2",
            notes="Child and two adults stranded on a first-floor terrace.",
        ),
        RescueRequest(
            disaster_id=disaster.id,
            requester_id=citizen.id,
            victim_name="Fathima Banu",
            victim_age=31,
            people_count=5,
            condition="stable",
            trapped=False,
            vulnerable_people=0,
            latitude=12.9769,
            longitude=80.224,
            priority_score=43,
            priority_label="Medium",
            status="en route",
            assigned_unit="Greater Chennai Volunteer Team A",
            notes="Family needs relocation to the relief camp.",
        ),
    ]
    alert = EmergencyAlert(
        identifier="RESQ-DEMO-FLOOD-001",
        sender_id=admin.id,
        event="Urban flood warning",
        audience="Ward 176 - Velachery",
        channels="SMS + radio + volunteer relay",
        urgency="immediate",
        severity="severe",
        certainty="observed",
        message="Water is rising near the lake bund service road.",
        instruction="Move to Velachery Govt School Relief Camp and avoid the lake bund service road.",
    )
    db.session.add_all([*rescues, alert])
    db.session.commit()
    seed_extended_demo_data()


def seed_extended_demo_data():
    """Add feature-rich demo records without duplicating an existing database."""
    admin = User.query.filter_by(role="Admin").first()
    citizen = User.query.filter_by(role="Citizen").first()
    if not admin or not citizen:
        return

    incident_specs = [
        {
            "title": "Brahmaputra flooding isolates Dibrugarh villages",
            "disaster_type": "flood",
            "description": "River overflow has cut road access to several villages; boats and food packets are being mobilized.",
            "address": "Dibrugarh District, Assam",
            "latitude": 27.4728,
            "longitude": 94.9120,
            "people_affected": 840,
            "severity_hint": "critical",
        },
        {
            "title": "Cloudburst blocks access near Joshimath",
            "disaster_type": "landslide",
            "description": "Debris has blocked a mountain access road and isolated travellers in remote settlements.",
            "address": "Chamoli District, Uttarakhand",
            "latitude": 30.5553,
            "longitude": 79.5650,
            "people_affected": 126,
            "severity_hint": "high",
        },
        {
            "title": "Cyclone evacuation along Puri coast",
            "disaster_type": "cyclone",
            "description": "Coastal evacuation and shelter activation are underway ahead of severe wind and storm surge.",
            "address": "Puri District, Odisha",
            "latitude": 19.8135,
            "longitude": 85.8312,
            "people_affected": 1260,
            "severity_hint": "high",
        },
    ]
    incidents = {}
    for spec in incident_specs:
        incident = Disaster.query.filter_by(title=spec["title"]).first()
        if not incident:
            incident = Disaster(**spec, reported_by_id=citizen.id)
            db.session.add(incident)
            db.session.flush()
        incidents[incident.title] = incident

    responder_specs = [
        ("TNDRF Boat Rescue Unit 2", "professional rescue", "swift-water rescue, evacuation, first aid", "9000000201", 12.9820, 80.2220),
        ("NDRF Mountain Rescue Team North", "professional rescue", "rope rescue, landslide search, remote evacuation", "9000000202", 30.5560, 79.5660),
        ("Odisha Coastal Rescue Unit 4", "professional rescue", "cyclone evacuation, water rescue, shelter transfer", "9000000203", 19.8150, 85.8320),
        ("Assam SDRF River Rescue Team", "professional rescue", "boat rescue, flood logistics, medical evacuation", "9000000204", 27.4730, 94.9130),
    ]
    for name, unit_type, skills, phone, latitude, longitude in responder_specs:
        if not ResponderUnit.query.filter_by(name=name).first():
            db.session.add(ResponderUnit(name=name, unit_type=unit_type, skills=skills, contact_phone=phone, latitude=latitude, longitude=longitude))

    alert_specs = [
        ("RESQ-DEMO-ASSAM-001", incidents[incident_specs[0]["title"]], "Assam - Dibrugarh river belt", "Move to raised shelters. Do not cross flooded roads; call 112 if isolated."),
        ("RESQ-DEMO-UK-001", incidents[incident_specs[1]["title"]], "Uttarakhand - Chamoli / Joshimath", "Avoid blocked mountain roads and share device location when requesting rescue."),
        ("RESQ-DEMO-ODISHA-001", incidents[incident_specs[2]["title"]], "Odisha - Puri coastal blocks", "Complete evacuation to the nearest cyclone shelter and carry medicines and identity documents."),
    ]
    for identifier, incident, audience, instruction in alert_specs:
        if not EmergencyAlert.query.filter_by(identifier=identifier).first():
            db.session.add(
                EmergencyAlert(
                    identifier=identifier,
                    sender_id=admin.id,
                    event=incident.title,
                    audience=audience,
                    channels="SMS + radio + web + volunteer relay",
                    urgency="immediate",
                    severity="severe",
                    certainty="observed",
                    message=incident.description,
                    instruction=instruction,
                )
            )

    chennai_incident = Disaster.query.filter_by(title="Flooding near Velachery lake bund").first()
    news_specs = [
        (incidents[incident_specs[0]["title"]], "Live: boat teams enter isolated Dibrugarh villages", "Assam", "Dibrugarh", True),
        (incidents[incident_specs[1]["title"]], "Live: alternate rescue route opened near Joshimath", "Uttarakhand", "Chamoli", True),
        (incidents[incident_specs[2]["title"]], "Live: Puri shelters begin coastal intake", "Odisha", "Puri", True),
    ]
    if chennai_incident:
        news_specs.append((chennai_incident, "Live: Velachery flood rescue and relief corridor", "Tamil Nadu", "Chennai", True))
    for incident, headline, state, district, is_live in news_specs:
        existing_news = DisasterNewsUpdate.query.filter_by(disaster_id=incident.id).first()
        if existing_news:
            existing_news.is_live = is_live
            existing_news.stream_url = "https://www.youtube.com/@DDNews/live"
        elif not DisasterNewsUpdate.query.filter_by(headline=headline).first():
            db.session.add(
                DisasterNewsUpdate(
                    disaster_id=incident.id,
                    headline=headline,
                    summary=f"Verified operations update for {incident.address}. Follow local authority instructions and avoid unverified forwards.",
                    source_name="ResQ verified field desk",
                    stream_url="https://www.youtube.com/@DDNews/live" if is_live else None,
                    state=state,
                    district=district,
                    is_live=is_live,
                    is_verified=True,
                    published_by_id=admin.id,
                )
            )

    flood = Disaster.query.order_by(Disaster.id).first()
    if flood and not DonationCampaign.query.filter_by(title="National Emergency Rescue & Victim Relief Fund").first():
        db.session.add(
            DonationCampaign(
                disaster_id=flood.id,
                title="National Emergency Rescue & Victim Relief Fund",
                description="Funds verified rescue transport, emergency food, medical supplies, temporary shelter, and victim recovery support.",
                goal_amount=2500000,
                currency="INR",
                organizer="ResQ Command Relief Coalition",
            )
        )

    if flood and not SupplyRequest.query.filter_by(requester_id=citizen.id).first():
        db.session.add(
            SupplyRequest(
                requester_id=citizen.id,
                disaster_id=flood.id,
                category="food and water",
                description="Five residents isolated on an upper floor need drinking water, ready-to-eat food, and essential medicines.",
                people_count=5,
                urgency="high",
                contact_phone=citizen.phone,
                latitude=12.9806,
                longitude=80.2194,
                location_accuracy=18,
                status="assigned",
                assigned_unit="Greater Chennai Volunteer Team A",
            )
        )

    if flood and not WelfareCheck.query.filter_by(requester_id=citizen.id).first():
        db.session.add(
            WelfareCheck(
                requester_id=citizen.id,
                disaster_id=flood.id,
                relative_name="Anita Raman",
                relationship="Sister",
                last_known_location="Velachery lake bund service road",
                requester_phone=citizen.phone,
                consent_to_contact=True,
                status="contacting",
                responder_id=admin.id,
                responder_notes="Call responder is checking the shelter intake list and field-team registry.",
            )
        )

    rescue = RescueRequest.query.order_by(RescueRequest.id).first()
    hospital = Hospital.query.order_by(Hospital.id).first()
    if rescue and hospital and not HospitalNotification.query.filter_by(rescue_request_id=rescue.id).first():
        db.session.add(
            HospitalNotification(
                hospital_id=hospital.id,
                disaster_id=rescue.disaster_id,
                rescue_request_id=rescue.id,
                expected_patients=rescue.people_count,
                priority=rescue.priority_label,
                message=f"Prepare pediatric and emergency triage for {rescue.people_count} incoming patient(s) from rescue #{rescue.id}.",
            )
        )

    db.session.commit()
