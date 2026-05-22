# 🏥 Personalised Healthcare MultiAgent Demo

A proof-of-concept multi-agent healthcare system built with **Agno**, **Groq (LLaMA 3 70B)**, **FastAPI**, and **Next.js + CopilotKit**.

---

## ✨ Features

| Agent | What it does |
|---|---|
| **Greeting Agent** | Validates User ID, retrieves profile, delivers personalised greeting |
| **Mood Tracker Agent** | Logs mood, computes rolling 7-session average, returns empathetic LLM response |
| **CGM Agent** | Validates glucose readings (80–300 mg/dL), flags personal range deviations |
| **Food Intake Agent** | Accepts free-text meals, estimates macros via LLM (carbs / protein / fat) |
| **Meal Planner Agent** | Generates adaptive 3-meal plan factoring diet, conditions, CGM, and mood |
| **Interrupt Agent** | Answers any off-topic question at any time; gracefully resumes the active flow |

---

## 📁 Project Structure

```
healthcare-multiagent/
├── .env.example              # ← copy to .env and fill GROQ_API_KEY
├── .gitignore
├── docker-compose.yml        # single command spin-up
│
├── data/
│   ├── generate_dataset.py   # generates 100-user SQLite dataset
│   └── db.py                 # shared DB helper (all agents import this)
│
├── agents/
│   ├── llm_client.py         # Groq API wrapper (one place to swap models)
│   ├── greeting_agent.py
│   ├── mood_tracker_agent.py
│   ├── cgm_agent.py
│   ├── food_intake_agent.py
│   ├── meal_planner_agent.py
│   ├── interrupt_agent.py
│   ├── orchestrator.py       # Agno orchestrator + intent dispatcher
│   ├── main.py               # FastAPI app (all HTTP routes)
│   └── requirements.txt
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── hooks/
│       │   └── useAgent.ts   # all API calls in one hook
│       ├── components/
│       │   ├── CGMChart.tsx
│       │   ├── MoodChart.tsx
│       │   ├── FoodLogForm.tsx
│       │   └── MealPlanCard.tsx
│       ├── pages/
│       │   ├── _app.tsx
│       │   └── index.tsx     # main dashboard
│       └── styles/
│           └── globals.css
│
├── deploy/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
└── docs/
    ├── agent_specs.json      # JSON schema for every agent
    └── sequence_diagram.md   # Mermaid sequence diagram
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- A free [Groq API key](https://console.groq.com)

### 1. Clone & configure

```bash
git clone https://github.com/<your-username>/healthcare-multiagent.git
cd healthcare-multiagent
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000
- API docs:    http://localhost:8000/docs

### 3. Test the demo

1. Open http://localhost:3000
2. Enter any User ID between **1 and 100**
3. The system will greet you by name
4. Use the dashboard to log mood, CGM, food; generate a meal plan
5. Ask any health question in the chat sidebar (Interrupt Agent)

---

## 🛠 Local Development (without Docker)

### Backend

```bash
# Create virtualenv (or use uv)
python -m venv .venv && source .venv/bin/activate
pip install -r agents/requirements.txt

# Seed dataset
python data/generate_dataset.py

# Start API
uvicorn agents.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/agent` | Intent-based agent dispatcher |
| `GET`  | `/users` | List users (dataset preview) |
| `GET`  | `/users/{id}` | Get user profile |
| `GET`  | `/users/{id}/cgm` | CGM history |
| `GET`  | `/users/{id}/mood` | Mood history |
| `GET`  | `/users/{id}/food` | Food log |
| `GET`  | `/users/{id}/meal_plan` | Latest meal plan |
| `GET`  | `/health` | Health check |

### Example `/agent` calls

```json
// Greet
{ "intent": "greet", "payload": { "user_id": 1 } }

// Log mood
{ "intent": "mood", "payload": { "user_id": 1, "mood": "happy" } }

// Log CGM
{ "intent": "cgm", "payload": { "user_id": 1, "reading": 145.5 } }

// Log food
{ "intent": "food", "payload": { "user_id": 1, "description": "oatmeal with blueberries" } }

// Generate meal plan
{ "intent": "meal_plan", "payload": { "user_id": 1 } }

// General Q&A (interrupt)
{ "intent": "interrupt", "payload": { "query": "What is insulin?", "current_flow": "cgm" } }
```

---

## 🏗 Design Decisions

| Decision | Rationale |
|---|---|
| **One module per agent** | Separation of concerns, easy to test individually |
| **Groq (LLaMA 3 70B)** | Fast inference, free tier, strong instruction-following |
| **SQLite** | Zero-config, perfect for a demo; easily swapped for Postgres |
| **Agno orchestrator** | Lightweight, tool-based agent framework; maps cleanly to our intent table |
| **CopilotKit sidebar** | Drop-in conversational UI with full React state access |
| **Intent dispatcher** | Deterministic routing avoids LLM hallucinating the wrong tool in structured flows |

---

## 📊 Evaluation Criteria Coverage

| Criterion | How it's addressed |
|---|---|
| **Completeness** | All 6 agents implemented and integrated end-to-end |
| **Code Quality** | One file per module, docstrings on every class/function, typed |
| **Innovativeness** | Adaptive CGM-aware meal planning, interrupt flow, macro estimation via LLM |
| **Deployment** | Single `docker-compose up --build` starts everything |

---

## 📄 License

MIT
