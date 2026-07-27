import math
from datetime import UTC, datetime

import requests
from flask import current_app

SEVERITY_WEIGHTS = {
    "low": 10,
    "medium": 25,
    "high": 45,
    "critical": 65,
}

DISASTER_WEIGHTS = {
    "flood": 22,
    "earthquake": 30,
    "cyclone": 26,
    "landslide": 24,
    "fire": 28,
}


def label_from_score(score):
    if score >= 85:
        return "Critical"
    if score >= 65:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def damage_estimation(payload):
    disaster_type = str(payload.get("disaster_type", "")).lower()
    severity_hint = str(payload.get("severity_hint", "medium")).lower()
    people_affected = int(payload.get("people_affected") or 0)
    image_url = payload.get("image_url")
    location_risk = int(payload.get("location_risk", 20))

    score = 15
    score += DISASTER_WEIGHTS.get(disaster_type, 18)
    score += SEVERITY_WEIGHTS.get(severity_hint, 25)
    score += min(25, people_affected // 20)
    score += min(15, max(0, location_risk))
    if image_url:
        score += 5

    score = max(0, min(100, score))
    label = label_from_score(score)
    explanation = (
        f"{label} damage predicted from {disaster_type or 'reported'} event, "
        f"{people_affected} people affected, and {severity_hint} severity signal."
    )
    explanation = ollama_explanation("damage estimation", payload, explanation)
    return {"score": score, "label": label, "explanation": explanation}


def relief_prioritization(payload):
    condition = str(payload.get("condition", "stable")).lower()
    trapped = bool(payload.get("trapped"))
    vulnerable_people = int(payload.get("vulnerable_people") or 0)
    people_count = int(payload.get("people_count") or 1)
    victim_age = int(payload.get("victim_age") or 0)
    disaster_type = str(payload.get("disaster_type", "")).lower()
    created_at = payload.get("created_at")

    score = 20
    if condition in {"critical", "unconscious", "bleeding", "serious"}:
        score += 35
    elif condition in {"injured", "sick"}:
        score += 20
    if trapped:
        score += 25
    if disaster_type in {"flood", "fire", "earthquake", "landslide"}:
        score += 10
    score += min(15, vulnerable_people * 5)
    score += min(10, max(0, people_count - 1) * 2)
    if victim_age and (victim_age < 12 or victim_age > 65):
        score += 10
    score += waiting_bonus(created_at)

    score = max(0, min(100, score))
    label = label_from_score(score)
    explanation = (
        f"{label} priority based on condition={condition}, trapped={trapped}, "
        f"vulnerable_people={vulnerable_people}, and group size={people_count}."
    )
    explanation = ollama_explanation("relief prioritization", payload, explanation)
    return {"score": score, "label": label, "explanation": explanation}


def resource_allocation(payload):
    severity = str(payload.get("severity", payload.get("priority_label", "Medium"))).lower()
    people_count = int(payload.get("people_count") or payload.get("people_affected") or 1)
    disaster_type = str(payload.get("disaster_type", "")).lower()
    available = payload.get("available_resources") or {}

    base = {
        "ambulances": 1 if severity in {"high", "critical"} else 0,
        "rescue_teams": 2 if severity == "critical" else 1,
        "volunteers": max(2, math.ceil(people_count / 20)),
        "food_packets": max(25, people_count * 3),
        "medicine_kits": max(5, math.ceil(people_count / 8)),
        "shelter_slots": max(0, people_count if disaster_type in {"flood", "cyclone", "fire"} else people_count // 2),
    }
    if severity == "critical":
        base["ambulances"] += 1
        base["rescue_teams"] += 1
    capped = {name: min(quantity, int(available.get(name, quantity))) for name, quantity in base.items()}
    explanation = f"Allocation favors {severity} severity, {people_count} affected people, and {disaster_type or 'general'} response needs."
    explanation = ollama_explanation("resource allocation", payload, explanation)
    return {"recommendations": capped, "explanation": explanation}


def waiting_bonus(created_at):
    if not created_at:
        return 0
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            return 0
    minutes = (datetime.now(UTC) - created_at).total_seconds() / 60
    return min(10, int(minutes // 30))


def ollama_explanation(task, payload, fallback):
    base_url = current_app.config.get("OLLAMA_BASE_URL")
    model = current_app.config.get("OLLAMA_MODEL")
    if not base_url or not model:
        return fallback
    prompt = (
        f"Give a concise disaster management explanation for {task}. "
        f"Use this input: {payload}. Keep it under 45 words."
    )
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=3,
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        return text or fallback
    except requests.RequestException:
        return fallback
