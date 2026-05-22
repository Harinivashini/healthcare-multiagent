"""
agents/orchestrator.py
───────────────────────
Multi-Agent Orchestrator
─────────────────────────
Clean intent-based dispatcher — no fragile agno decorators.
Agno Agent is built separately for conversational flows.

Intent routing table
─────────────────────
  "greet"       → GreetingAgent
  "mood"        → MoodTrackerAgent
  "cgm"         → CGMAgent
  "food"        → FoodIntakeAgent
  "meal_plan"   → MealPlannerAgent
  "interrupt"   → InterruptAgent
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Any

from agents.greeting_agent import GreetingAgent
from agents.mood_tracker_agent import MoodTrackerAgent
from agents.cgm_agent import CGMAgent
from agents.food_intake_agent import FoodIntakeAgent
from agents.meal_planner_agent import MealPlannerAgent
from agents.interrupt_agent import InterruptAgent

# ── Instantiate all domain agents once at import time ─────────────────────────

_greeting  = GreetingAgent()
_mood      = MoodTrackerAgent()
_cgm       = CGMAgent()
_food      = FoodIntakeAgent()
_planner   = MealPlannerAgent()
_interrupt = InterruptAgent()

# ── Intent dispatch map ───────────────────────────────────────────────────────

INTENT_MAP = {
    "greet":     lambda p: _greeting.run(p["user_id"]),
    "mood":      lambda p: _mood.run(p["user_id"], p["mood"]),
    "cgm":       lambda p: _cgm.run(p["user_id"], float(p["reading"])),
    "food":      lambda p: _food.run(p["user_id"], p["description"], p.get("timestamp")),
    "meal_plan": lambda p: _planner.run(p["user_id"]),
    "interrupt": lambda p: _interrupt.run(p["query"], p.get("current_flow", "main menu")),
}


def run_agent(intent: str, payload: dict) -> Any:
    """
    Dispatch a structured intent to the appropriate agent.

    Args:
        intent:  One of greet / mood / cgm / food / meal_plan / interrupt.
        payload: Dict containing the required fields for that agent.

    Returns:
        The agent's result dict.

    Raises:
        ValueError: If the intent is not recognised.
    """
    handler = INTENT_MAP.get(intent)
    if handler is None:
        raise ValueError(
            f"Unknown intent '{intent}'. "
            f"Valid intents: {list(INTENT_MAP.keys())}"
        )
    return handler(payload)