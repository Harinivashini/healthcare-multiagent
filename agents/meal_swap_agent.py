"""
agents/meal_swap_agent.py
──────────────────────────
Meal Swap Agent
───────────────
Regenerates a single meal slot (breakfast / lunch / dinner)
with a completely different option, respecting the same
dietary preferences and medical constraints.
"""

import json
import re
from data.db import get_user, get_cgm_history, get_mood_history
from agents.llm_client import chat
from agents.json_parser import parse_json

SWAP_SYSTEM_PROMPT = """You are a registered dietitian AI.
A patient wants to swap one meal in their plan for a completely different option.

Respond with ONLY this JSON object. No markdown, no explanation. Start with { end with }:
{
  "name": "New dish name",
  "description": "2 sentences describing the meal",
  "macros": {"carbs_g": 45, "protein_g": 30, "fat_g": 12, "calories_kcal": 410},
  "prep_tip": "One practical preparation tip"
}"""


def _parse_meal(raw: str) -> dict:
    try:
        return json.loads(raw.strip())
    except Exception:
        pass
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(cleaned)
    except Exception:
        pass
    try:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {"parse_error": True, "raw": raw}


class MealSwapAgent:
    name = "MealSwapAgent"

    def run(self, user_id: int, slot: str, current_meal_name: str) -> dict:
        """
        Args:
            user_id:           Validated user identifier.
            slot:              'breakfast', 'lunch', or 'dinner'
            current_meal_name: Name of the meal being swapped out

        Returns:
            { "slot": str, "meal": dict }
        """
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        cgm_history  = get_cgm_history(user_id, limit=1)
        latest_cgm   = cgm_history[0]["reading"] if cgm_history else None
        mood_history = get_mood_history(user_id, limit=1)
        latest_mood  = mood_history[0]["mood"] if mood_history else None

        cgm_note = ""
        if latest_cgm:
            if latest_cgm > user.get("cgm_high", 180):
                cgm_note = f"CGM is HIGH ({latest_cgm} mg/dL) — use low-glycaemic foods."
            elif latest_cgm < user.get("cgm_low", 80):
                cgm_note = f"CGM is LOW ({latest_cgm} mg/dL) — include complex carbs."

        prompt = (
            f"Generate a DIFFERENT {slot} option for this patient.\n"
            f"They want to swap out: '{current_meal_name}'\n"
            f"Make it completely different — different cuisine, different ingredients.\n\n"
            f"Patient profile:\n"
            f"- Dietary preference: {user['dietary_preference']}\n"
            f"- Medical conditions: {user['medical_conditions']}\n"
            f"- Physical limitations: {user['physical_limitations']}\n"
            f"- Mood: {latest_mood or 'unknown'}\n"
            f"- {cgm_note or 'CGM in normal range'}\n\n"
            f"Output ONLY the JSON object."
        )

        raw  = chat(SWAP_SYSTEM_PROMPT, prompt, temperature=0.8, max_tokens=400)
        meal = parse_json(raw)

        return {"slot": slot, "meal": meal}