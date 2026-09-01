# Research and AI Methodology

Swasthya Sathi AI is structured as an applied AI operations assistant for rural healthcare attendance management. The project focuses on turning supervisor intent into safe, auditable attendance workflows.

## Research Objective

The core research question is:

```text
Can a natural-language AI assistant reduce friction in rural health workforce attendance monitoring while keeping operational actions grounded in real backend data?
```

The project explores this through:

- Natural-language supervision workflows.
- Structured attendance tools.
- Dashboard-based observability.
- Automated daily and weekly reporting.
- Human-readable operational recommendations.

## User Context

The target users are health supervisors who need to monitor field workers across rural health centres. These users may prefer Hindi, English, or mixed-language prompts, and they may need quick summaries rather than complex dashboard navigation.

Representative tasks include:

- Mark a worker present, absent, on leave, or half-day.
- Check a worker's attendance summary.
- Find low-attendance workers.
- Identify who has not marked attendance today.
- Generate a supervisor-ready daily broadcast.
- Generate a weekly attendance insight report.

## AI Agent Design

The project uses a tool-using agent pattern. The AI model receives a set of backend functions with clear responsibilities and can choose which function to invoke for attendance workflows.

This improves reliability because:

- Attendance actions are executed through application code.
- Worker names are resolved against database records.
- Attendance percentages come from stored records.
- Reports can be generated from live operational data.
- The agent can return an audit trail of actions taken.

## Tool Grounding

The agent is grounded through functions in `backend/agent.py`, including:

- `mark_attendance`
- `get_attendance_summary`
- `find_low_attendance_workers`
- `list_workers`
- `who_has_not_marked_today`
- `generate_daily_broadcast`
- `generate_weekly_insights`

These functions keep state-changing operations inside the backend and reduce the risk of fabricated operational output.

## Data Workflow

```text
User prompt
    |
    v
AI agent intent interpretation
    |
    v
Backend tool selection
    |
    v
Database read or write
    |
    v
Formatted operations response
```

## Evaluation Approach

The current repository supports lightweight automated checks through backend and frontend tests. A stronger research-ready evaluation can be built around:

- Intent coverage: percentage of common supervisor tasks handled correctly.
- Tool accuracy: whether the chosen backend tool matches the user request.
- Data grounding: whether responses match database records.
- Language quality: clarity of Hindi and English operational responses.
- Safety: refusal to invent missing worker names or attendance values.
- Latency: response time for chat, reports, and dashboard refreshes.

## Suggested Evaluation Dataset

A future dataset can include prompt categories such as:

| Category | Example |
| --- | --- |
| Attendance mutation | "Mark Kajal Kumari absent today" |
| Attendance lookup | "Show Sunny Kumar's monthly attendance" |
| Missing attendance | "Who has not marked attendance today?" |
| Low attendance | "Which workers need follow-up?" |
| Broadcast | "Prepare today's WhatsApp update" |
| General question | "What is the role of ASHA workers?" |

Expected outputs should include tool choice, database effect, and final user-facing response.

## Limitations

- The default local database is SQLite, which is convenient for demos but not ideal for production multi-user deployments.
- AI responses depend on external model providers and configured API keys.
- Real healthcare deployment would require authentication, authorization, privacy review, and stronger audit controls.
- Current tests cover basic API availability, but deeper behavioral tests are needed for agent workflows.

## Future Research Directions

- Compare tool-using responses against plain chatbot responses.
- Measure multilingual prompt handling across Hindi, English, and Hinglish.
- Add benchmark tests for worker-name fuzzy matching.
- Evaluate supervisor task completion time with and without the AI agent.
- Add human review workflows for sensitive attendance actions.
