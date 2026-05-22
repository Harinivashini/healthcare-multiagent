"""
agents/greeting_agent.py
─────────────────────────
Greeting Agent
──────────────
• Validates user_id against the SQLite dataset.
• If valid → retrieves first_name, last_name, city → returns a warm greeting.
• If invalid → returns an error asking the user to re-enter a valid ID.
"""

from data.db import get_user


class GreetingAgent:
    """Validates a user ID and generates a personalised greeting."""

    name = "GreetingAgent"

    def run(self, user_id: int) -> dict:
        """
        Args:
            user_id: Integer supplied by the user at login.

        Returns:
            {
                "valid": bool,
                "user": dict | None,   # full user row if valid
                "message": str         # greeting or error text
            }
        """
        user = get_user(user_id)

        if user is None:
            return {
                "valid": False,
                "user": None,
                "message": (
                    f"⚠️  User ID {user_id} was not found in our system. "
                    "Please double-check and enter a valid ID (1–100)."
                ),
            }

        message = (
            f"👋 Hello, {user['first_name']} {user['last_name']}! "
            f"Welcome back from {user['city']}. "
            "How can I assist you with your health today?"
        )

        return {
            "valid": True,
            "user": user,
            "message": message,
        }