"""
agents/mood_tracker_agent.py
─────────────────────────────
Mood Tracker Agent
──────────────────
• Accepts a mood label (happy / sad / excited / tired / anxious / calm / angry / neutral).
• Persists the entry to the mood_logs table.
• Computes a rolling 7-session average score (1–5 scale).
• Returns a short motivational/empathetic response.
"""

import statistics
from data.db import log_mood, get_mood_history
from agents.llm_client import chat

VALID_MOODS = {
    "happy", "excited", "content", "calm",
    "neutral", "tired", "anxious", "sad", "angry",
}

SYSTEM_PROMPT = (
    "You are a compassionate healthcare assistant who responds briefly "
    "(2-3 sentences) to a patient's reported mood. "
    "Be warm, supportive, and always end with an encouraging note."
)


class MoodTrackerAgent:
    """Logs and tracks user mood per session."""

    name = "MoodTrackerAgent"

    def run(self, user_id: int, mood: str) -> dict:
        """
        Args:
            user_id: Validated user identifier.
            mood:    Mood label string from the user.

        Returns:
            {
                "mood": str,
                "score": int,
                "rolling_average": float,
                "history": list[dict],
                "message": str
            }
        """
        mood = mood.lower().strip()
        if mood not in VALID_MOODS:
            closest = self._closest_mood(mood)
            return {
                "error": (
                    f"'{mood}' isn't a recognised mood. "
                    f"Did you mean '{closest}'? "
                    f"Valid options: {', '.join(sorted(VALID_MOODS))}."
                )
            }

        # Persist
        entry = log_mood(user_id, mood)

        # Rolling average (last 7 sessions)
        history = get_mood_history(user_id, limit=7)
        scores = [h["score"] for h in history]
        rolling_avg = round(statistics.mean(scores), 2) if scores else entry["score"]

        # LLM empathetic response
        user_msg = f"The patient just told me they are feeling: {mood}."
        message = chat(SYSTEM_PROMPT, user_msg, max_tokens=120)

        return {
            "mood": mood,
            "score": entry["score"],
            "rolling_average": rolling_avg,
            "history": history,
            "message": message,
        }

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _closest_mood(raw: str) -> str:
        """Simple character-overlap heuristic to suggest the nearest mood."""
        raw_set = set(raw)
        best, best_score = "neutral", 0
        for m in VALID_MOODS:
            score = len(raw_set & set(m))
            if score > best_score:
                best, best_score = m, score
        return best