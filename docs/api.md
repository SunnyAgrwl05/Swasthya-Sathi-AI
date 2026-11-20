# Swasthya Sathi AI — REST API Documentation

Comprehensive REST API reference for the Swasthya Sathi AI backend service (`http://localhost:8000`).

Interactive OpenAPI documentation is available locally at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).

---

## Base URL & General Conventions

- **Local Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **Cross-Origin Resource Sharing (CORS)**: Enabled for all origins (`*`) with credential support.

### Common HTTP Status Codes
| Status Code | Meaning | Description |
| --- | --- | --- |
| `200 OK` | Success | Request succeeded. |
| `400 Bad Request` | Client Error | Invalid parameters or business constraint violation (e.g., duplicate `worker_code`). |
| `404 Not Found` | Resource Missing | Entity ID does not exist in database. |
| `422 Unprocessable Entity` | Validation Failed | Missing required fields or schema type mismatch. |
| `500 Internal Error` | Server Error | Unhandled server or database exception. |

---

## 1. System Health & Diagnostics

### `GET /`
Returns the operational health and database connectivity status.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "service": "Swasthya Sathi AI Backend",
  "database": "Connected"
}
```

---

## 2. Health Workers (`/api/workers`)

### `GET /api/workers`
Returns a list of all registered healthcare workers (ASHA, ANM, Anganwadi).

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "worker_code": "ASHA-PAT-001",
    "name": "Sunita Devi",
    "role": "ASHA Worker",
    "center": "Patna Sadar PHC",
    "phone": "+919876543210"
  }
]
```

### `POST /api/workers`
Registers a new healthcare worker in the system.

**Request Body:**
```json
{
  "worker_code": "ANM-DAN-101",
  "name": "Pooja Kumari",
  "role": "ANM",
  "center": "Danapur Sub-Center",
  "phone": "+919812345678"
}
```

**Response `200 OK`:**
```json
{
  "id": 2,
  "worker_code": "ANM-DAN-101",
  "name": "Pooja Kumari",
  "role": "ANM",
  "center": "Danapur Sub-Center",
  "phone": "+919812345678"
}
```

**Errors:**
- `400 Bad Request`: `{"detail": "Worker with this worker_code already exists"}`
- `422 Unprocessable Entity`: Missing required fields (`worker_code`, `name`, `center`, `phone`).

### `DELETE /api/workers/{worker_id}`
Deletes a healthcare worker by their numeric ID.

**Response `200 OK`:**
```json
{
  "deleted": 2
}
```

**Errors:**
- `404 Not Found`: `{"detail": "Worker not found"}`

---

## 3. Attendance Management (`/api/attendance`)

### `GET /api/attendance`
Retrieves logged attendance records, ordered by date descending (up to 500 records).

**Query Parameters:**
| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `worker_id` | Integer | Optional | Filter attendance logs for a specific worker. |

**Response `200 OK`:**
```json
[
  {
    "id": 101,
    "worker_id": 1,
    "date": "2026-11-17",
    "status": "present",
    "note": "Field immunisation drive",
    "marked_by": "manual"
  }
]
```

### `POST /api/attendance`
Creates or idempotently updates an attendance record for a worker on a given date. Automatically appends an entry to the `AuditLog`.

**Request Body:**
```json
{
  "worker_id": 1,
  "date": "2026-11-17",
  "status": "present",
  "note": "Village survey completed"
}
```

**Response `200 OK`:**
```json
{
  "id": 101,
  "worker_id": 1,
  "date": "2026-11-17",
  "status": "present",
  "note": "Village survey completed",
  "marked_by": "manual"
}
```

---

## 4. Analytics & Summaries (`/api/analytics`)

### `GET /api/analytics/summary`
Calculates attendance statistics over a rolling window. Results are sorted lowest attendance percentage first to prioritize follow-up.

**Query Parameters:**
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `days` | Integer | `30` | Number of past days to include in window. |

**Response `200 OK`:**
```json
[
  {
    "worker_id": 2,
    "name": "Pooja Kumari",
    "role": "ANM",
    "center": "Danapur Sub-Center",
    "present": 12,
    "total_logged": 20,
    "attendance_pct": 60.0
  },
  {
    "worker_id": 1,
    "name": "Sunita Devi",
    "role": "ASHA Worker",
    "center": "Patna Sadar PHC",
    "present": 28,
    "total_logged": 30,
    "attendance_pct": 93.3
  }
]
```

---

## 5. AI Chat & Operations Agent (`/api/chat`)

### `POST /api/chat`
Sends a supervisor prompt to the AI agent. The agent can execute backend tool actions (marking attendance, querying summaries, detecting low attendance) and records both `ChatLog` and `AgentLog`.

**Request Body:**
```json
{
  "message": "Sunita Devi ko aaj present mark karo aur uska attendance percentage batao"
}
```

**Response `200 OK`:**
```json
{
  "reply": "Sunita Devi (ASHA-PAT-001) ki aaj (2026-11-17) ki upasthiti 'Present' mark kar di gayi hai. Pichhle 30 dino me unki attendance 93.3% hai.",
  "actions_taken": [
    "mark_attendance(ASHA-PAT-001, present)"
  ]
}
```

---

## 6. Supervisor Broadcasts & Insights

### `GET /api/broadcast/daily`
Generates a morning broadcast briefing for field workers and logs WhatsApp/SMS notifications in `NotificationLog`.

**Response `200 OK`:**
```json
{
  "message": "सुप्रभात स्वास्थ्य साथियों! आज का दिन मातृ एवं शिशु स्वास्थ्य जांच अभियान के लिए समर्पित है। कृपया समय पर रिपोर्ट करें।"
}
```

### `GET /api/insights/weekly`
Returns an AI-synthesized weekly operational overview for supervisors.

**Query Parameters:**
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `language` | String | `"hi"` | Language code (`"hi"` for Hindi, `"en"` for English). |

**Response `200 OK`:**
```json
{
  "report": "साप्ताहिक सारांश: इस सप्ताह कुल औसत उपस्थिति 88.5% रही। 2 स्वास्थ्य कार्यकर्ताओं को अतिरिक्त सहायता की आवश्यकता है।"
}
```

### `POST /api/insights/weekly`
Alternative POST endpoint for weekly insights.

**Request Body:**
```json
{
  "language": "en"
}
```

**Response `200 OK`:**
```json
{
  "report": "Weekly Operations Summary: Overall workforce attendance is 88.5%. Danapur center recorded 100% compliance."
}
```
