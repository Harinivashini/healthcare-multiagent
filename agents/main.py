"""
agents/main.py
───────────────
FastAPI backend — entry-point for the healthcare multi-agent system.
"""

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional

from agents.orchestrator import run_agent
from data.db import (
    list_users, get_user,
    get_cgm_history, get_mood_history,
    get_food_history, get_latest_meal_plan,
    get_critical_alerts, create_alerts_table,
)

app = FastAPI(
    title="Healthcare MultiAgent API",
    description="Personalised healthcare demo — Groq + FastAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────────────────

class AgentRequest(BaseModel):
    intent: str
    payload: dict


class AgentResponse(BaseModel):
    intent: str
    result: Any
    error: Optional[str] = None


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "healthcare-multiagent"}


# ── CopilotKit stub (prevents 404 from sidebar) ───────────────────────────────

@app.options("/copilotkit")
async def copilotkit_options():
    return JSONResponse(content={}, status_code=200)


@app.post("/copilotkit")
async def copilotkit_endpoint(request: Request):
    return JSONResponse(
        content={"actions": [], "messages": [], "threadId": ""},
        status_code=200
    )


# ── Agent dispatcher ──────────────────────────────────────────────────────────

@app.post("/agent", response_model=AgentResponse)
def dispatch_agent(request: AgentRequest):
    """
    Route an intent to the appropriate agent.

    Intents & required payload fields:
      greet      → { user_id }
      mood       → { user_id, mood }
      cgm        → { user_id, reading }
      food       → { user_id, description, timestamp? }
      meal_plan  → { user_id }
      interrupt  → { query, current_flow? }
    """
    try:
        result = run_agent(request.intent, request.payload)
        return AgentResponse(intent=request.intent, result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()   # prints full error to backend terminal
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


# ── Data / user routes ────────────────────────────────────────────────────────

@app.get("/users")
def get_users(limit: int = 100):
    return {"users": list_users(limit=limit)}


@app.get("/users/{user_id}")
def get_user_profile(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
    return user


@app.get("/users/{user_id}/cgm")
def get_user_cgm(user_id: int, limit: int = 7):
    return {"user_id": user_id, "cgm_history": get_cgm_history(user_id, limit)}


@app.get("/users/{user_id}/mood")
def get_user_mood(user_id: int, limit: int = 7):
    return {"user_id": user_id, "mood_history": get_mood_history(user_id, limit)}


@app.get("/users/{user_id}/food")
def get_user_food(user_id: int, limit: int = 10):
    return {"user_id": user_id, "food_history": get_food_history(user_id, limit)}


@app.get("/users/{user_id}/meal_plan")
def get_user_meal_plan(user_id: int):
    plan = get_latest_meal_plan(user_id)
    if not plan:
        raise HTTPException(status_code=404, detail="No meal plan found for this user.")
    return {"user_id": user_id, **plan}


@app.get("/users/{user_id}/alerts")
def get_user_alerts(user_id: int, limit: int = 20):
    return {"user_id": user_id, "alerts": get_critical_alerts(user_id, limit)}


@app.on_event("startup")
async def startup_event():
    create_alerts_table()


if __name__ == "__main__":
    import uvicorn
    from data.generate_dataset import main as seed_db
    seed_db()
    uvicorn.run(
        "agents.main:app",
        host=os.environ.get("BACKEND_HOST", "0.0.0.0"),
        port=int(os.environ.get("BACKEND_PORT", 8000)),
        reload=False,
    )