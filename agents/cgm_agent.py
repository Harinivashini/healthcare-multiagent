"""
agents/cgm_agent.py
────────────────────
CGM Agent — validates glucose readings, flags alerts,
logs critical events to the database.
"""

from data.db import log_cgm, get_cgm_history, get_user, log_critical_alert, create_alerts_table

GLOBAL_LOW      = 80
GLOBAL_HIGH     = 300
CRITICAL_LOW    = 70    # Emergency threshold
CRITICAL_HIGH   = 250   # Emergency threshold


def _classify(reading: float, user: dict) -> dict:
    personal_low  = user.get("cgm_low", GLOBAL_LOW)
    personal_high = user.get("cgm_high", GLOBAL_HIGH)

    # CRITICAL states — trigger full-screen alert
    if reading < CRITICAL_LOW:
        return {
            "level":      "CRITICAL_LOW",
            "critical":   True,
            "flagged":    True,
            "color":      "red",
            "title":      "🚨 CRITICAL: Dangerously Low Glucose",
            "clinical":   (
                f"Your glucose is {reading} mg/dL — severely hypoglycaemic. "
                "This is a medical emergency. Brain function is at risk without immediate action."
            ),
            "actions": [
                "Eat 15–20g fast-acting carbs NOW (4 glucose tablets, half a cup of juice, or regular soda)",
                "Do NOT lie down — stay seated and stay calm",
                "Call a family member or caregiver immediately",
                "Recheck your glucose in exactly 15 minutes",
                "If no improvement, call emergency services (112 / 911)",
            ],
            "recheck_minutes": 15,
        }

    if reading > CRITICAL_HIGH:
        return {
            "level":    "CRITICAL_HIGH",
            "critical": True,
            "flagged":  True,
            "color":    "red",
            "title":    "🚨 CRITICAL: Dangerously High Glucose",
            "clinical": (
                f"Your glucose is {reading} mg/dL — severely hyperglycaemic. "
                "Prolonged high glucose can lead to diabetic ketoacidosis (DKA), a life-threatening condition."
            ),
            "actions": [
                "Drink a large glass of water immediately to help flush excess glucose",
                "Do NOT eat or drink anything sugary",
                "Check for symptoms: nausea, vomiting, fruity breath, confusion",
                "Contact your doctor or diabetes care team right now",
                "Recheck glucose in 15 minutes — if still above 250, go to emergency",
            ],
            "recheck_minutes": 15,
        }

    # WARNING states
    if reading < personal_low:
        return {
            "level": "LOW", "critical": False, "flagged": True, "color": "amber",
            "title": f"⚠️ Low: {reading} mg/dL",
            "clinical": f"Below your personal target ({personal_low} mg/dL). Have a small snack.",
            "actions": ["Have a small snack with 15g carbs", "Recheck in 15 minutes"],
            "recheck_minutes": 15,
        }

    if reading > personal_high:
        return {
            "level": "HIGH", "critical": False, "flagged": True, "color": "amber",
            "title": f"⚠️ High: {reading} mg/dL",
            "clinical": f"Above your personal target ({personal_high} mg/dL). Monitor closely.",
            "actions": ["Drink water", "Avoid carbs for the next hour", "Recheck in 30 minutes"],
            "recheck_minutes": 30,
        }

    # Normal
    return {
        "level": "NORMAL", "critical": False, "flagged": False, "color": "green",
        "title": f"✅ Normal: {reading} mg/dL",
        "clinical": f"Within your target range ({personal_low}–{personal_high} mg/dL). Keep it up!",
        "actions": [],
        "recheck_minutes": None,
    }


class CGMAgent:
    name = "CGMAgent"

    def run(self, user_id: int, reading: float) -> dict:
        try:
            reading = float(reading)
        except (TypeError, ValueError):
            return {"error": f"Invalid reading '{reading}'. Please enter a numeric value."}

        # Ensure alerts table exists
        create_alerts_table()

        user       = get_user(user_id) or {}
        entry      = log_cgm(user_id, reading)
        history    = get_cgm_history(user_id, limit=7)
        assessment = _classify(reading, user)

        # Log critical events to DB
        if assessment["critical"]:
            log_critical_alert(
                user_id  = user_id,
                reading  = reading,
                alert_type = assessment["level"],
                message  = assessment["clinical"],
            )

        return {
            "reading":         reading,
            "flagged":         assessment["flagged"],
            "critical":        assessment["critical"],
            "level":           assessment["level"],
            "color":           assessment["color"],
            "title":           assessment["title"],
            "clinical":        assessment["clinical"],
            "actions":         assessment["actions"],
            "recheck_minutes": assessment["recheck_minutes"],
            "alert_message":   assessment["title"],   # backward compat
            "history":         history,
        }