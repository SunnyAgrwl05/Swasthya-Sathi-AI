# 🧪 Backend Testing Guide

## Overview

Swasthya Sathi AI backend utilizes **Pytest** alongside **pytest-cov** and **httpx** (`fastapi.testclient.TestClient`) to provide end-to-end automated testing for API endpoints, database ORM models, agent tool executions, and analytical queries.

---

## Running Tests

From the `backend/` directory:

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run with test coverage report
```bash
pytest --cov=. --cov-report=term-missing
```

### Run specific test module
```bash
pytest tests/test_health_worker.py -v
```

---

## Test Suite Architecture

```text
backend/tests/
├── conftest.py           # In-memory SQLite database setup and TestClient fixtures
├── test_root.py          # Service health and root route verification
├── test_health_worker.py # Health Worker CRUD, unique constraint checks
├── test_attendance.py    # Attendance logging, validation, and filtering
├── test_analytics.py     # Attendance rate calculation and sorting orders
├── test_database.py      # SQLAlchemy ORM models, relationships, and persistence
├── test_ai_agent.py      # AI Chat endpoint, broadcast, and weekly reports (mocked LLM)
├── test_agent_tools.py   # Agent execution tools (fuzzy matching, attendance marker)
└── test_auth.py          # CORS middleware and route not found handling
```

---

## Mocking External LLM APIs

External Google Gemini / OpenRouter API calls are mocked using `unittest.mock.patch` in `test_ai_agent.py` to ensure fast, deterministic tests without incurring API quota or network dependencies:

```python
with patch("main.chat_with_agent", return_value=("Attendance marked", ["mark_worker_attendance"])):
    res = client.post("/api/chat", json={"message": "Mark attendance"})
    assert res.status_code == 200
```
