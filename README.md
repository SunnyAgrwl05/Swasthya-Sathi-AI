# Swasthya Sathi AI

**An AI agent that manages rural health worker attendance in plain Hindi/English — not a chatbot skin on a form.**

Built for the Google AI Agent Builder Series 2026 (HiDevs).

![thumbnail](assets/thumbnail.png)

<br>

## The Problem

Bihar's PHC (Primary Health Centre) network runs on hundreds of ASHA, ANM, and Anganwadi workers spread across rural sub-centers. Supervisors currently track their attendance manually — in paper registers or WhatsApp groups. There's no visibility into who's underperforming until it's already too late to act.

I built this to fix that.

<br>

## This Is an Agent, Not a Form

Most "AI attendance" tools just wrap a chat UI around a database. This project takes a different approach — Gemini is given a set of real Python tools (`mark_attendance`, `get_attendance_summary`, `find_low_attendance_workers`, `who_has_not_marked_today`, `list_workers`), and the model decides on its own, turn by turn, which tool(s) to call and in what order — using Gemini's automatic function calling.

A supervisor can type:

> "Sunny Kumar ko aaj half-day mark karo aur uska is month ka summary dikhao"

...and the agent will chain two tool calls automatically, then reply in the same language the supervisor used. Every tool call the agent actually performs is shown back as a small audit-trail chip, so nothing happens silently in the background.

**The proactive feature:** `find_low_attendance_workers` lets a supervisor simply ask "who's underperforming this month?" and the agent flags anyone below a configurable threshold — turning a reactive register into something that surfaces problems before they escalate.

<br>

## Tech Stack

| Layer | Choice |
|---|---|
| Agent / LLM | Gemini 2.0 Flash, Python SDK, automatic function calling |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Frontend | React 18 + Vite + Tailwind CSS + Recharts |
| Deploy | Render (backend) + Vercel (frontend), Docker also included |

<br>

## Project Structure

swasthya-sathi-ai/
├── backend/
│   ├── main.py              # FastAPI app, REST + /api/chat
│   ├── agent.py             # Gemini agent + tool functions
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # SQLite session setup
│   ├── seed.py              # Demo data generator
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   │       ├── Header
│   │       ├── StatCards
│   │       ├── AttendanceChart
│   │       ├── WorkerTable
│   │       ├── ChatAgent
│   │       └── PulseDivider
│   ├── package.json
│   └── Dockerfile
│
├── assets/
├── docker-compose.yml
├── render.yaml
└── DEMO_SCRIPT.md
