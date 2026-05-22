"""
agents/interrupt_agent.py
──────────────────────────
Interrupt Agent — General Q&A Assistant
─────────────────────────────────────────
• Intercepts any off-flow question the user asks at any point.
• Answers using the Groq LLM with a healthcare-aware system prompt.
• Returns the answer AND a graceful "return to flow" prompt so the
  orchestrator can resume the previous agent flow without losing context.
"""

from agents.llm_client import chat

INTERRUPT_SYSTEM_PROMPT = """You are a knowledgeable, friendly healthcare
assistant. The user may ask general health questions, medication queries,
symptom lookups, nutrition facts, or completely off-topic questions.

Guidelines:
1. Answer clearly and concisely (3–5 sentences max for factual questions).
2. Always recommend consulting a doctor for personal medical decisions.
3. End every response with a single line:
   "↩️  Ready to continue where we left off whenever you are."
4. Never make up medications, dosages, or clinical facts.
"""

FAQ_MAP = {
    "what is cgm": (
        "A Continuous Glucose Monitor (CGM) is a wearable sensor that "
        "measures blood glucose levels in real time, typically every 1–5 minutes, "
        "helping people with diabetes manage their condition more effectively."
    ),
    "what is a1c": (
        "HbA1c (glycated haemoglobin) is a blood test reflecting your average "
        "blood sugar level over the past 2–3 months. A result below 5.7% is normal; "
        "5.7–6.4% indicates prediabetes; 6.5%+ indicates diabetes."
    ),
    "what is hypertension": (
        "Hypertension (high blood pressure) is a condition where the force of blood "
        "against artery walls is consistently too high (≥130/80 mmHg), increasing the "
        "risk of heart disease and stroke."
    ),
}


def _faq_lookup(query: str) -> str | None:
    """Return a canned answer if the query matches a known FAQ key."""
    q_lower = query.lower().strip().rstrip("?")
    for key, answer in FAQ_MAP.items():
        if key in q_lower:
            return answer + "\n\n↩️  Ready to continue where we left off whenever you are."
    return None


class InterruptAgent:
    """
    Handles arbitrary user questions irrespective of the active flow.
    Always answers, then signals readiness to return to the previous context.
    """

    name = "InterruptAgent"

    def run(self, query: str, current_flow: str = "main menu") -> dict:
        """
        Args:
            query:        The user's free-form question.
            current_flow: Name of the agent/flow that was active before interruption.

        Returns:
            {
                "answer": str,
                "return_prompt": str,   # message to resume the previous flow
                "source": "faq" | "llm"
            }
        """
        if not query or not query.strip():
            return {"error": "Empty query — nothing to answer."}

        # Try FAQ first (faster, no API call)
        faq_answer = _faq_lookup(query)
        if faq_answer:
            return {
                "answer": faq_answer,
                "return_prompt": f"Returning you to: **{current_flow}**.",
                "source": "faq",
            }

        # Fall back to LLM
        answer = chat(INTERRUPT_SYSTEM_PROMPT, query, temperature=0.4, max_tokens=300)

        return {
            "answer": answer,
            "return_prompt": f"Returning you to: **{current_flow}**.",
            "source": "llm",
        }