from pathlib import Path
from random import choice, randint, random, seed

seed(42)

roles = ["Citizen", "NGO", "Volunteer", "Police", "Hospital", "Fire Service", "Shelter", "Ambulance", "Admin"]
types = ["flood", "earthquake", "cyclone", "landslide", "fire"]
conditions = ["stable", "injured", "critical", "unconscious", "bleeding"]
districts = [
    "Chennai Ward",
    "Cuddalore Coastal Zone",
    "Nagapattinam Block",
    "Thanjavur Delta Ward",
    "Nilgiris Ghat Road",
    "Madurai Urban Ward",
    "Tiruchirappalli Zone",
    "Kanyakumari Coast",
]


def sql(value):
    return "'" + str(value).replace("'", "''") + "'"


def tn_lat():
    return 8.1 + random() * 5.4


def tn_lng():
    return 76.2 + random() * 4.2


lines = ["USE disaster_response;", "START TRANSACTION;"]

for i in range(1, 2501):
    role = choice(roles)
    lines.append(
        "INSERT INTO users (name, email, phone, role, password_hash) VALUES "
        f"({sql(f'Demo User {i}')}, {sql(f'user{i}@demo.local')}, {sql(9000000000 + i)}, {sql(role)}, 'demo-hash');"
    )

for i in range(1, 501):
    dtype = choice(types)
    lat = tn_lat()
    lng = tn_lng()
    lines.append(
        "INSERT INTO disasters (title, disaster_type, description, address, latitude, longitude, people_affected, severity_hint, reported_by_id) VALUES "
        f"({sql(f'{dtype.title()} incident #{i}')}, {sql(dtype)}, 'Generated Tamil Nadu capstone dataset incident.', {sql(f'{choice(districts)} {randint(1, 80)}')}, "
        f"{lat:.7f}, {lng:.7f}, {randint(5, 900)}, {sql(choice(['low', 'medium', 'high', 'critical']))}, {randint(1, 2500)});"
    )

for i in range(1, 1401):
    score = randint(20, 100)
    label = "Critical" if score >= 85 else "High" if score >= 65 else "Medium" if score >= 40 else "Low"
    lines.append(
        "INSERT INTO rescue_requests (disaster_id, requester_id, victim_name, victim_age, people_count, condition_label, trapped, vulnerable_people, latitude, longitude, status, priority_score, priority_label, notes) VALUES "
        f"({randint(1, 500)}, {randint(1, 2500)}, {sql(f'Victim {i}')}, {randint(1, 86)}, {randint(1, 9)}, {sql(choice(conditions))}, "
        f"{choice(['TRUE', 'FALSE'])}, {randint(0, 3)}, {tn_lat():.7f}, {tn_lng():.7f}, "
        f"{sql(choice(['pending', 'assigned', 'en route', 'rescued']))}, {score}, {sql(label)}, 'Generated rescue request.');"
    )

for i in range(1, 201):
    lines.append(
        "INSERT INTO hospitals (name, address, latitude, longitude, total_beds, available_beds, icu_beds, emergency_capacity, contact_phone) VALUES "
        f"({sql(f'Tamil Nadu Hospital {i}')}, {sql(f'{choice(districts)} Medical Road {i}')}, {tn_lat():.7f}, {tn_lng():.7f}, "
        f"{randint(50, 500)}, {randint(0, 160)}, {randint(0, 40)}, {randint(5, 80)}, {sql(8300000000 + i)});"
    )

for i in range(1, 251):
    lines.append(
        "INSERT INTO shelters (name, address, latitude, longitude, total_capacity, available_capacity, food_available, medical_support, contact_phone) VALUES "
        f"({sql(f'Tamil Nadu Relief Shelter {i}')}, {sql(f'{choice(districts)} School Zone {i}')}, {tn_lat():.7f}, {tn_lng():.7f}, "
        f"{randint(100, 1200)}, {randint(0, 700)}, TRUE, {choice(['TRUE', 'FALSE'])}, {sql(8400000000 + i)});"
    )

for i in range(1, 251):
    lines.append(
        "INSERT INTO ambulances (vehicle_number, driver_name, phone, latitude, longitude, status) VALUES "
        f"({sql(f'TN-{randint(1, 99):02d}-ER-{1000 + i}')}, {sql(f'Driver {i}')}, {sql(8500000000 + i)}, "
        f"{tn_lat():.7f}, {tn_lng():.7f}, {sql(choice(['available', 'dispatched', 'maintenance']))});"
    )

lines.append("COMMIT;")
Path("large_seed_5000_plus.sql").write_text("\n".join(lines), encoding="utf-8")
print("Wrote database/large_seed_5000_plus.sql with", len(lines) - 2, "insert statements")
