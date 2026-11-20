# Local Development & Setup Guide

This guide walks you through setting up, configuring, running, and testing **Swasthya Sathi AI** on your local development machine.

---

## Prerequisites

Ensure you have the following installed before beginning:

| Tool | Minimum Version | Recommended | Check Command |
|---|---|---|---|
| **Python** | 3.11+ | 3.11 or 3.12 | `python --version` |
| **Node.js** | 18+ | 20 LTS or 22 LTS | `node --version` |
| **npm** | 9+ | 10+ | `npm --version` |
| **Git** | 2.30+ | Latest | `git --version` |
| **Docker** *(Optional)* | 20+ | Latest with Compose v2 | `docker compose version` |

An API key for Google Gemini is recommended for testing the AI chat and report features. You can get a free API key at [Google AI Studio](https://aistudio.google.com/apikey).

---

## 1. Clone the Repository

```bash
git clone https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI.git
cd Swasthya-Sathi-AI
```

---

## 2. Backend Setup

### Option A: macOS & Linux (Bash / Zsh)

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Upgrade pip and install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Open `backend/.env` in your editor and add your Gemini API key:
   ```env
   GEMINI_API_KEY=AIzaSy...your_actual_key...
   GEMINI_MODEL=gemini-2.5-flash
   ```
   *(Note: The backend REST APIs and unit tests will run even without an API key, but AI chat endpoints require it).*

5. Seed the SQLite database with initial demo data:
   ```bash
   python seed.py
   ```

6. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

### Option B: Windows (PowerShell)

1. Open PowerShell and navigate to the backend directory:
   ```powershell
   cd backend
   ```

2. Create the virtual environment:
   ```powershell
   python -m venv .venv
   ```

3. If script execution is restricted, allow it for the current process:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

4. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

5. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Create your `.env` file:
   ```powershell
   Copy-Item .env.example .env
   ```
   Add your `GEMINI_API_KEY` to `backend/.env`.

7. Populate demo health workers and attendance records:
   ```powershell
   python seed.py
   ```

8. Launch the backend server:
   ```powershell
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

The backend will be live at:
* **API Root**: [http://localhost:8000](http://localhost:8000)
* **Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 3. Frontend Setup

Open a second terminal window in the project root:

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

3. *(Optional)* Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   During local development, Vite's proxy automatically routes `/api` requests to `http://localhost:8000`, so `VITE_API_URL` can be left blank.

4. Start the Vite development server:
   ```bash
   npm run dev
   ```

The frontend application will be live at:
* **Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 4. Running with Docker Compose

If you have Docker installed, you can spin up both frontend and backend in unified containers:

```bash
# From the repository root
docker compose up --build
```

To run in the background (detached mode):
```bash
docker compose up -d
```

To stop containers:
```bash
docker compose down
```

---

## 5. Running Quality Checks & Tests

Always run checks before submitting changes:

### Backend Checks
```bash
cd backend

# Run backend unit tests with Pytest
pytest -v

# Run lint checks with Ruff
ruff check .

# Syntax compilation check
python -m compileall -q .
```

### Frontend Checks
```bash
cd frontend

# Run frontend unit tests with Vitest
npm test

# Run ESLint linter
npm run lint

# Build production assets with Vite
npm run build
```

---

## 6. Troubleshooting Common Issues

### Issue 1: `Port 8000 already in use`
* **Cause**: Another uvicorn instance or background process is already bound to port 8000.
* **Fix (Windows)**:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
  ```
* **Fix (macOS/Linux)**:
  ```bash
  lsof -ti :8000 | xargs kill -9
  ```

### Issue 2: `Frontend cannot connect to backend` / `Network Error`
* **Cause**: Backend server is not running or running on an unexpected port.
* **Fix**: Ensure `uvicorn main:app --reload` is running on `http://127.0.0.1:8000`. Test it by opening `http://localhost:8000/` in your browser. Verify `frontend/.env` does not have a misconfigured `VITE_API_URL`.

### Issue 3: `All Gemini API Keys failed` in AI Chat
* **Cause**: `GEMINI_API_KEY` is missing, expired, or rate-limited.
* **Fix**: Obtain a valid key from [Google AI Studio](https://aistudio.google.com/apikey) and verify it is present in `backend/.env`. You can also supply fallback keys (`GEMINI_API_KEY_2`, etc.).

### Issue 4: `Database empty / No workers found`
* **Cause**: The SQLite database hasn't been seeded yet.
* **Fix**: In the `backend/` directory, run:
  ```bash
  python seed.py
  ```

### Issue 5: PowerShell `UnauthorizedAccess` / `Activate.ps1 cannot be loaded`
* **Cause**: Windows PowerShell execution policy restricts running unsigned scripts.
* **Fix**:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```

### Issue 6: `npm error EUSAGE / Missing packages`
* **Cause**: Lockfile mismatch when using `npm ci`.
* **Fix**: Run `npm install` inside the `frontend/` directory to sync your node dependencies with `package.json`.
