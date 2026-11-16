# Comprehensive Testing Guide

This document describes the automated testing framework for **Swasthya Sathi AI** backend using **Pytest**, **HTTPX**, and **pytest-cov**.

Closes Issues [#16](https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI/issues/16) and [#17](https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI/issues/17).

---

## 1. Overview & Test Architecture

The backend test suite is designed for high reliability, deterministic execution, and fast feedback loops:
- **In-Memory Database Isolation**: All tests run against isolated in-memory SQLite instances using SQLAlchemy's `StaticPool`. Tests never modify or depend on local development `.db` files.
- **Dependency Overrides**: The FastAPI `get_db` dependency is overridden per test function in `conftest.py`, ensuring full cleanup before and after every test.
- **External API Mocking**: AI integrations (Google Gemini API and OpenRouter) are cleanly mocked via `unittest.mock.patch` to avoid network flakiness, rate limits, and API credential requirements.

```
backend/
├── pytest.ini                  # Pytest configuration file
├── requirements.txt            # Includes pytest and pytest-cov
└── tests/
    ├── conftest.py             # In-memory SQLite fixtures & TestClient setup
    ├── test_root.py            # Basic root endpoint verification
    ├── test_auth.py            # Health check & CORS verification
    ├── test_health_worker.py   # Worker CRUD, duplicates, validation tests
    ├── test_attendance.py      # Attendance logging, updates, filtering
    ├── test_analytics.py       # Attendance summary, broadcasts, insights
    └── test_ai_agent.py        # Chat agent endpoint & audit log verification
```

---

## 2. Running the Test Suite

### Run All Tests
From the project root:
```bash
python -m pytest backend
```
Or from within the `backend/` directory:
```bash
pytest
```

### Run with Detailed Verbosity
```bash
pytest -v
```

### Run a Specific Test Module
```bash
pytest tests/test_health_worker.py -v
```

### Run Tests with Coverage Report
Generate code coverage metrics across backend services:
```bash
pytest --cov=. --cov-report=term-missing
```

To export HTML coverage reports:
```bash
pytest --cov=. --cov-report=html
```

---

## 3. Test Modules Summary

| Module | Scope | Key Test Cases |
| :--- | :--- | :--- |
| `test_auth.py` | Health Check & Middleware | `GET /` status verification, CORS header assertions |
| `test_health_worker.py` | Health Worker Roster | Worker listing, worker creation, duplicate `worker_code` rejection, validation rules, deletion |
| `test_attendance.py` | Attendance Records | Logging attendance, in-place updates for same date, worker filtering, schema validation |
| `test_analytics.py` | Analytics & Broadcasts | Summary percentage calculations, daily WhatsApp broadcasts, weekly insights generation |
| `test_ai_agent.py` | AI Agent & Audit Logging | `POST /api/chat` execution, `ChatLog` and `AgentLog` database persistence, error handling |
| `test_root.py` | Baseline Health | FastAPI root endpoint status |
| `test_workers.py` | Legacy Roster Check | Baseline worker endpoint test |
