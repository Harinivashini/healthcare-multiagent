"""
agents/meal_planner_agent.py
"""

import json
import re

from data.db import (
    get_user, get_mood_history, get_cgm_history,
    save_meal_plan, get_latest_meal_plan,
)
from agents.llm_client import chat

MEAL_PLAN_SYSTEM_PROMPT = """You are a registered dietitian AI.
Generate a 1-day meal plan as ONLY a JSON object. No explanation, no markdown, no code blocks.
Start your response directly with { and end with }.

Use exactly this structure:
{
  "goal": "one sentence health goal",
  "meals": {
    "breakfast": {
      "name": "dish name",
      "description": "2 sentences about the meal",
      "macros": {"carbs_g": 45, "protein_g": 20, "fat_g": 10, "calories_kcal": 350},
      "prep_tip": "one short tip"
    },
    "lunch": {
      "name": "dish name",
      "description": "2 sentences about the meal",
      "macros": {"carbs_g": 60, "protein_g": 35, "fat_g": 15, "calories_kcal": 520},
      "prep_tip": "one short tip"
    },
    "dinner": {
      "name": "dish name",
      "description": "2 sentences about the meal",
      "macros": {"carbs_g": 50, "protein_g": 40, "fat_g": 18, "calories_kcal": 510},
      "prep_tip": "one short tip"
    }
  },
  "clinical_notes": "brief notes about this plan"
}

Replace the example numbers with real values appropriate for the patient."""


def _build_context(user: dict, latest_cgm, latest_mood) -> str:
    cgm_note = ""
    if latest_cgm is not None:
        if latest_cgm > user.get("cgm_high", 180):
            cgm_note = f"IMPORTANT: CGM is HIGH ({latest_cgm} mg/dL) - use low-glycaemic foods."
        elif latest_cgm < user.get("cgm_low", 80):
            cgm_note = f"IMPORTANT: CGM is LOW ({latest_cgm} mg/dL) - include complex carbs."
        else:
            cgm_note = f"CGM is in range ({latest_cgm} mg/dL)."

    return (
        f"Patient: {user['first_name']} {user['last_name']}\n"
        f"Dietary preference: {user['dietary_preference']}\n"
        f"Medical conditions: {user['medical_conditions']}\n"
        f"Physical limitations: {user['physical_limitations']}\n"
        f"Current mood: {latest_mood or 'unknown'}\n"
        f"{cgm_note}\n\n"
        f"Generate the JSON meal plan now. Output ONLY the JSON object, nothing else."
    )


def _parse_plan(llm_response: str) -> dict:
    """Try multiple strategies to extract valid JSON."""
    # Strategy 1: direct parse
    try:
        return json.loads(llm_response.strip())
    except Exception:
        pass

    # Strategy 2: strip markdown fences
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", llm_response).strip()
        return json.loads(cleaned)
    except Exception:
        pass

    # Strategy 3: extract first { ... } block
    try:
        match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    # Fallback: return raw text
    return {"raw": llm_response, "parse_error": True}


def _format_message(plan: dict, first_name: str) -> str:
    """Build a readable summary from the plan dict."""
    if plan.get("parse_error"):
        return plan.get("raw", "Meal plan generated.")

    meals = plan.get("meals", {})
    lines = [f"🥗 Meal Plan for {first_name}", f"Goal: {plan.get('goal', '')}", ""]

    for slot, data in meals.items():
        macros = data.get("macros", {})
        lines.append(
            f"{slot.capitalize()}: {data.get('name', '')}\n"
            f"{data.get('description', '')}\n"
            f"{macros.get('calories_kcal', '?')} kcal | "
            f"Carbs {macros.get('carbs_g', '?')}g | "
            f"Protein {macros.get('protein_g', '?')}g | "
            f"Fat {macros.get('fat_g', '?')}g\n"
            f"Tip: {data.get('prep_tip', '')}"
        )

    if plan.get("clinical_notes"):
        lines.append(f"\nNotes: {plan['clinical_notes']}")

    return "\n".join(lines)


class MealPlannerAgent:
    name = "MealPlannerAgent"

    def run(self, user_id: int) -> dict:
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        cgm_history  = get_cgm_history(user_id, limit=1)
        latest_cgm   = cgm_history[0]["reading"] if cgm_history else None
        mood_history = get_mood_history(user_id, limit=1)
        latest_mood  = mood_history[0]["mood"] if mood_history else None

        context = _build_context(user, latest_cgm, latest_mood)
        raw     = chat(MEAL_PLAN_SYSTEM_PROMPT, context, temperature=0.3, max_tokens=1200)
        plan    = _parse_plan(raw)

        save_meal_plan(user_id, json.dumps(plan))

        return {
            "plan":    plan,
            "message": _format_message(plan, user["first_name"]),
        }