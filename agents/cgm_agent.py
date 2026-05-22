"""
agents/cgm_agent.py
────────────────────
CGM (Continuous Glucose Monitor) Agent
───────────────────────────────────────
• Accepts a glucose reading (mg/dL).
• Validates against the global safe range (80–300) AND the user's
  personalised range stored in the dataset.
• Flags abnormal readings with appropriate clinical alerts.
• Stores the reading in cgm_logs.
"""

from data.db import log_cgm, get_cgm_history, get_user

GLOBAL_LOW = 80
GLOBAL_HIGH = 300


def _alert_message(reading: float, user: dict) -> str:
    personal_low = user.get("cgm_low", GLOBAL_LOW)
    personal_high = user.get("cgm_high", GLOBAL_HIGH)

    if reading < GLOBAL_LOW:
        return (
            f"🚨 CRITICAL LOW: {reading} mg/dL is dangerously low (< {GLOBAL_LOW}). "
            "Please consume fast-acting carbs immediately and contact your care team."
        )
    if reading > GLOBAL_HIGH:
        return (
            f"🚨 CRITICAL HIGH: {reading} mg/dL exceeds the maximum safe limit "
            f"({GLOBAL_HIGH} mg/dL). Seek medical attention."
        )
    if reading < personal_low:
        return (
            f"⚠️  LOW for you: {reading} mg/dL is below your personal target "
            f"({personal_low} mg/dL). Consider a small snack."
        )
    if reading > personal_high:
        return (
            f"⚠️  HIGH for you: {reading} mg/dL is above your personal target "
            f"({personal_high} mg/dL). Monitor closely and review recent meals."
        )
    return (
        f"✅  Reading looks good: {reading} mg/dL is within your target range "
        f"({personal_low}–{personal_high} mg/dL). Keep it up!"
    )


class CGMAgent:
    """Validates and logs continuous glucose monitor readings."""

    name = "CGMAgent"

    def run(self, user_id: int, reading: float) -> dict:
        """
        Args:
            user_id: Validated user identifier.
            reading: Blood glucose reading in mg/dL (float).

        Returns:
            {
                "reading": float,
                "flagged": bool,
                "alert_message": str,
                "history": list[dict]
            }
        """
        try:
            reading = float(reading)
        except (TypeError, ValueError):
            return {"error": f"Invalid reading '{reading}'. Please enter a numeric value."}

        user = get_user(user_id) or {}
        entry = log_cgm(user_id, reading)
        history = get_cgm_history(user_id, limit=7)

        alert = _alert_message(reading, user)

        return {
            "reading": reading,
            "flagged": entry["flagged"],
            "alert_message": alert,
            "history": history,
        }