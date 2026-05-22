"""
agents/recipe_agent.py
"""

from data.db import get_user
from agents.llm_client import chat
from agents.json_parser import parse_json

RECIPE_SYSTEM_PROMPT = """You are a professional chef. Generate a recipe as JSON only.

Output ONLY this JSON structure, nothing else, no explanation:
{
  "meal_name": "name",
  "servings": 1,
  "prep_time_minutes": 10,
  "cook_time_minutes": 20,
  "ingredients": [
    {"item": "rolled oats", "amount": "0.5", "unit": "cup"},
    {"item": "milk", "amount": "1", "unit": "cup"}
  ],
  "steps": [
    "Boil water in a pot.",
    "Add oats and stir for 5 minutes.",
    "Serve hot."
  ],
  "health_tip": "This meal is good because..."
}

Use real values. Keep steps as simple strings."""


def _aggressive_parse(raw: str) -> dict:
    """Try every strategy to get valid JSON out of the LLM response."""

    # Strategy 1: direct parse
    try:
        return json.loads(raw.strip())
    except Exception:
        pass

    # Strategy 2: strip markdown fences
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(cleaned)
    except Exception:
        pass

    # Strategy 3: find outermost { }
    try:
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        pass

    # Strategy 4: fix common issues — trailing commas, single quotes
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        start   = cleaned.index("{")
        end     = cleaned.rindex("}") + 1
        chunk   = cleaned[start:end]
        # Remove trailing commas before } or ]
        chunk   = re.sub(r",\s*([}\]])", r"\1", chunk)
        return json.loads(chunk)
    except Exception:
        pass

    return {"parse_error": True, "raw": raw}


class RecipeAgent:
    name = "RecipeAgent"

    def run(self, user_id: int, meal_name: str) -> dict:
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        prompt = (
            f"Generate a recipe for: {meal_name}\n"
            f"Dietary preference: {user['dietary_preference']}\n"
            f"Medical conditions: {user['medical_conditions']}\n"
            f"Physical limitations: {user['physical_limitations']}\n\n"
            f"IMPORTANT: Output ONLY the JSON object. Start with {{ and end with }}. "
            f"No text before or after. No markdown."
        )

        raw    = chat(RECIPE_SYSTEM_PROMPT, prompt, temperature=0.3, max_tokens=800)
        recipe = parse_json(raw)
        return recipe