# Swasthya Sathi AI

**An AI agent that manages rural health worker attendance in plain Hindi/English — not a chatbot skin on a form.**

Built for the Google AI Agent Builder Series 2026 (HiDevs).

![thumbnail](assets/thumbnail.png)

## The problem

Bihar's PHC (Primary Health Centre) network runs on ASHA, ANM and Anganwadi workers spread across dozens of rural sub-centers. Supervisors track their attendance manually in registers or WhatsApp — no visibility into who's underperforming until it's too late.

## What makes this an *agent*, not a form

Most "AI attendance" submissions wrap a chat UI around a database. Swasthya Sathi AI instead gives **Gemini a set of real Python tools** (`mark_attendance`, `get_attendance_summary`, `find_low_attendance_workers`, `who_has_not_marked_today`, `list_workers`) and lets the model decide, turn by turn, which tool(s) to call and in what order — using Gemini's automatic function calling. A supervisor can type:

> "Sunita Devi ko aaj half-day mark karo aur uska is month ka summary dikhao"

...and the agent will chain two tool calls on its own, then reply in the same language the supervisor used. Every tool call the agent actually performs is shown back to the user as a small audit-trail chip, so nothing happens silently.

**The proactive feature:** `find_low_attendance_workers` lets a supervisor ask "kaun underperform kar raha hai is month?" and the agent flags anyone below a configurable threshold — turning a reactive register into something that surfaces problems before they escalate.

## Tech stack

| Layer | Choice |
|---|---|
| Agent / LLM | Gemini 2.0 Flash, Python SDK, automatic function calling |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | React 18 + Vite + Tailwind CSS + Recharts |
| Deploy | Render (backend) + Vercel (frontend), Docker also included |

## Project structure

```
swasthya-sathi-ai/
├── backend/
│   ├── main.py          # FastAPI app, REST + /api/chat
│   ├── agent.py         # Gemini agent + tool functions (the core feature)
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── database.py      # SQLite session setup
│   ├── seed.py          # Demo data generator
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/  # Header, StatCards, AttendanceChart, WorkerTable, ChatAgent, PulseDivider
│   ├── package.json
│   └── Dockerfile
├── assets/thumbnail.svg / .png
├── docker-compose.yml
├── render.yaml
└── DEMO_SCRIPT.md
```

## Run locally

**1. Get a free Gemini API key:** https://aistudio.google.com/apikey

**2. Backend**
```bash
cd backend
cp .env.example .env        # paste your GEMINI_API_KEY into .env
pip install -r requirements.txt --break-system-packages
python seed.py               # creates 5 demo workers + 30 days of history
uvicorn main:app --reload --port 8000
```

**3. Frontend** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — dashboard on the left, AI agent chat on the right.

**Or with Docker:**
```bash
cp backend/.env.example backend/.env   # add your key
docker compose up --build
```

## Deploy (for the submission link)

**Backend → Render**
1. Push this repo to GitHub.
2. New → Blueprint on Render, point it at your repo (uses `render.yaml`).
3. Set `GEMINI_API_KEY` in the Render dashboard's environment tab.
4. Note the live URL, e.g. `https://swasthya-sathi-ai-backend.onrender.com`.

**Frontend → Vercel**
1. Import the repo, set root directory to `frontend`.
2. Add environment variable `VITE_API_URL` = your Render backend URL.
3. Deploy. Vercel gives you the public link for the HiDevs submission form.

## Try these in the chat

- "Priya Kumari ko aaj present mark karo"
- "Is month kaun sabse kam attendance wala hai?"
- "Sunita Devi ka attendance summary dikhao"
- "Aaj kisne attendance nahi mark ki?"
- "Ramesh Yadav ko kal absent mark karo, reason: bimar tha"

## Author

Sunny Kumar — Co-Organizer & Tech Lead, GDG On Campus BCE Patna · Beta MLSA · GFG Campus Mantri
