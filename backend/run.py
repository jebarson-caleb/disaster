from app import create_app
from app.bootstrap import initialize_database

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("APP_ENV") == "development")
