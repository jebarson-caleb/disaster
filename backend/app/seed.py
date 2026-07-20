from .auth import hash_password
from .extensions import db
from .models import Ambulance, Disaster, EmergencyAlert, Hospital, RescueRequest, Resource, Shelter, User, Volunteer


def seed_demo_data():
    if User.query.first():
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
