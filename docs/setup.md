# Setup Guide

This guide explains how to run Swasthya Sathi AI locally for development and testing.

## Prerequisites

Install:

- Python 3.11 or newer.
- Node.js 18 or newer.
- npm.
- Git.

Optional:

- Docker and Docker Compose.
- API keys for AI chat and report generation.

## Clone the Repository

```bash
git clone https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI.git
cd Swasthya-Sathi-AI
```

## Backend Setup

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

The backend runs at:

```text
http://localhost:8000
```

The API documentation is available at:

```text
http://localhost:8000/docs
```

## Backend Environment Variables

Create a local `.env` file inside `backend/` if you want AI features to call external model providers.

```env
GEMINI_API_KEY=your-primary-gemini-key
GEMINI_API_KEY_2=optional-fallback-key
GEMINI_MODEL=gemini-2.5-flash
OPENROUTER_API_KEY=optional-openrouter-key
```

Basic REST endpoints and tests can run without these keys. AI chat and generated reports need a configured provider key.

## Frontend Setup

Open a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

If the backend is not served from the same origin, create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Restart the Vite dev server after changing environment variables.

## Run Tests

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Docker Setup

From the repository root:

```bash
docker compose up --build
```

Use Docker when you want to test both services together in an environment closer to deployment.

## Common Issues

### Frontend Cannot Reach Backend

Check that the backend is running at `http://localhost:8000`, then set:

```env
VITE_API_URL=http://localhost:8000
```

### AI Chat Fails

Confirm that at least one provider key is configured in `backend/.env`.

### Database Looks Empty

Run the seed script again:

```bash
cd backend
python seed.py
```

### PowerShell Blocks Virtual Environment Activation

If activation is blocked, run PowerShell as the current user and allow script execution for the session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```
