from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .extensions import db
from .routes.admin import admin_bp
from .routes.ai import ai_bp
from .routes.auth import auth_bp
from .routes.disasters import disasters_bp
from .routes.facilities import facilities_bp


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(disasters_bp, url_prefix="/api/v1")
    app.register_blueprint(facilities_bp, url_prefix="/api/v1")
    app.register_blueprint(ai_bp, url_prefix="/api/v1/ai")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok", "service": "disaster-response-api"})

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": str(error.description or "Bad request")}), 400

    return app
