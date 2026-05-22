"""
agents/orchestrator.py
───────────────────────
Intent routing table
─────────────────────
  greet       → GreetingAgent
  mood        → MoodTrackerAgent
  cgm         → CGMAgent
  food        → FoodIntakeAgent
  meal_plan   → MealPlannerAgent
  meal_swap   → MealSwapAgent
  recipe      → RecipeAgent
  spike       → SpikePredictorAgent
  interrupt   → InterruptAgent
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any
from agents.greeting_agent        import GreetingAgent
from agents.mood_tracker_agent    import MoodTrackerAgent
from agents.cgm_agent             import CGMAgent
from agents.food_intake_agent     import FoodIntakeAgent
from agents.meal_planner_agent    import MealPlannerAgent
from agents.meal_swap_agent       import MealSwapAgent
from agents.recipe_agent          import RecipeAgent
from agents.spike_predictor_agent import SpikePredictorAgent
from agents.interrupt_agent       import InterruptAgent

_greeting  = GreetingAgent()
_mood      = MoodTrackerAgent()
_cgm       = CGMAgent()
_food      = FoodIntakeAgent()
_planner   = MealPlannerAgent()
_swap      = MealSwapAgent()
_recipe    = RecipeAgent()
_spike     = SpikePredictorAgent()
_interrupt = InterruptAgent()

INTENT_MAP = {
    "greet":     lambda p: _greeting.run(p["user_id"]),
    "mood":      lambda p: _mood.run(p["user_id"], p["mood"]),
    "cgm":       lambda p: _cgm.run(p["user_id"], float(p["reading"])),
    "food":      lambda p: _food.run(p["user_id"], p["description"], p.get("timestamp")),
    "meal_plan": lambda p: _planner.run(p["user_id"]),
    "meal_swap": lambda p: _swap.run(p["user_id"], p["slot"], p["current_meal_name"]),
    "recipe":    lambda p: _recipe.run(p["user_id"], p["meal_name"]),
    "spike":     lambda p: _spike.run(p["user_id"], p["meal_description"]),
    "interrupt": lambda p: _interrupt.run(p["query"], p.get("current_flow", "main menu")),
}

def run_agent(intent: str, payload: dict) -> Any:
    handler = INTENT_MAP.get(intent)
    if handler is None:
        raise ValueError(f"Unknown intent '{intent}'. Valid: {list(INTENT_MAP.keys())}")
    return handler(payload)