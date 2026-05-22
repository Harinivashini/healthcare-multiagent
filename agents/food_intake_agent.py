"""
agents/food_intake_agent.py
────────────────────────────
Food Intake Agent
─────────────────
• Accepts a free-text meal description (+ optional timestamp).
• Uses an LLM prompt to estimate macronutrients (carbs / protein / fat).
• Persists the entry with estimated macros to food_logs.
• Returns a structured summary.
"""

import json
import re
from datetime import datetime

from data.db import log_food, get_food_history
from agents.llm_client import chat

MACRO_SYSTEM_PROMPT = """You are a clinical nutritionist AI.
Given a meal description, estimate the approximate macronutrients.
Respond ONLY with a valid JSON object — no markdown, no extra text:
{
  "carbs_g": <number>,
  "protein_g": <number>,
  "fat_g": <number>,
  "calories_kcal": <number>,
  "notes": "<brief 1-sentence note about this meal>"
}
Round each number to one decimal place."""


def _parse_macros(llm_response: str) -> dict:
    """Extract JSON from LLM response, with fallback defaults."""
    try:
        # Strip any accidental markdown fences
        cleaned = re.sub(r"```(?:json)?|```", "", llm_response).strip()
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {"carbs_g": None, "protein_g": None, "fat_g": None,
                "calories_kcal": None, "notes": "Could not estimate macros."}


class FoodIntakeAgent:
    """Records meals and estimates macronutrients via LLM."""

    name = "FoodIntakeAgent"

    def run(self, user_id: int, description: str,
            timestamp: str = None) -> dict:
        """
        Args:
            user_id:     Validated user identifier.
            description: Free-text meal description (e.g. "two boiled eggs and toast").
            timestamp:   Optional ISO datetime string; defaults to now.

        Returns:
            {
                "description": str,
                "timestamp": str,
                "macros": { carbs_g, protein_g, fat_g, calories_kcal, notes },
                "history": list[dict],
                "message": str
            }
        """
        if not description or not description.strip():
            return {"error": "Please describe what you ate."}

        timestamp = timestamp or datetime.utcnow().isoformat()

        # LLM macro estimation
        macro_data = _parse_macros(
            chat(MACRO_SYSTEM_PROMPT, f"Meal: {description}", temperature=0.3)
        )

        # Persist to DB
        log_food(
            user_id,
            description,
            carbs=macro_data.get("carbs_g"),
            protein=macro_data.get("protein_g"),
            fat=macro_data.get("fat_g"),
        )

        history = get_food_history(user_id, limit=5)

        message = (
            f"🍽️  Logged: **{description}**\n"
            f"  • Carbs: {macro_data.get('carbs_g', '?')} g\n"
            f"  • Protein: {macro_data.get('protein_g', '?')} g\n"
            f"  • Fat: {macro_data.get('fat_g', '?')} g\n"
            f"  • Calories: {macro_data.get('calories_kcal', '?')} kcal\n"
            f"  ℹ️  {macro_data.get('notes', '')}"
        )

        return {
            "description": description,
            "timestamp": timestamp,
            "macros": macro_data,
            "history": history,
            "message": message,
        }