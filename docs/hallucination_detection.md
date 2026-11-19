# 🛡️ Medical Hallucination Detection & Safety Verification

## Overview

Large Language Models (LLMs) used in clinical or public health contexts may occasionally generate unsupported claims, excessive medical guarantees, or inaccurate pharmaceutical dosages (hallucinations).

**Swasthya Sathi AI** implements a multi-tiered hallucination detection and response-safety framework to guard healthcare workers and patients against unverified advice.

---

## Architecture & Detection Pipeline

```
User Query + Generated Response (+ Optional Context/RAG Docs)
                          │
                          ▼
            [Medical Domain Classification]
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 [General Operations]             [Clinical Safety Checks]
  - Neutral baseline               - Lexical Grounding overlap
  - No disclaimer penalty          - Dangerous claim penalty scan
                                   - Clinical hedging & disclaimer check
                                            │
                                            ▼
                                [Confidence Scoring (0.0 - 1.0)]
                                            │
                                            ▼
                           [Risk Classification (LOW / MEDIUM / HIGH)]
                                            │
                                            ▼
                             [Advisory Warning & UI Banner]
```

### 1. Confidence Scoring Breakdown

The final confidence score is computed as:

$$\text{Confidence} = w_{\text{base}} + w_{\text{grounding}} - P_{\text{risk}} + M_{\text{disclaimer}}$$

Where:
- **Base Confidence**: Default prior for conversational clarity.
- **Context Grounding Overlap**: Evaluates content-word intersection with verified medical knowledge base entries (RAG context).
- **Dangerous Claim Penalty ($P_{\text{risk}}$)**: Heavily penalizes dangerous claims such as "100% cure", "instant miracle cure", "no side effects", or unverified dangerous dosing intervals.
- **Hedging & Disclaimer Modifier ($M_{\text{disclaimer}}$)**: Rewards professional caution ("consult a physician", "for informational purposes") and penalizes clinical advice lacking safety disclaimers.

---

## Risk Classifications & Thresholds

| Risk Level | Threshold Criteria | UI Behavior |
| :--- | :--- | :--- |
| **LOW** | Confidence $\ge 0.70$ and no dangerous claims detected | Response displayed normally without interruption. |
| **MEDIUM** | Confidence $< 0.70$ or missing required clinical hedging | Yellow warning banner alerting user to cross-check. |
| **HIGH** | Confidence $< 0.45$ or critical absolute claim detected | Prominent red safety banner warning against medical action. |

---

## Configuration via Environment Variables

All confidence thresholds are configurable without code modifications:

```bash
# Confidence below which a response is classified as HIGH risk
HALLUCINATION_HIGH_RISK_THRESHOLD=0.45

# Confidence below which a response is flagged (MEDIUM risk)
HALLUCINATION_FLAG_THRESHOLD=0.70

# Whether medical answers must include clinical disclaimers
HALLUCINATION_REQUIRE_DISCLAIMER=true
```

---

## API Reference

### Standalone Check Endpoint
`POST /api/safety/check-hallucination`

#### Request Body
```json
{
  "query": "Can herbal tea completely cure high blood pressure?",
  "response": "Drinking this tea 100% guarantees to cure your high blood pressure instantly.",
  "context": "Hypertension requires systematic monitoring and clinical consultation."
}
```

#### Response Body
```json
{
  "is_flagged": true,
  "confidence_score": 0.35,
  "risk_level": "HIGH",
  "flagged_reasons": [
    "Unsubstantiated or dangerous absolute claim detected: '100%\\s*(guarantee[s]?|cure[s]?|safe|effective)'",
    "Medical response is missing a standard clinical advisory or disclaimer."
  ],
  "warning_message": "⚠️ Critical Advisory: This response contains unverified medical claims or unsupported advice. Do not make health decisions based on this output. Consult a qualified physician.",
  "breakdown": {
    "is_medical_domain": true,
    "grounding_score": 0.35,
    "risk_penalty": 0.35,
    "has_disclaimer": false
  }
}
```

---

## Running Unit & Integration Tests

From the `backend/` directory:

```bash
pytest -v tests/test_hallucination_detector.py tests/test_safety_endpoint.py
```
