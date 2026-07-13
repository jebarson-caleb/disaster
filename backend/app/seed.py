from .auth import hash_password
from .extensions import db
from .models import Ambulance, Disaster, Hospital, Resource, Shelter, User, Volunteer


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
        name="Asha Nair",
        email="citizen@rescue.local",
        phone="9000000001",
        role="Citizen",
        password_hash=hash_password("password123"),
    )
    volunteer_user = User(
        name="Ravi Kumar",
        email="volunteer@rescue.local",
        phone="9000000002",
        role="Volunteer",
        password_hash=hash_password("password123"),
    )
    db.session.add_all([admin, citizen, volunteer_user])
    db.session.flush()

    disaster = Disaster(
        title="Flooding near Riverside Colony",
        disaster_type="flood",
        description="Water level rising rapidly near low-lying homes.",
        address="Riverside Colony, Kochi",
        latitude=9.9312,
        longitude=76.2673,
        people_affected=240,
        severity_hint="high",
        reported_by_id=citizen.id,
    )
    hospital = Hospital(
        name="City Emergency Hospital",
        address="MG Road, Kochi",
        latitude=9.9668,
        longitude=76.2870,
        total_beds=180,
        available_beds=42,
        icu_beds=8,
        emergency_capacity=30,
        contact_phone="0484000001",
    )
    shelter = Shelter(
        name="Govt Higher Secondary Relief Camp",
        address="Panampilly Nagar, Kochi",
        latitude=9.9515,
        longitude=76.2998,
        total_capacity=600,
        available_capacity=310,
        food_available=True,
        medical_support=True,
        contact_phone="0484000002",
    )
    ambulance = Ambulance(
        vehicle_number="KL-07-ER-108",
        driver_name="Nikhil Das",
        phone="9000000108",
        latitude=9.9668,
        longitude=76.2870,
        status="available",
    )
    volunteer = Volunteer(
        user_id=volunteer_user.id,
        skills="first aid, evacuation, logistics",
        availability_status="available",
        latitude=9.952,
        longitude=76.29,
    )
    resources = [
        Resource(name="Food Packets", category="food", unit="packet", available_quantity=2500, storage_location="Central Warehouse"),
        Resource(name="ORS Sachets", category="medicine", unit="box", available_quantity=800, storage_location="Medical Depot"),
        Resource(name="Rescue Boats", category="rescue", unit="boat", available_quantity=12, storage_location="Fire Station Dock"),
    ]
    db.session.add_all([disaster, hospital, shelter, ambulance, volunteer, *resources])
    db.session.commit()
