# Hallucination Detection & Medical Safety Assurance

> **Issue #14** – Detect and Flag Potential Hallucinated Medical Responses

---

## Overview

Swasthya Sathi AI is deployed for ASHA/ANM frontline health workers who rely on the AI agent for
clinical and operational guidance. If the model hallucinates a drug dosage, an unauthorized
procedure, or a protocol contradiction, the downstream risk to patients can be severe.

The **HallucinationDetector** engine intercepts every AI response before it reaches the user and
assigns a *confidence score* (0.0 → 1.0). Responses that fall below configurable thresholds are
flagged with a warning message so the worker knows to verify with the PHC Medical Officer.

---

## Architecture

```
User Query
    │
    ▼
chat_with_agent()          ← existing Gemini agent (tool-calling)
    │
    │  reply, actions
    ▼
HallucinationDetector.assess_response(reply, query)
    │
    │  HallucinationReport { confidence_score, risk_level, is_flagged, warning_message, … }
    ▼
ChatResponse
  ├─ reply           (original AI text)
  ├─ actions_taken   (tools the agent called)
  ├─ safety_warning  (human-readable warning or null)
  ├─ is_flagged      (bool)
  └─ confidence_score (float 0–1)
```

---

## Detection Layers

### 1. Unauthorized Prescription / Clinical Procedure Scan

Flags any response that instructs frontline workers to independently perform actions outside
their scope of practice under NHM:

| Trigger phrase | Reason flagged |
|---|---|
| `give iv`, `intravenous injection` | IV therapy requires a nurse or doctor |
| `prescribe antibiotics / amoxicillin / azithromycin` | Schedule H drugs – prescription only |
| `administer steroids`, `give dexamethasone` | Steroid administration by ASHA is prohibited |
| `perform incision` | Surgical procedure – referral mandatory |

### 2. Dangerous Protocol Contradiction Scan

Checks for statements that directly contradict NHM clinical SOPs:

| Contradiction detected | Protocol rule |
|---|---|
| "take IFA with tea/milk" | Iron supplements must NOT be consumed with tea or dairy |
| "stop zinc after 1 day" | Zinc must be given for the full **14-day** course in diarrhoea |
| "skip BCG at birth" | BCG is mandatory at birth or within 1 year |
| "no ANC needed" | Minimum 4 ANC visits are mandatory |

### 3. NHM Lexical Anchor Grounding

Positive evidence that the response is based on official NHM guidelines. Anchors are grouped
by clinical domain:

| Domain | Example terms |
|---|---|
| Immunization | `bcg`, `opv`, `pentavalent`, `rotavirus`, `national immunization schedule` |
| Maternal Health | `anc`, `ifa`, `preeclampsia`, `pmsma`, `calcium`, `albendazole` |
| Childhood Illness | `ors`, `zinc`, `diarrhea`, `imnci`, `exclusive breastfeeding` |
| Field Protocols | `vhsnd`, `hbnc`, `due list`, `phc`, `referral` |

Responses matching **≥ 3** anchor terms receive a confidence score of **0.95**.

### 4. Operational / Administrative Detection

Responses about attendance, roster management, broadcasts, or shift summaries are
**non-clinical** and automatically receive a HIGH confidence score (0.90). They are
never flagged for clinical safety reasons.

---

## Confidence Scoring Algorithm

```
score = f(flagged_reasons, grounded_terms, is_administrative)

if flagged_reasons:
    score = max(0.10,  0.45 − (0.15 × number_of_violations))

elif grounded_terms ≥ 3:
    score = 0.95

elif grounded_terms ≥ 1:
    score = 0.82

elif is_administrative:
    score = 0.90

else:  # unverifiable claims
    score = 0.55
    add_flag("Low guideline lexical grounding")

score = clamp(score, 0.0, 1.0)
```

---

## Risk Levels

| Risk Level | Confidence Range | `is_flagged` | Displayed Warning |
|---|---|---|---|
| **LOW** | ≥ 0.80 | `false` | None |
| **MEDIUM** | 0.60 – 0.79 | `true` | Review with PHC supervisor |
| **HIGH** | < 0.60 | `true` | Full clinical safety warning |

Thresholds are configurable via environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `HALLUCINATION_HIGH_THRESHOLD` | `0.80` | Minimum score for LOW risk |
| `HALLUCINATION_LOW_THRESHOLD` | `0.60` | Minimum score for MEDIUM risk |

---

## API Endpoint

### `POST /api/safety/verify`

Runs the hallucination detector on any AI-generated text. Useful for frontend validation,
integration testing, or external quality checks.

**Request body** (`SafetyVerificationRequest`):

```json
{
  "response_text": "Give ORS and zinc for 14 days. Refer to PHC if no improvement.",
  "query": "diarrhea management"
}
```

**Response** (`SafetyVerificationResponse`):

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

**Flagged example**:

```json
{
  "confidence_score": 0.30,
  "risk_level": "HIGH",
  "is_flagged": true,
  "warning_message": "⚠️ Clinical Safety Warning: This response contains medical claims …",
  "flagged_reasons": [
    "Unauthorized clinical procedure or prescription detected: 'prescribe antibiotics'"
  ],
  "grounded_terms": []
}
```

**HTTP Status Codes**:

| Code | Meaning |
|---|---|
| 200 | Detection ran successfully (inspect `is_flagged`) |
| 422 | Validation error – `response_text` field missing |

---

## Chat Endpoint Integration

The detector runs automatically on every `/api/chat` response. The `ChatResponse`
schema includes three new fields:

```json
{
  "reply": "…",
  "actions_taken": ["mark_attendance"],
  "safety_warning": null,
  "is_flagged": false,
  "confidence_score": 0.9
}
```

---

## Frontend Integration Guide

Display the safety warning **inline, below the AI message bubble** when `is_flagged` is `true`:

```jsx
{message.is_flagged && (
  <div className="safety-warning">
    <span className="warning-icon">⚠️</span>
    <p>{message.safety_warning}</p>
  </div>
)}
```

Colour-code by risk:

- 🟢 `LOW` → no badge
- 🟡 `MEDIUM` → amber notice banner
- 🔴 `HIGH` → red warning card, action disabled until acknowledged

---

## Running the Tests

```bash
cd backend
python -m pytest tests/test_hallucination_detector.py -v
```

---

## File Map

| File | Purpose |
|---|---|
| `backend/hallucination_detector.py` | Core engine – `HallucinationDetector`, `HallucinationReport`, `RiskLevel` |
| `backend/schemas.py` | Pydantic models: `SafetyVerificationRequest/Response`, extended `ChatResponse` |
| `backend/main.py` | Wires detector into `/api/chat`; exposes `POST /api/safety/verify` |
| `backend/tests/test_hallucination_detector.py` | 20 pytest tests covering all detection layers and the API endpoint |
| `docs/hallucination_detection.md` | This document |
