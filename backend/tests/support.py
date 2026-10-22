"""Sign-in helpers for the seeded sample accounts used by the test suite."""

SEEDED_PASSWORD = "DemoPassword123!"
SEEDED_EMAILS = {
    "Admin": "admin@rescue.local",
    "Citizen": "citizen@rescue.local",
    "Volunteer": "volunteer@rescue.local",
    "Hospital": "hospital@rescue.local",
    "Shelter": "shelter@rescue.local",
    "Ambulance": "ambulance@rescue.local",
    "NGO": "ngo@rescue.local",
    "Police": "police@rescue.local",
    "Fire Service": "fire@rescue.local",
}


def login_response(client, role):
    """Sign in as the seeded account for a role through the real password flow."""
    return client.post("/api/v1/auth/login", json={"email": SEEDED_EMAILS[role], "password": SEEDED_PASSWORD})


def bearer(client, role):
    response = login_response(client, role)
    assert response.status_code == 200, response.get_json()
    return {"Authorization": f"Bearer {response.get_json()['token']}"}
