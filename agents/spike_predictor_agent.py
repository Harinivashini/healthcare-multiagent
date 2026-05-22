"""
agents/spike_predictor_agent.py
────────────────────────────────
Glucose Spike Predictor Agent
"""

import json
import re
from data.db import get_user, get_cgm_history
from agents.llm_client import chat
from agents.json_parser import parse_json

SPIKE_SYSTEM_PROMPT = """You are a clinical nutrition AI. Analyze the meal and predict glucose spike risk.

Respond with ONLY this JSON. No text before or after. No markdown. Start with { end with }:
{"spike_risk":"HIGH","risk_score":8,"reason":"brief reason here","peak_estimate_mg_dl":45,"time_to_peak_minutes":45,"actions":["action 1","action 2","action 3"],"foods_of_concern":["food1","food2"],"safer_swap":"swap suggestion here"}"""


def _build_prompt(meal: str, user: dict, latest_cgm) -> str:
    return (
        f"Meal: {meal}\n"
        f"Patient conditions: {user['medical_conditions']}\n"
        f"Diet: {user['dietary_preference']}\n"
        f"Current CGM: {latest_cgm or 'unknown'} mg/dL\n"
        f"Personal CGM range: {user.get('cgm_low',80)}-{user.get('cgm_high',180)} mg/dL\n\n"
        f"Output ONLY the JSON object. Nothing else."
    )


def _parse_prediction(raw: str) -> dict:
    # Strategy 1: direct
    try:
        return json.loads(raw.strip())
    except Exception:
        pass
    # Strategy 2: strip fences
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(cleaned)
    except Exception:
        pass
    # Strategy 3: extract {...}
    try:
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    # Strategy 4: extract largest {...} block
    try:
        matches = re.findall(r'\{.*?\}', raw, re.DOTALL)
        if matches:
            longest = max(matches, key=len)
            return json.loads(longest)
    except Exception:
        pass
    return {"parse_error": True, "raw": raw}


class SpikePredictorAgent:
    name = "SpikePredictorAgent"

    def run(self, user_id: int, meal_description: str) -> dict:
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        cgm_history = get_cgm_history(user_id, limit=1)
        latest_cgm  = cgm_history[0]["reading"] if cgm_history else None

        prompt = _build_prompt(meal_description, user, latest_cgm)
        raw    = chat(SPIKE_SYSTEM_PROMPT, prompt, temperature=0.1, max_tokens=400)
        result = parse_json(raw)

        result["meal"]       = meal_description
        result["latest_cgm"] = latest_cgm
        return result