"""
agents/meal_planner_agent.py
─────────────────────────────
Meal Planner Agent
──────────────────
• Takes dietary preference, medical conditions, latest mood, and
  latest CGM reading as inputs.
• If CGM is out of range → prioritises glucose-stabilising meals.
• Calls Groq LLM to generate a full 3-meal plan (breakfast / lunch /
  dinner) with macros and preparation tips.
• Persists the plan as JSON in meal_plans table.
• Returns the structured plan + a human-readable summary.
"""

import json
import re

from data.db import (
    get_user, get_mood_history, get_cgm_history,
    save_meal_plan, get_latest_meal_plan,
)
from agents.llm_client import chat

MEAL_PLAN_SYSTEM_PROMPT = """You are a registered dietitian AI specialising in
personalised nutrition for patients with chronic conditions.

Generate a 1-day meal plan (3 meals) as a JSON object.
The JSON must follow this exact schema — no markdown, no extra text:

{
  "date": "<today>",
  "dietary_preference": "<preference>",
  "goal": "<one-sentence health goal for today>",
  "meals": {
    "breakfast": {
      "name": "<dish name>",
      "description": "<2-3 sentences>",
      "macros": { "carbs_g": <n>, "protein_g": <n>, "fat_g": <n>, "calories_kcal": <n> },
      "prep_tip": "<short tip>"
    },
    "lunch": { ... same structure ... },
    "dinner": { ... same structure ... }
  },
  "daily_totals": { "carbs_g": <n>, "protein_g": <n>, "fat_g": <n>, "calories_kcal": <n> },
  "clinical_notes": "<important notes about this plan given the patient's conditions>"
}"""


def _build_context(user: dict, latest_cgm: float | None,
                   latest_mood: str | None) -> str:
    """Construct the user prompt for the meal planner."""
    cgm_note = ""
    if latest_cgm is not None:
        if latest_cgm > user.get("cgm_high", 180):
            cgm_note = (
                f"⚠️  Latest CGM reading is HIGH ({latest_cgm} mg/dL). "
                "Prioritise low-glycaemic foods to bring glucose under control."
            )
        elif latest_cgm < user.get("cgm_low", 80):
            cgm_note = (
                f"⚠️  Latest CGM reading is LOW ({latest_cgm} mg/dL). "
                "Include complex carbs to safely raise blood sugar."
            )
        else:
            cgm_note = f"CGM reading is within range ({latest_cgm} mg/dL)."

    return f"""
Patient Profile:
- Name: {user['first_name']} {user['last_name']}
- Dietary Preference: {user['dietary_preference']}
- Medical Conditions: {user['medical_conditions']}
- Physical Limitations: {user['physical_limitations']}
- Current Mood: {latest_mood or 'unknown'}
- {cgm_note}

Generate a personalised 1-day meal plan respecting ALL dietary restrictions
and medical conditions listed above.
""".strip()


def _parse_plan(llm_response: str) -> dict:
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", llm_response).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {"raw": llm_response, "parse_error": True}


class MealPlannerAgent:
    """Generates an adaptive, personalised daily meal plan."""

    name = "MealPlannerAgent"

    def run(self, user_id: int) -> dict:
        """
        Args:
            user_id: Validated user identifier.

        Returns:
            {
                "plan": dict,          # structured meal plan
                "message": str         # human-readable summary
            }
        """
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        # Pull latest context
        cgm_history = get_cgm_history(user_id, limit=1)
        latest_cgm = cgm_history[0]["reading"] if cgm_history else None

        mood_history = get_mood_history(user_id, limit=1)
        latest_mood = mood_history[0]["mood"] if mood_history else None

        context = _build_context(user, latest_cgm, latest_mood)
        raw = chat(MEAL_PLAN_SYSTEM_PROMPT, context, temperature=0.5, max_tokens=1200)
        plan = _parse_plan(raw)

        # Persist
        save_meal_plan(user_id, json.dumps(plan))

        # Human-readable summary
        if plan.get("parse_error"):
            message = f"Meal plan generated (raw):\n{plan.get('raw', '')}"
        else:
            meals = plan.get("meals", {})
            lines = [
                f"🥗 **Meal Plan for {user['first_name']}**",
                f"*Goal:* {plan.get('goal', '')}",
                "",
            ]
            for slot, data in meals.items():
                lines.append(
                    f"**{slot.capitalize()}** — {data.get('name', '')}\n"
                    f"{data.get('description', '')}\n"
                    f"Macros: {data['macros'].get('calories_kcal')} kcal | "
                    f"Carbs {data['macros'].get('carbs_g')}g | "
                    f"Protein {data['macros'].get('protein_g')}g | "
                    f"Fat {data['macros'].get('fat_g')}g\n"
                    f"💡 {data.get('prep_tip', '')}"
                )
            lines.append(f"\n📋 *Clinical notes:* {plan.get('clinical_notes', '')}")
            message = "\n".join(lines)

        return {"plan": plan, "message": message}