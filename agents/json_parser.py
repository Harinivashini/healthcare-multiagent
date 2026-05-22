"""
agents/json_parser.py
──────────────────────
Shared aggressive JSON parser used by all LLM agents.
Tries multiple strategies to extract valid JSON from LLM responses.
"""

import json
import re


def parse_json(raw: str) -> dict:
    """
    Try every strategy to extract valid JSON from an LLM response.
    Returns the parsed dict, or {"parse_error": True, "raw": raw} on failure.
    """
    if not raw:
        return {"parse_error": True, "raw": ""}

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

    # Strategy 3: find outermost { ... }
    try:
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except Exception:
        pass

    # Strategy 4: strip fences then find outermost { ... }
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        start   = cleaned.index("{")
        end     = cleaned.rindex("}") + 1
        chunk   = cleaned[start:end]
        return json.loads(chunk)
    except Exception:
        pass

    # Strategy 5: remove trailing commas (common LLM mistake)
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        start   = cleaned.index("{")
        end     = cleaned.rindex("}") + 1
        chunk   = cleaned[start:end]
        chunk   = re.sub(r",\s*([}\]])", r"\1", chunk)
        return json.loads(chunk)
    except Exception:
        pass

    # All strategies failed
    return {"parse_error": True, "raw": raw}