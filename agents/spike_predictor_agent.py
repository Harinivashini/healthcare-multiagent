"""
agents/spike_predictor_agent.py
"""

from data.db import get_user, get_cgm_history
from agents.llm_client import chat
from agents.json_parser import parse_json

SPIKE_SYSTEM_PROMPT = """You are a clinical dietitian AI specialising in diabetes management.
Your ONLY job is to analyse a meal and return a JSON object — no preamble, no explanation, no markdown.

CLINICAL REASONING STEPS (think silently, output only JSON):

1. IDENTIFY the primary carb source in the meal and classify base risk:
   - HIGH (score 7-10): white rice, biryani, biriyani, briyani, bread, pasta, naan, maida, roti made of maida, sweets, sugary drinks, fried food, potato, pure carb meal >60g
   - MEDIUM (score 4-6): millets (ragi/jowar/bajra/foxtail), whole wheat chapati, oats, idli, dosa, dal, lentils, banana, mango, mixed carb meal 30-60g
   - LOW (score 1-3): salad, grilled/boiled protein, non-starchy vegetables, eggs, paneer, tofu, nuts, pure protein meal <30g carbs

2. CHECK if meal has significant protein or fat (chicken, fish, egg, paneer, dal, curd, nuts, ghee, mutton, prawn):
   - YES → reduce score by 1-2, reduce peak by 30%, slow time_to_peak to 60-75 min
   - This applies even for diabetic patients — protein always blunts the glucose curve

3. APPLY condition escalation ONLY after protein check:
   - Type 2 Diabetes or Hypertension + low/no protein → escalate one level (LOW→MEDIUM, MEDIUM→HIGH)
   - Millets + protein + diabetes → stay MEDIUM, max score 6, never HIGH
   - CGM already >150 mg/dL → add +1 to score only

4. SET peak_estimate_mg_dl based on final risk:
   - HIGH: 60-100 mg/dL | MEDIUM: 25-50 mg/dL | LOW: 10-25 mg/dL

OUTPUT RULES — strictly follow:
- Return ONLY a single-line JSON object, nothing else
- No markdown, no code fences, no backticks, no explanation before or after
- All string values must use double quotes
- actions must be an array of exactly 3 specific, actionable strings tailored to this meal
- foods_of_concern must list only the actual risky foods from the meal (empty array [] if none)
- safer_swap must be a specific food swap (empty string "" if meal is already safe)

EXACT OUTPUT FORMAT (replace values, keep all keys):
{"spike_risk":"HIGH","risk_score":8,"reason":"brief clinical reason","peak_estimate_mg_dl":80,"time_to_peak_minutes":45,"actions":["action 1","action 2","action 3"],"foods_of_concern":["food1"],"safer_swap":"swap suggestion"}"""


# ---------------------------------------------------------------------------
# Protein / fat keywords that dampen glucose response
# ---------------------------------------------------------------------------
_PROTEIN_DAMPENERS = [
    "chicken", "fish", "egg", "paneer", "tofu", "dal", "lentil", "curd",
    "yogurt", "yoghurt", "dahi", "nuts", "almond", "walnut", "ghee",
    "mutton", "prawn", "shrimp", "tuna", "salmon", "beef", "pork",
    "cottage cheese", "soya", "soy", "tempeh", "kidney bean", "chickpea",
    "chana", "rajma", "moong",
]

# Millets that are diabetic-friendly — should never be AUTO-escalated to HIGH
# when protein is present
_DIABETIC_FRIENDLY_GRAINS = [
    "millet", "ragi", "jowar", "bajra", "foxtail", "barnyard", "kodo",
    "little millet", "proso",
]


def _has_protein(meal: str) -> bool:
    """Return True if the meal contains a significant protein/fat source."""
    meal_lower = meal.lower()
    return any(p in meal_lower for p in _PROTEIN_DAMPENERS)


def _has_diabetic_friendly_grain(meal: str) -> bool:
    """Return True if the meal is based on a diabetic-friendly grain."""
    meal_lower = meal.lower()
    return any(g in meal_lower for g in _DIABETIC_FRIENDLY_GRAINS)


def _rule_based_risk(meal: str, conditions: str, latest_cgm) -> dict:
    """
    Improved rule-based fallback. Returns a dict with:
      risk, score, peak_estimate, time_to_peak
    instead of just a risk string — so the fallback block can use richer data.
    """
    meal_lower = meal.lower()

    high_gi    = ["biryani", "white rice", "bread", "pasta", "naan", "maida",
                  "sugar", "sweet", "cake", "juice", "soda", "potato", "fried"]
    medium_gi  = ["millet", "ragi", "jowar", "bajra", "chapati", "oats",
                  "banana", "mango", "dal", "lentil", "idli", "dosa", "foxtail"]

    has_diabetes        = "diabetes" in conditions.lower()
    has_hypertension    = "hypertension" in conditions.lower()
    high_cgm            = latest_cgm and latest_cgm > 150
    protein_present     = _has_protein(meal)
    friendly_grain      = _has_diabetic_friendly_grain(meal)

    # ── Base classification ──────────────────────────────────────────────────
    if any(f in meal_lower for f in high_gi):
        base, score, peak = "HIGH", 8, 80
    elif any(f in meal_lower for f in medium_gi):
        base, score, peak = "MEDIUM", 5, 40
    else:
        base, score, peak = "LOW", 2, 15

    # ── Protein / fat dampener ───────────────────────────────────────────────
    if protein_present and base in ("MEDIUM", "HIGH"):
        score = max(score - 2, 1)
        peak  = max(int(peak * 0.65), 10)
        if base == "HIGH" and score <= 6:
            base = "MEDIUM"

    # ── Condition escalation (capped for diabetic-friendly grains + protein) ─
    needs_escalation = (has_diabetes or has_hypertension or high_cgm)
    if needs_escalation:
        if friendly_grain and protein_present:
            # Soft escalation: bump score by 1, keep MEDIUM label
            score = min(score + 1, 6)
            peak  = min(int(peak * 1.15), 50)
        else:
            # Standard escalation
            if base == "LOW":
                base, score, peak = "MEDIUM", max(score + 2, 4), 35
            elif base == "MEDIUM":
                base, score, peak = "HIGH",   max(score + 2, 7), 65

    # ── CGM already elevated: +1 score, no label change ─────────────────────
    if high_cgm and not needs_escalation:
        score = min(score + 1, 10)

    # ── Clamp score to label range ───────────────────────────────────────────
    clamp = {"HIGH": (7, 10), "MEDIUM": (4, 6), "LOW": (1, 3)}
    lo, hi = clamp[base]
    score  = max(lo, min(hi, score))

    return {
        "risk":           base,
        "score":          score,
        "peak_estimate":  peak,
        "time_to_peak":   45,
    }


class SpikePredictorAgent:
    name = "SpikePredictorAgent"

    def run(self, user_id: int, meal_description: str) -> dict:
        user = get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found."}

        cgm_history = get_cgm_history(user_id, limit=1)
        latest_cgm  = cgm_history[0]["reading"] if cgm_history else None
        conditions  = user.get("medical_conditions", "")

        prompt = (
            f"Meal: {meal_description}\n"
            f"Medical conditions: {conditions or 'None'}\n"
            f"Dietary preference: {user['dietary_preference']}\n"
            f"Current CGM: {latest_cgm or 'unknown'} mg/dL\n"
            f"Target range: {user.get('cgm_low', 80)}-{user.get('cgm_high', 180)} mg/dL\n\n"
            f"Analyse this meal using all 4 clinical steps. "
            f"Your entire response must be exactly one JSON object — no other text."
        )

        raw    = chat(SPIKE_SYSTEM_PROMPT, prompt, temperature=0.0, max_tokens=600)
        result = parse_json(raw)

        if result.get("parse_error"):
            # ── Rule-based fallback ──────────────────────────────────────────
            rb = _rule_based_risk(meal_description, conditions, latest_cgm)
            result = {
                "spike_risk":          rb["risk"],
                "risk_score":          rb["score"],
                "reason": (
                    f"Based on meal composition and patient profile ({conditions}). "
                    + ("Protein content dampens glucose response." if _has_protein(meal_description) else "")
                ),
                "peak_estimate_mg_dl": rb["peak_estimate"],
                "time_to_peak_minutes": rb["time_to_peak"],
                "actions": [
                    "Take a 10-15 minute walk after eating",
                    "Drink a glass of water before the meal",
                    "Monitor your CGM 45 minutes after eating",
                ],
                "foods_of_concern": [],
                "safer_swap": "",
            }
        else:
            # ── Post-process LLM result ──────────────────────────────────────
            risk = result.get("spike_risk", "").upper()
            if risk not in ["LOW", "MEDIUM", "HIGH"]:
                rb   = _rule_based_risk(meal_description, conditions, latest_cgm)
                risk = rb["risk"]
                result["spike_risk"] = risk

            score = result.get("risk_score", 0)
            peak  = result.get("peak_estimate_mg_dl", 0)

            # ── Guard: LLM over-escalated a protein-rich millet meal ─────────
            protein_present  = _has_protein(meal_description)
            friendly_grain   = _has_diabetic_friendly_grain(meal_description)
            high_cgm_now     = latest_cgm and latest_cgm > 150

            if risk == "HIGH" and friendly_grain and protein_present and not high_cgm_now:
                # Downgrade to MEDIUM — LLM ignored protein dampener
                risk  = "MEDIUM"
                score = min(score, 6)
                peak  = min(peak,  50)
                result["spike_risk"] = risk
                result["reason"]     = (
                    result.get("reason", "") +
                    " (Downgraded: millet + protein combination has a blunted glucose response.)"
                )

            # ── Fix score / peak contradictions ─────────────────────────────
            clamp = {"HIGH": (7, 10), "MEDIUM": (4, 6), "LOW": (1, 3)}
            lo, hi = clamp[risk]
            result["risk_score"] = max(lo, min(hi, score))

            peak_bounds = {"HIGH": (60, 100), "MEDIUM": (25, 50), "LOW": (10, 25)}
            p_lo, p_hi  = peak_bounds[risk]
            result["peak_estimate_mg_dl"] = max(p_lo, min(p_hi, peak))

        result["meal"]       = meal_description
        result["latest_cgm"] = latest_cgm
        return result