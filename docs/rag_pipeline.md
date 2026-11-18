# Retrieval-Augmented Generation (RAG) Architecture & Setup

## Overview
Swasthya Sathi AI incorporates a grounded **Retrieval-Augmented Generation (RAG)** pipeline designed for rural healthcare operations in Bihar and national Indian public health programs.

When supervisors or health workers ask questions concerning immunization timing, maternal antenatal care (ANC), childhood illness triage (IMNCI), or ASHA/ANM field protocols, the AI Operations Agent automatically retrieves verified national guidelines to ensure medical accuracy and eliminate hallucinations.

---

## Architecture Flow

```text
Supervisor Prompt (Hindi / Hinglish / English)
         │
         ▼
Gemini 2.5 Flash Agent (enable_automatic_function_calling=True)
         │
         ├─► Attendance Query  ──► Database Tools (mark_attendance, etc.)
         │
         └─► Health / Protocol Query
                   │
                   ▼
       consult_medical_guidelines(topic)
                   │
                   ▼
     HealthKnowledgeBase (Vector / TF-IDF Retrieval)
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
Document Store         Synonym Expansion
(backend/knowledge/    (teeka ➔ vaccine,
 guidelines/*.md)       garbhwati ➔ ANC)
         │                   │
         └─────────┬─────────┘
                   ▼
     Top-K Ranked Protocol Chunks
                   │
                   ▼
  Grounded LLM Operational Response
  + MoHFW Protocol Citation & Medical Officer Advisory
```

---

## Curated Knowledge Base

Guidelines are stored in `backend/knowledge/guidelines/`:

1. **`immunization_schedule.md`**:
   - Universal Immunization Programme (UIP) schedule: Birth (BCG, Hep B, OPV 0), 6 weeks, 10 weeks, 14 weeks (Pentavalent, RVV, fIPV, PCV), 9 months (MR 1, JE 1, Vit A), 16-24 months, 5-6 years, and Td for pregnant women.
2. **`maternal_child_health.md`**:
   - 4 mandatory ANC checkups schedule, Pradhan Mantri Surakshit Matritva Abhiyan (PMSMA on the 9th), IFA tablets (180 days), Calcium, High-Risk Pregnancy (HRP) red flags, and JSY/JSSK entitlement benefits.
3. **`childhood_illness_imnci.md`**:
   - Diarrhea management: WHO ORS preparation (1 packet in 1 liter clean water) and 14-day Zinc supplementation.
   - Acute Respiratory Infections (ARI): Age-stratified fast breathing thresholds for pneumonia detection.
4. **`asha_anm_field_protocols.md`**:
   - Village Health, Sanitation and Nutrition Days (VHSND) monthly protocols, Home-Based Newborn Care (HBNC 6/7 visits), Drug depot rules, and 102 emergency ambulance escalation chains.

---

## API Endpoints

### Direct Knowledge Search
- **Endpoint**: `GET /api/knowledge/search?q={query}`
- **Example**:
  ```bash
  curl "http://localhost:8000/api/knowledge/search?q=pentavalent%20vaccine"
  ```
- **Response**:
  ```json
  {
    "query": "pentavalent vaccine",
    "results": [
      {
        "chunk_id": "immunization_schedule_2",
        "document_title": "National Immunization Schedule (NIS) — India & Bihar Health Guidelines",
        "section_title": "At 6 Weeks",
        "content": "2. Pentavalent 1 (DTP + Hepatitis B + Hib)...",
        "source_file": "immunization_schedule.md",
        "relevance_score": 0.42
      }
    ]
  }
  ```

---

## Testing the RAG Pipeline

Run the automated Pytest suite:
```bash
cd backend
python -m pytest tests/test_rag.py -v
```
