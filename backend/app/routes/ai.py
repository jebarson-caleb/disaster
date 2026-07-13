from flask import Blueprint, jsonify, request

from ..auth import login_required
from ..services.ai_service import damage_estimation, relief_prioritization, resource_allocation

ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/damage-estimation")
@login_required()
def estimate_damage():
    return jsonify(damage_estimation(request.get_json() or {}))


@ai_bp.post("/prioritize-rescue")
@login_required()
def prioritize_rescue():
    return jsonify(relief_prioritization(request.get_json() or {}))


@ai_bp.post("/allocate-resources")
@login_required()
def allocate_resources():
    return jsonify(resource_allocation(request.get_json() or {}))
