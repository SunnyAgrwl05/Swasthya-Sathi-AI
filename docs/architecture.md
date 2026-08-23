# System Architecture

Swasthya Sathi AI uses a client-server architecture with an AI-assisted operations layer. The frontend presents dashboards and chat workflows, the backend owns business logic and persistence, and the AI agent coordinates attendance-related actions through controlled backend functions.

## High-Level Flow

```text
Supervisor
    |
    v
React Dashboard
    |
    | HTTP / JSON
    v
FastAPI Backend
    |
    +--> Worker management
    +--> Attendance records
    +--> Analytics summaries
    +--> Broadcast and insight endpoints
    +--> AI chat orchestration
    |
    v
SQLAlchemy Models
    |
    v
SQLite Database
```

## Frontend Layer

The frontend is located in `frontend/` and is built with React and Vite.

Core responsibilities:

- Render the operational dashboard.
- Display worker and attendance summaries.
- Show charts and stat cards.
- Provide the chat interface for supervisor questions.
- Call backend endpoints through `frontend/src/api.js`.

Important files:

- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/components/StatCards.jsx`
- `frontend/src/components/AttendanceChart.jsx`
- `frontend/src/components/WorkerTable.jsx`
- `frontend/src/components/ChatAgent.jsx`
- `frontend/src/components/DailyBroadcast.jsx`
- `frontend/src/components/WeeklyInsights.jsx`

## Backend Layer

The backend is located in `backend/` and is built with FastAPI.

Core responsibilities:

- Expose REST endpoints.
- Validate request and response payloads.
- Read and write worker and attendance data.
- Generate analytics summaries.
- Route chat requests to the AI operations agent.
- Persist audit, chat, notification, and agent logs.

Important files:

- `backend/main.py`
- `backend/models.py`
- `backend/schemas.py`
- `backend/database.py`
- `backend/seed.py`
- `backend/tests/`

## Data Model

The SQLAlchemy models represent the operational state of the application.

| Model | Purpose |
| --- | --- |
| `HealthWorker` | Stores ASHA, ANM, Anganwadi, and other worker profiles |
| `AttendanceRecord` | Stores date-based attendance status per worker |
| `ChatLog` | Stores user and agent messages |
| `HealthCenter` | Stores healthcare facility metadata |
| `NotificationLog` | Stores generated broadcast notification logs |
| `AuditLog` | Stores manual or AI-driven attendance audit events |
| `AgentLog` | Stores AI request metadata and tool execution details |

## AI Operations Agent

The agent logic lives in `backend/agent.py`.

It provides attendance-oriented functions that can:

- Mark or update attendance.
- Resolve worker names with fuzzy matching.
- Summarize attendance for one or more workers.
- Detect low-attendance workers.
- List registered workers.
- Identify workers missing today's attendance.
- Generate daily broadcasts.
- Generate weekly insights.

This design keeps the AI layer grounded in backend functions instead of allowing it to invent records or percentages.

## API Boundary

The frontend talks to the backend through JSON endpoints:

| Endpoint | Responsibility |
| --- | --- |
| `/api/workers` | Worker listing and creation |
| `/api/attendance` | Attendance listing and mutation |
| `/api/analytics/summary` | Attendance percentage summaries |
| `/api/chat` | Natural-language AI operations |
| `/api/broadcast/daily` | Daily supervisor update generation |
| `/api/insights/weekly` | Weekly attendance trend reporting |

## Deployment View

```text
Vercel
  |
  +-- React frontend

Render
  |
  +-- FastAPI backend
  +-- SQLite database file
```

For production deployments, a managed relational database and stricter CORS settings should be considered before handling real operational data.
