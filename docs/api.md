# Swasthya Sathi AI - REST API Reference

The Swasthya Sathi AI backend is built on **FastAPI** and provides automatic interactive documentation via Swagger UI and ReDoc:

* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **OpenAPI JSON Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Base URL

| Environment | Base URL |
|---|---|
| Local Development | `http://localhost:8000` |
| Production Backend | `https://swasthya-sathi-ai.onrender.com` |

---

## Summary of Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/` | Service health status and database connectivity |
| **Workers** | `GET` | `/api/workers` | Retrieve all registered health workers |
| | `POST` | `/api/workers` | Register a new health worker |
| | `DELETE` | `/api/workers/{worker_id}` | Delete a health worker record |
| **Attendance** | `GET` | `/api/attendance` | Query attendance records with optional filtering |
| | `POST` | `/api/attendance` | Mark or update an attendance record |
| **Analytics** | `GET` | `/api/analytics/summary` | Retrieve attendance aggregation and trends |
| **AI Agent** | `POST` | `/api/chat` | Natural language chat with tool-calling operations agent |
| **Reports** | `GET` | `/api/broadcast/daily` | Generate automated daily supervisor broadcast |
| | `GET` | `/api/insights/weekly` | Generate weekly operational trends and AI insights (Hindi) |
| | `POST` | `/api/insights/weekly` | Generate weekly insights with customizable language |

---

## Endpoint Details

### 1. Health Check

#### `GET /`
Verifies backend service operational state and database connection.

* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "status": "ok",
  "service": "Swasthya Sathi AI Backend",
  "database": "Connected"
}
```

---

### 2. Health Workers

#### `GET /api/workers`
Returns the list of all registered healthcare workers across the primary healthcare network.

* **Response Status**: `200 OK`
* **Response Body**:
```json
[
  {
    "id": 1,
    "name": "Sunita Devi",
    "worker_code": "ASHA-001",
    "role": "ASHA",
    "phone": "+91 98765 43210",
    "center": "PHC Danapur",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Poonam Kumari",
    "worker_code": "ANM-002",
    "role": "ANM",
    "phone": "+91 98765 43211",
    "center": "PHC Bihta",
    "is_active": true
  }
]
```

#### `POST /api/workers`
Registers a new worker (ASHA, ANM, Anganwadi, or Medical Officer).

* **Request Body** (`application/json`):
```json
{
  "name": "Kavita Singh",
  "worker_code": "ASHA-015",
  "role": "ASHA",
  "phone": "+91 98765 43225",
  "center": "PHC Maner",
  "is_active": true
}
```
* **Response Status**: `200 OK` (or `400 Bad Request` if `worker_code` already exists)

#### `DELETE /api/workers/{worker_id}`
Deletes a worker record and associated attendance records.

* **Parameters**: `worker_id` (integer, path parameter)
* **Response Status**: `200 OK`

---

### 3. Attendance Management

#### `GET /api/attendance`
Fetches attendance records with optional filtering.

* **Query Parameters**:
  * `worker_id` (optional, integer): Filter records for a specific worker ID.
* **Response Status**: `200 OK`
* **Response Body**:
```json
[
  {
    "id": 101,
    "worker_id": 1,
    "date": "2026-11-14",
    "status": "present",
    "notes": "Field vaccination drive",
    "worker_name": "Sunita Devi",
    "worker_role": "ASHA",
    "worker_center": "PHC Danapur"
  }
]
```

#### `POST /api/attendance`
Marks or updates attendance for a specific date and worker. If an entry exists for that worker and date, it updates the record; otherwise, a new record is created.

* **Request Body** (`application/json`):
```json
{
  "worker_id": 1,
  "date": "2026-11-14",
  "status": "present",
  "notes": "Verified by PHC supervisor"
}
```
* **Valid Status Values**: `"present"`, `"absent"`, `"half-day"`, `"leave"`
* **Response Status**: `200 OK`

---

### 4. Analytics Summary

#### `GET /api/analytics/summary`
Calculates attendance percentages, roster counts, present/absent tallies, and identifies low-attendance workers.

* **Query Parameters**:
  * `days` (optional, integer, default `30`): Lookback window in days.
* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "total_workers": 12,
  "present_today": 10,
  "absent_today": 2,
  "attendance_rate_today": 83.3,
  "average_monthly_rate": 87.5,
  "low_attendance_workers": [
    {
      "worker_id": 4,
      "name": "Manju Devi",
      "role": "ASHA",
      "attendance_rate": 62.5
    }
  ],
  "role_breakdown": {
    "ASHA": 7,
    "ANM": 3,
    "Anganwadi": 2
  }
}
```

---

### 5. AI Operations Agent Chat

#### `POST /api/chat`
Conversational endpoint powering the autonomous operations agent. The backend binds Python tools to the Gemini API (`gemini-2.5-flash`), allowing it to understand natural language in Hindi and English, execute appropriate tools, and return structured actions alongside natural text.

* **Request Body** (`application/json`):
```json
{
  "message": "Sunita Devi ko aaj present mark karo aur attendance summary batao"
}
```
* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "reply": "सुनीता देवी (ASHA) की उपस्थिति आज 'present' दर्ज कर दी गई है। उनका पिछले 30 दिनों का उपस्थिति प्रतिशत 92% है।",
  "actions_taken": [
    "mark_attendance(worker_name='Sunita Devi', status='present')",
    "get_worker_attendance_summary(worker_name='Sunita Devi')"
  ],
  "language": "hi"
}
```

---

### 6. Operational Broadcasts & Insights

#### `GET /api/broadcast/daily`
Generates a formatted daily summary notification suitable for messaging or field bulletin broadcast.

* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "broadcast": "*Swasthya Sathi AI — Daily Update (14 Nov 2026)*\nPresent today: 10/12\nMissing today: Manju Devi, Rekha Sharma\nLow attendance (<75%): Manju Devi (62.5%)"
}
```

#### `GET /api/insights/weekly` / `POST /api/insights/weekly`
Generates week-over-week analytical trends and strategic supervisor recommendations using the AI model.

* **Request Body for POST** (`application/json`):
```json
{
  "language": "hi"
}
```
* **Response Status**: `200 OK`
* **Response Body**:
```json
{
  "insights": "### साप्ताहिक परिचालन समीक्षा\n- कुल 12 कार्यकर्ताओं में से 10 सक्रिय रहे।\n- पीएचसी दानापुर का समग्र प्रदर्शन 89% रहा।\n- अनुशंसा: कम उपस्थिति वाले कार्यकर्ताओं से संपर्क करें।"
}
```

---

## Error Responses

The API uses standard HTTP error codes:

| HTTP Code | Meaning | Typical Scenario |
|---|---|---|
| `400 Bad Request` | Invalid input or duplicate key | Worker code already exists or invalid date format |
| `404 Not Found` | Resource not found | Requested `worker_id` does not exist |
| `422 Unprocessable Entity` | Schema validation error | Missing required fields or payload type mismatch |
| `500 Internal Server Error` | Unhandled server exception | Database lock or unexpected provider error |

Error response format:
```json
{
  "detail": "Worker with this worker_code already exists"
}
```
