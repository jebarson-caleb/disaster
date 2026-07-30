import logging
import re
from uuid import uuid4

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from .auth import enforce_csrf
from .config import Config, production_configuration_issues
from .extensions import db, limiter, migrate
from .routes.admin import admin_bp
from .routes.ai import ai_bp
from .routes.auth import auth_bp
from .routes.community import community_bp
from .routes.disasters import disasters_bp
from .routes.facilities import facilities_bp
from .routes.operations import operations_bp

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    if app.config.get("TRUST_PROXY_HEADERS"):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", [])}},
        supports_credentials=app.config.get("CORS_SUPPORTS_CREDENTIALS", True),
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "X-Request-ID"],
    )
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(disasters_bp, url_prefix="/api/v1")
    app.register_blueprint(facilities_bp, url_prefix="/api/v1")
    app.register_blueprint(ai_bp, url_prefix="/api/v1/ai")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(operations_bp, url_prefix="/api/v1")
    app.register_blueprint(community_bp, url_prefix="/api/v1")

    @app.before_request
    def request_context_and_csrf():
        supplied = request.headers.get("X-Request-ID", "")
        g.request_id = supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else uuid4().hex
        csrf_error = enforce_csrf()
        if csrf_error is not None:
            return csrf_error
        if request.is_json:
            payload = request.get_json(silent=True)
            if payload is not None and not isinstance(payload, dict):
                return jsonify({"error": "JSON request body must be an object"}), 400
        return None

    @app.after_request
    def secure_response(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", uuid4().hex)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; "
            "object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if app.config.get("APP_ENV") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.get("/api/v1/health")
    @limiter.exempt
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "disaster-response-api",
                "version": app.config.get("RELEASE_VERSION"),
                "commit": app.config.get("RELEASE_COMMIT") or None,
            }
        )

    @app.get("/api/v1/ready")
    @limiter.exempt
    def ready():
        issues = production_configuration_issues(app.config)
        database_ready = True
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            database_ready = False
            db.session.rollback()
            app.logger.exception("Database readiness check failed")
        if issues:
            app.logger.error("Production configuration is not ready: %s", "; ".join(issues))
        ready_status = database_ready and not issues
        return (
            jsonify(
                {
                    "status": "ready" if ready_status else "not_ready",
                    "checks": {"database": database_ready, "configuration": not issues},
                    "request_id": g.request_id,
                }
            ),
            200 if ready_status else 503,
        )

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": str(error.description or "Bad request")}), 400

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": "Request payload is too large"}), 413

    @app.errorhandler(429)
    def rate_limited(_error):
        return jsonify({"error": "Too many requests. Try again later."}), 429

    @app.errorhandler(ValueError)
    @app.errorhandler(TypeError)
    def invalid_value(error):
        return jsonify({"error": f"Invalid request value: {error}"}), 400

    @app.errorhandler(Exception)
    def unexpected_error(error):
        db.session.rollback()
        app.logger.log(logging.ERROR, "Unhandled API error request_id=%s", g.request_id, exc_info=error)
        return jsonify({"error": "Internal server error", "request_id": g.request_id}), 500

    return app
