# API Reference

> **Swasthya Sathi AI** – FastAPI Backend v1.0.0  
> Base URL (production): `https://swasthya-sathi-ai.onrender.com`  
> Base URL (local): `http://localhost:8000`  
> Interactive docs: `{BASE_URL}/docs`

---

## Table of Contents

1. [Root](#root)
2. [Health Workers](#health-workers)
3. [Attendance](#attendance)
4. [Analytics](#analytics)
5. [AI Chat](#ai-chat)
6. [Safety Verification](#safety-verification)
7. [Reports & Insights](#reports--insights)
8. [Error Codes](#error-codes)

---

## Root

### `GET /`

Health check.

**Response 200**:
```json
{
  "status": "ok",
  "service": "Swasthya Sathi AI Backend",
  "database": "Connected"
}
```

---

## Health Workers

### `GET /api/workers`

List all registered health workers.

**Response 200** – array of `WorkerOut`:
```json
[
  {
    "id": 1,
    "worker_code": "ASHA-DL-001",
    "name": "Sunita Devi",
    "role": "ASHA Worker",
    "center": "PHC Sector 4",
    "phone": "9876543210"
  }
]
```

---

### `POST /api/workers`

Register a new health worker.

**Request body** (`WorkerCreate`):
```json
{
  "worker_code": "ASHA-DL-001",
  "name": "Sunita Devi",
  "role": "ASHA Worker",
  "center": "PHC Sector 4",
  "phone": "9876543210"
}
```

**Response 200** – `WorkerOut` (see above)  
**Response 400** – `worker_code` already exists

---

### `DELETE /api/workers/{worker_id}`

Delete a health worker by ID.

**Response 200**:
```json
{ "deleted": 1 }
```

**Response 404** – worker not found

---

## Attendance

### `GET /api/attendance`

List attendance records (latest 500, most-recent first).

**Query params**:

| Param | Type | Description |
|---|---|---|
| `worker_id` | `int` (optional) | Filter by worker |

**Response 200** – array of `AttendanceOut`:
```json
[
  {
    "id": 1,
    "worker_id": 1,
    "date": "2024-07-27",
    "status": "present",
    "note": null,
    "marked_by": "manual"
  }
]
```

---

### `POST /api/attendance`

Create or update an attendance record. If a record exists for the same `(worker_id, date)`, it is **updated** (upsert behaviour).

**Request body** (`AttendanceCreate`):
```json
{
  "worker_id": 1,
  "date": "2024-07-27",
  "status": "present",
  "note": "On field visit"
}
```

**Response 200** – `AttendanceOut`

---

## Analytics

### `GET /api/analytics/summary`

Attendance summary per worker over the last N days.

**Query params**:

| Param | Type | Default | Description |
|---|---|---|---|
| `days` | `int` | `30` | Lookback window in days |

**Response 200**:
```json
[
  {
    "worker_id": 1,
    "name": "Sunita Devi",
    "role": "ASHA Worker",
    "center": "PHC Sector 4",
    "present": 22,
    "total_logged": 25,
    "attendance_pct": 88.0
  }
]
```

Results are sorted ascending by `attendance_pct` (lowest attendance first).

---

## AI Chat

### `POST /api/chat`

Send a natural-language query to the Swasthya Sathi AI operations agent. The agent can mark attendance, summarise trends, list workers, identify absentees, and generate broadcast messages.

**Request body** (`ChatRequest`):
```json
{
  "message": "Who has not marked attendance today?"
}
```

**Response 200** (`ChatResponse`):
```json
{
  "reply": "The following workers have not marked attendance today: ...",
  "actions_taken": ["who_has_not_marked_today"],
  "safety_warning": null,
  "is_flagged": false,
  "confidence_score": 0.9
}
```

| Field | Type | Description |
|---|---|---|
| `reply` | `string` | Full AI response text |
| `actions_taken` | `string[]` | Names of agent tools called |
| `safety_warning` | `string \| null` | Clinical safety warning (see [Safety Verification](#safety-verification)) |
| `is_flagged` | `bool` | `true` if medical content could not be verified |
| `confidence_score` | `float \| null` | Hallucination detection confidence (0.0 → 1.0) |

> **Note**: Every chat response is automatically scanned by the [Hallucination Detector](hallucination_detection.md). Display `safety_warning` to users when `is_flagged` is `true`.

---

## Safety Verification

### `POST /api/safety/verify`

Run the medical hallucination detector on any text. Use for standalone validation or frontend pre-checks.

**Request body** (`SafetyVerificationRequest`):
```json
{
  "response_text": "Give ORS and zinc for 14 days. Refer to PHC if no improvement.",
  "query": "diarrhea management"
}
```

**Response 200** (`SafetyVerificationResponse`):
```json
{
  "confidence_score": 0.95,
  "risk_level": "LOW",
  "is_flagged": false,
  "warning_message": null,
  "flagged_reasons": [],
  "grounded_terms": ["ors", "zinc", "diarrhea", "referral"]
}
```

Risk levels:

| Level | Confidence | Meaning |
|---|---|---|
| `LOW` | ≥ 0.80 | Response is well-grounded in NHM guidelines |
| `MEDIUM` | 0.60 – 0.79 | Review with PHC supervisor recommended |
| `HIGH` | < 0.60 | Potential hallucination or protocol violation |

See [docs/hallucination_detection.md](hallucination_detection.md) for the full algorithm.

---

## Reports & Insights

### `GET /api/broadcast/daily`

Generate a daily broadcast message and log notifications for all registered workers.

**Response 200**:
```json
{
  "message": "आज की उपस्थिति रिपोर्ट: 12/15 कार्यकर्ता उपस्थित हैं..."
}
```

---

### `GET /api/insights/weekly`

Generate a weekly insight report.

**Query params**:

| Param | Type | Default | Description |
|---|---|---|---|
| `language` | `string` | `"hi"` | Report language (`hi` = Hindi, `en` = English) |

**Response 200**:
```json
{
  "report": "..."
}
```

---

### `POST /api/insights/weekly`

Same as above, but language is provided in the request body (useful for JSON clients).

**Request body**:
```json
{ "language": "en" }
```

---

## Error Codes

| HTTP Code | Meaning |
|---|---|
| `400` | Bad request (e.g. duplicate `worker_code`) |
| `404` | Resource not found |
| `422` | Validation error – check request body schema |
| `500` | Internal server error |

All errors return a JSON body:
```json
{
  "detail": "Human-readable error message"
}
```
