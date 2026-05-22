"""
agents/recipe_agent.py
───────────────────────
Returns recipe as structured plain text — no JSON parsing needed.
"""

from data.db import get_user
from agents.llm_client import chat

RECIPE_SYSTEM_PROMPT = """You are a professional chef. Write a recipe in this EXACT format with these EXACT headers.
Do not add any other text, intro, or explanation.

MEAL: {meal name here}
SERVINGS: {number}
PREP: {number} minutes
COOK: {number} minutes

INGREDIENTS:
- {amount} {unit} {ingredient name}
- {amount} {unit} {ingredient name}
- {amount} {unit} {ingredient name}

STEPS:
1. {instruction}
2. {instruction}
3. {instruction}

TIP: {one health tip sentence}"""


class RecipeAgent:
    name = "RecipeAgent"

    def run(self, user_id: int, meal_name: str) -> dict:
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        prompt = (
            f"Write a recipe for: {meal_name}\n"
            f"Diet: {user['dietary_preference']}\n"
            f"Medical conditions: {user['medical_conditions']}\n"
            f"Limitations: {user['physical_limitations']}\n\n"
            f"Follow the exact format. Start with MEAL:"
        )

        raw = chat(RECIPE_SYSTEM_PROMPT, prompt, temperature=0.3, max_tokens=800)

        # Parse the plain text into structured data
        return _parse_text_recipe(raw, meal_name)


def _parse_text_recipe(text: str, fallback_name: str) -> dict:
    """Parse the plain text recipe format into a structured dict."""
    import re

    lines = text.strip().split("\n")
    result = {
        "meal_name": fallback_name,
        "servings": None,
        "prep_time_minutes": None,
        "cook_time_minutes": None,
        "ingredients": [],
        "steps": [],
        "health_tip": None,
    }

    mode = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.upper().startswith("MEAL:"):
            result["meal_name"] = line.split(":", 1)[1].strip()
        elif line.upper().startswith("SERVINGS:"):
            val = re.findall(r"\d+", line)
            result["servings"] = int(val[0]) if val else 1
        elif line.upper().startswith("PREP:"):
            val = re.findall(r"\d+", line)
            result["prep_time_minutes"] = int(val[0]) if val else None
        elif line.upper().startswith("COOK:"):
            val = re.findall(r"\d+", line)
            result["cook_time_minutes"] = int(val[0]) if val else None
        elif line.upper().startswith("INGREDIENTS:"):
            mode = "ingredients"
        elif line.upper().startswith("STEPS:"):
            mode = "steps"
        elif line.upper().startswith("TIP:"):
            result["health_tip"] = line.split(":", 1)[1].strip()
            mode = None
        elif mode == "ingredients" and line.startswith("-"):
            ingredient_text = line[1:].strip()
            # Try to split: amount unit name
            parts = ingredient_text.split(" ", 2)
            if len(parts) >= 3:
                result["ingredients"].append({
                    "item": parts[2],
                    "amount": parts[0],
                    "unit": parts[1],
                })
            else:
                result["ingredients"].append({
                    "item": ingredient_text,
                    "amount": "",
                    "unit": "",
                })
        elif mode == "steps" and re.match(r"^\d+\.", line):
            step_text = re.sub(r"^\d+\.\s*", "", line)
            result["steps"].append(step_text)

    # If parsing got nothing useful, store raw text
    if not result["ingredients"] and not result["steps"]:
        result["raw"] = text
        result["parse_error"] = True

    return result