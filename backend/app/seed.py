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
        name="Kavya Raman",
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
    db.session.commit()
