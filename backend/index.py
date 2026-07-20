"""Vercel Services entry point for the Flask backend."""

from app import create_app
from app.extensions import db
from app.seed import seed_demo_data


app = create_app()

# Vercel's no-configuration demo database lives in writable /tmp storage.
# When DATABASE_URL is configured, the same initialization targets the
# persistent MySQL or PostgreSQL database instead.
with app.app_context():
    db.create_all()
    if app.config["DEMO_MODE"]:
        seed_demo_data()
