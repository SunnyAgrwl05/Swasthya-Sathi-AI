"""
Swasthya Sathi AI Agent
-----------------------
This is a real tool-using agent (not a wrapper chatbot). It is given a set of
Python functions as "tools". Gemini decides on its own, turn by turn, which
tool(s) to call, calls them, reads the result, and keeps going until it can
answer the supervisor in plain Hindi/English. This is what makes it an
"agent" for the Google Agent Builder track rather than a plain chat UI.
"""


# code written by Developer Sunny ❤️
import contextvars
import datetime
import os
import re
from difflib import get_close_matches

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

import models
from database import SessionLocal

load_dotenv()


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

FALLBACK_MODELS = [
    GEMINI_MODEL,
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]
# Remove duplicates while preserving order
FALLBACK_MODELS = list(dict.fromkeys([m for m in FALLBACK_MODELS if m]))

GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
]

GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def gemini_generate(prompt, system_instruction=None, tools=None):
    last_error = None

    for key in GEMINI_KEYS:
        for model_name in FALLBACK_MODELS:
            try:
                genai.configure(api_key=key)

                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction,
                    tools=tools,
                )

                return model.generate_content(prompt)

            except Exception as e:
                print(f"[Gemini Failed] {key[:10]}... ({model_name}) -> {e}")
                last_error = e
                continue

    raise Exception(f"All Gemini API Keys and models failed: {last_error}")

# _actions_context tracks actions executed by tools within a request context,
# isolating actions per async task / thread to prevent concurrent request race conditions.
_actions_context: contextvars.ContextVar[list[str]] = contextvars.ContextVar(
    "_actions_context", default=[]
)


def record_action(action: str):
    """Records an executed tool action in the current request context."""
    current = list(_actions_context.get())
    current.append(action)
    _actions_context.set(current)
# actions_taken is filled by tools during a single chat turn so the API
# response can show the user a small audit trail of what the agent did.
# Using ContextVar ensures thread-safety under concurrent async FastAPI workers.
_actions_var: contextvars.ContextVar[list[str]] = contextvars.ContextVar("_actions_var")
_actions_taken: list[str] = []


def record_action(msg: str) -> None:
    """Record an action taken during a tool invocation in a thread-safe context."""
    try:
        actions = _actions_var.get()
        actions.append(msg)
    except LookupError:
        _actions_taken.append(msg)


def get_actions() -> list[str]:
    """Retrieve actions recorded in the current request context."""
    try:
        return _actions_var.get()
    except LookupError:
        return _actions_taken


class AmbiguousWorkerError(Exception):
    """Raised when a worker name matches multiple records without enough context."""

    def __init__(self, name: str, candidates: list[models.HealthWorker]):
        self.name = name
        self.candidates = candidates
        options = ", ".join(
            f"{worker.name} ({worker.center or 'No Center'}, ID: {worker.id})"
            for worker in candidates
        )
        super().__init__(
            f"Multiple health workers found matching '{name}': {options}. "
            "Please specify the center name or worker ID to disambiguate."
        )


def _resolve_worker(db: Session, name: str, center: str | None = None):
    """Resolve a worker by ID, exact/composite name, or unambiguous fuzzy match.

    Duplicate names are never resolved by choosing the first database row.
    Callers receive AmbiguousWorkerError and can ask the supervisor to clarify.
    """
    workers = db.query(models.HealthWorker).all()
    if not workers:
        return None

    query = (name or "").strip()
    query_lower = query.lower()
    if not query_lower:
        return None

    # Support IDs entered as "12", "#12", or "id: 12".
    id_text = query_lower.removeprefix("#").removeprefix("id:").strip()
    if id_text.isdigit():
        worker = db.query(models.HealthWorker).filter_by(id=int(id_text)).first()
        if worker:
            return worker

    # Exact composite queries are the safest way to resolve duplicate names.
    composite_matches = [
        worker
        for worker in workers
        if query_lower in {
            f"{worker.name} {worker.center or ''}".strip().lower(),
            f"{worker.name} ({worker.center or ''})".strip().lower(),
            f"{worker.name} - {worker.center or ''}".strip().lower(),
        }
    ]
    if len(composite_matches) == 1:
        return composite_matches[0]
    if len(composite_matches) > 1:
        raise AmbiguousWorkerError(query, composite_matches)

    name_groups: dict[str, list[models.HealthWorker]] = {}
    for worker in workers:
        name_groups.setdefault(worker.name.strip().lower(), []).append(worker)

    candidates = name_groups.get(query_lower)
    if candidates is None:
        # A query may contain both a worker name and its center without punctuation.
        combined_matches = [
            worker
            for worker in workers
            if worker.name.strip().lower() in query_lower
            and any(
                token in query_lower
                for token in re.findall(r"[a-z0-9]+", (worker.center or "").lower())
                if len(token) > 2
            )
        ]
        if len(combined_matches) == 1:
            return combined_matches[0]
        if len(combined_matches) > 1:
            raise AmbiguousWorkerError(query, combined_matches)

        # Fuzzy matching is performed against unique names, then ambiguity is
        # checked against every worker sharing the selected name.
        matches = get_close_matches(query_lower, list(name_groups), n=1, cutoff=0.6)
        if not matches:
            return None
        candidates = name_groups[matches[0]]

    if len(candidates) == 1:
        return candidates[0]

    # If the caller supplies a center, use it only when it identifies one worker.
    if center:
        center_lower = center.strip().lower()
        center_matches = [
            worker
            for worker in candidates
            if center_lower and center_lower in (worker.center or "").lower()
        ]
        if len(center_matches) == 1:
            return center_matches[0]
        if center_matches:
            candidates = center_matches

    # Also accept center text included in the worker-name query.
    query_center_matches = [
        worker
        for worker in candidates
        if any(
            token in query_lower
            for token in re.findall(r"[a-z0-9]+", (worker.center or "").lower())
            if len(token) > 2
        )
    ]
    if len(query_center_matches) == 1:
        return query_center_matches[0]
    if query_center_matches:
        candidates = query_center_matches

    raise AmbiguousWorkerError(query, candidates)

def _parse_date(date_str: str | None) -> datetime.date:
    if not date_str or date_str.lower() == "today":
        return datetime.date.today()
    if date_str.lower() == "yesterday":
        return datetime.date.today() - datetime.timedelta(days=1)
    try:
        return datetime.date.fromisoformat(date_str)
    except ValueError:
        return datetime.date.today()


# ---------------------------------------------------------------------------
# Tools. Each function's name, args and docstring are read directly by Gemini
# to decide when/how to call it, so keep the docstrings clear.
# ---------------------------------------------------------------------------


def mark_attendance(
    worker_name: str,
    status: str,
    date_str: str = "today",
    note: str = "",
    center: str = "",
) -> str:
    """Marks attendance for a health worker on a given date.

    Args:
        worker_name: Full or partial name of the health worker.
        status: One of 'present', 'absent', 'half-day', 'leave'.
        date_str: Date in YYYY-MM-DD, or 'today' / 'yesterday'.
        note: Optional short remark, e.g. reason for absence.
        center: Optional center/sub-center name to disambiguate duplicate worker names.
    """
    db = SessionLocal()

    try:
        try:
            worker = _resolve_worker(db, worker_name)
        except AmbiguousWorkerError as e:
            return str(e)
            worker = _resolve_worker(db, worker_name, center=center or None)
        except AmbiguousWorkerError as error:
            return str(error)

        if not worker:
            return (
                f"No health worker found matching '{worker_name}'. "
                "Ask the supervisor to check the spelling or add the worker first."
            )

        status = status.lower().strip()

        if status not in {"present", "absent", "half-day", "leave"}:
            status = "present"

        the_date = _parse_date(date_str)

        existing = (
            db.query(models.AttendanceRecord)
            .filter_by(worker_id=worker.id, date=the_date)
            .first()
        )

        if existing:
            existing.status = status
            existing.note = note
        else:
            db.add(
                models.AttendanceRecord(
                    worker_id=worker.id,
                    date=the_date,
                    status=status,
                    note=note,
                    marked_by="agent",
                )
            )

        db.commit()

        record_action(
            f"Marked {worker.name} as {status} on {the_date.isoformat()}"
        )

        return f"""
✅ Attendance Updated

Worker:
{worker.name}

Role:
{getattr(worker, "role", "Not available")}

Centre:
{getattr(worker, "center", "Not available")}

Status:
{status.title()}

Date:
{the_date.isoformat()}

Result:
Attendance has been updated successfully.

Recommendation:
Ensure all worker details are complete for comprehensive reporting.
"""

    finally:
        db.close()


def get_attendance_summary(worker_name: str = "", days: int = 30, center: str = "") -> str:
    """Gets an attendance summary (present/absent/half-day/leave counts) for one worker
    or, if worker_name is empty, for every worker, over the last N days.

    Args:
        worker_name: Worker name, or leave blank for all workers.
        days: Lookback window in days (default 30).
        center: Optional center/PHC name to disambiguate workers sharing the same name.
        center: Optional center/sub-center name to disambiguate duplicate worker names.
    """
    db = SessionLocal()
    try:
        since = datetime.date.today() - datetime.timedelta(days=days)
        query = db.query(models.HealthWorker)
        if worker_name:
            try:
                w = _resolve_worker(db, worker_name)
            except AmbiguousWorkerError as e:
                return str(e)
                w = _resolve_worker(db, worker_name, center=center or None)
            except AmbiguousWorkerError as error:
                return str(error)
            if not w:
                return f"No health worker found matching '{worker_name}'."
            query = query.filter(models.HealthWorker.id == w.id)

        lines = []
        for w in query.all():
            records = [r for r in w.records if r.date >= since]
            present = sum(1 for r in records if r.status == "present")
            absent = sum(1 for r in records if r.status == "absent")
            half = sum(1 for r in records if r.status == "half-day")
            leave = sum(1 for r in records if r.status == "leave")
            total = len(records)
            pct = round((present / total) * 100, 1) if total else 0.0
            lines.append(
                f"{w.name} ({w.center or 'no center'}): {pct}% present "
                f"[present={present}, absent={absent}, half-day={half}, leave={leave}, days_logged={total}]"
            )
        if not lines:
            return "No workers or attendance records found yet."
        return "\n".join(lines)
    finally:
        db.close()


def find_low_attendance_workers(min_percent: float = 75.0, days: int = 30) -> str:
    """
    Returns a professional attendance analysis for workers
    whose attendance is below the configured threshold.
    """

    db = SessionLocal()

    try:
        since = datetime.date.today() - datetime.timedelta(days=days)

        flagged = []
        newly_onboarded = []

        for w in db.query(models.HealthWorker).all():

            records = [r for r in w.records if r.date >= since]

            if not records:
                newly_onboarded.append(w)
                continue

            present = sum(1 for r in records if r.status == "present")

            pct = round((present / len(records)) * 100, 1)

            if pct < min_percent:
                flagged.append(
                    {
                        "name": w.name,
                        "role": w.role,
                        "center": w.center,
                        "attendance": pct,
                    }
                )

        if not flagged:
            msg = (
                "📊 Attendance Analysis\n\n"
                f"All health workers have maintained attendance above {min_percent}% "
                f"during the last {days} days.\n\n"
                "✅ No follow-up required."
            )
            if newly_onboarded:
                msg += f"\n\n🌱 {len(newly_onboarded)} newly registered worker(s) are in onboarding (0 records logged, no penalty applied)."
            return msg

        flagged.sort(key=lambda x: x["attendance"])

        lines = []

        lines.append("📊 Attendance Analysis")
        lines.append("")
        lines.append("⚠ Workers Requiring Attention")
        lines.append("")

        for i, w in enumerate(flagged, start=1):
            lines.append(f"{i}. {w['name']}")
            lines.append(f"   • Attendance : {w['attendance']}%")
            lines.append(f"   • Role       : {w['role']}")
            lines.append(f"   • Centre     : {w['center']}")
            lines.append("")

        if newly_onboarded:
            lines.append("🌱 Newly Onboarded Workers (Exempt from Penalty)")
            lines.append("")
            for nw in newly_onboarded:
                lines.append(f"• {nw.name} ({nw.center}) — Onboarding in progress")
            lines.append("")

        lines.append("🔴 Risk Level")
        lines.append("High")
        lines.append("")

        lines.append("✅ Operational Recommendation")
        lines.append("")

        lines.append("• Contact low-attendance workers today.")
        lines.append("• Inform the PHC Supervisor.")
        lines.append("• Schedule counselling / follow-up meeting.")
        lines.append("• Review attendance again before weekly closure.")

        return "\n".join(lines)

    finally:
        db.close()


def list_workers() -> str:
    """Lists all registered health workers with their role and center."""
    db = SessionLocal()
    try:
        workers = db.query(models.HealthWorker).all()
        if not workers:
            return "No health workers registered yet."
        return "\n".join(f"{w.id}. {w.name} - {w.role} - {w.center or 'no center'}" for w in workers)
    finally:
        db.close()


def who_has_not_marked_today() -> str:
    """Find workers whose attendance has not been marked today."""

    db = SessionLocal()

    try:
        today = datetime.date.today()

        all_workers = db.query(models.HealthWorker).all()

        marked_ids = {
            r.worker_id
            for r in db.query(models.AttendanceRecord)
            .filter_by(date=today)
            .all()
        }

        missing_workers = [
            w for w in all_workers
            if w.id not in marked_ids
        ]

        if not missing_workers:
            return (
                "📢 Daily Operations Report\n\n"
                "✅ All registered health workers have marked attendance today.\n\n"
                "No pending action required."
            )

        lines = []

        lines.append("📢 Daily Operations Report")
        lines.append("")
        lines.append("📋 Pending Attendance")
        lines.append("")

        for worker in missing_workers:
            lines.append(f"• {worker.name}")
            lines.append(f"  {worker.role}")
            lines.append(f"  {worker.center}")
            lines.append("")

        lines.append("✅ Operational Recommendation")
        lines.append("")
        lines.append("• Contact all pending workers before end of shift.")
        lines.append("• Escalate unresolved cases to the PHC Supervisor.")
        lines.append("• Verify attendance before daily reporting closes.")

        return "\n".join(lines)

    finally:
        db.close()


def generate_daily_broadcast() -> str:
    """Composes a short, ready-to-share daily status update covering today's attendance
    and any workers who need follow-up. Use this when the supervisor asks for a
    'daily update', 'broadcast', 'WhatsApp message', or 'today ka summary bhejo'."""
    db = SessionLocal()
    try:
        today = datetime.date.today()
        workers = db.query(models.HealthWorker).all()
        total = len(workers)
        marked_today = [
            r for r in db.query(models.AttendanceRecord).filter_by(date=today).all()
        ]
        present_today = sum(1 for r in marked_today if r.status == "present")
        marked_ids = {r.worker_id for r in marked_today}
        missing_workers = [w for w in workers if w.id not in marked_ids]

        since = today - datetime.timedelta(days=30)
        flagged = []
        for w in workers:
            records = [r for r in w.records if r.date >= since]
            if not records:
                continue
            pct = round(sum(1 for r in records if r.status == "present") / len(records) * 100, 1)
            if pct < 75:
                flagged.append(f"{w.name} ({pct}%)")

        lines = [
            f"*Swasthya Sathi AI — Daily Update ({today.strftime('%d %b %Y')})*",
            f"Present today: {present_today}/{total}",
        ]

        if missing_workers:
            lines.append("")
            lines.append(f"📋 Pending Attendance ({len(missing_workers)} Workers)")
            lines.append("")

            for worker in missing_workers:
                lines.append(f"• {worker.name}")
                lines.append(f"  {worker.role}")
                lines.append(f"  {worker.center}")
                lines.append("")

        if flagged:
            lines.append("⚠ Workers Requiring Follow-up")
            lines.append("")

            for worker in workers:
                rec_count = len([r for r in worker.records if r.date >= since])
                if rec_count == 0:
                    continue

                pct = round(
                    sum(
                        1
                        for r in worker.records
                        if r.date >= since and r.status == "present"
                    )
                    / rec_count
                    * 100,
                    1,
                )

                if pct < 75:
                    lines.append(f"• {worker.name} ({pct}%)")

            for item in flagged:
                lines.append(f"• {item}")
            lines.append("")

        lines.append("✅ Operational Recommendation")
        lines.append("")
        lines.append("• Contact all pending workers before end of shift.")
        lines.append("• Escalate unresolved cases to the PHC Supervisor.")
        lines.append("• Verify attendance records before daily reporting closes.")

        return "\n".join(lines)

    finally:
        db.close()


def consult_medical_guidelines(topic: str) -> str:
    """Consults verified Indian public health protocols and guidelines for
    immunization schedules, maternal care (ANC), childhood illnesses (IMNCI),
    and ASHA/ANM field duties. Use this whenever the supervisor asks a medical,
    immunization, disease, or clinical protocol question.

    Args:
        topic: The disease, vaccine, pregnancy protocol, or public health topic.
    """
    from knowledge.rag_service import get_health_knowledge_base

    kb = get_health_knowledge_base()
    results = kb.search(topic, top_k=2)

    if not results:
        return (
            f"No specific national guideline found matching '{topic}'. "
            "Please advise the supervisor to consult the Primary Health Centre (PHC) Medical Officer."
        )

    record_action(f"Retrieved verified health guideline: {results[0]['section_title']}")

    formatted = []
    for r in results:
        formatted.append(
            f"📖 {r['document_title']} — {r['section_title']}\n"
            f"{r['content']}\n"
            f"(Source: {r['source_file']})"
        )

    return "\n\n---\n\n".join(formatted)


SYSTEM_INSTRUCTION = """
You are Swasthya Sathi AI.

You are an AI Operations Agent for Bihar Health Department.

You are NOT a chatbot.

Your responsibility is to monitor, analyse and manage attendance of ASHA Workers, ANMs and Anganwadi Workers across the Bihar PHC Network.

====================================================

YOUR CAPABILITIES

• Mark attendance
• Update attendance
• View attendance summaries
• Analyse attendance trends
• Detect low attendance
• Generate weekly insights
• Generate daily operational reports
• Identify workers requiring follow-up
• Consult verified public health, immunization, and maternal care guidelines
• Answer general knowledge questions when unrelated to attendance

====================================================

FOR ATTENDANCE TASKS

Always use the available tools.

Never invent attendance records.

Never invent attendance percentages.

Never invent worker names.

Never assume data.

If a worker cannot be found,
politely inform the supervisor.

====================================================

FOR MEDICAL & PUBLIC HEALTH QUESTIONS

Always use the consult_medical_guidelines tool.

Never invent vaccine schedules, drug doses, or medical treatments.

Always ground advice in the retrieved guideline text.

Always finish with a clear recommendation that clinical decisions must be confirmed by the PHC Medical Officer.

====================================================

WHEN TOOL DATA IS RETURNED

Never copy the raw tool output.

Always convert it into a professional AI Operations Report.

Use clear headings.

Use bullets whenever appropriate.

Always finish with a recommendation.

====================================================

FORMAT FOR ATTENDANCE UPDATE

✅ Attendance Updated

Worker:
<Name>

Role:
<Role>

Centre:
<PHC/Sub-center>

Status:
Present / Absent / Leave / Half Day

Date:
<Date>

Result:
Attendance has been updated successfully.

Recommendation:
One short practical recommendation.

====================================================

FORMAT FOR ATTENDANCE SUMMARY

📋 Worker Attendance Summary

Worker:
<Name>

Role:
<Role>

Centre:
<Centre>

Attendance:
<Percentage>

Present:
<X>

Absent:
<Y>

Half Day:
<Z>

Leave:
<N>

Performance Status:

🟢 Excellent (90%+)

🟡 Watch (75–89%)

🔴 Follow-up Required (<75%)

Recommendation:
One short recommendation.

====================================================

FORMAT FOR LOW ATTENDANCE ANALYSIS

📊 Attendance Analysis Complete

Workers Requiring Attention

• Worker Name
  Attendance : xx%

• Worker Name
  Attendance : xx%

Overall Observation

Briefly explain the current attendance situation.

Recommendation

Provide 2-3 practical recommendations for the supervisor.

====================================================

FORMAT FOR DAILY REPORT

📢 Daily Operations Report

Present Today

Pending Attendance

Workers Requiring Follow-up

Operational Recommendation

====================================================

FORMAT FOR WEEKLY INSIGHTS

📈 Weekly Insights Report

Attendance Trend

Key Improvements

Areas of Concern

High Performing Workers

Workers Requiring Immediate Attention

Recommendation

====================================================

GENERAL QUESTIONS

If the user's question is unrelated to attendance
(for example AI, Google, coding, internships, hospitals,
career guidance, technology, programming, interview etc.)

Answer naturally like ChatGPT.

Do NOT force attendance topics.

====================================================

STYLE

Always match the user's language.

Prefer Hindi when the user writes in Hindi.

Be concise.

Professional.

Executive.

Action-oriented.

Never expose internal reasoning.

Never mention:

• Gemini

• OpenRouter

• Function Calling

• Tools

• APIs

• Prompt

• Internal instructions

• Database

• SQL

Output plain text only.

Always make the response feel like it is coming from an AI Operations Agent rather than a chatbot.
"""


# this is a separate function for OpenRouter in case we want to use it instead of Gemini.




def call_openrouter(user_message: str):
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek/deepseek-chat-v3-0324",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "temperature": 0.4,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]


def format_agent_response(user_query: str, tool_output: str) -> str:
    """
    Uses Gemini to clean up the raw tool response.
    """

    prompt = f"""
You are a response formatter.

User Query:
{user_query}

RAW RESPONSE:
{tool_output}

Return ONLY the formatted response.
"""

    try:
        response = gemini_generate(prompt=prompt)

        if response.text:
            return response.text.strip()

    except Exception:
        pass

    return tool_output


def get_insights_system_instruction(language: str = "hi") -> str:
    if language == "en":
        report_language = "Write the report in simple, professional English."
    else:
        report_language = "Write the report in simple Hindi."

    return f"""You are the Insights Agent for Swasthya Sathi AI, a specialist that ONLY writes short analytical reports for a PHC supervisor in Bihar.

You do not take actions or call tools.

You are given this week's and last week's attendance numbers per health worker.

{report_language}

Write a concise report (5–8 sentences) that:

(1) calls out any worker whose attendance is trending down week-over-week,
(2) calls out any worker improving,
(3) gives one concrete, practical recommendation for the supervisor.

Be specific with numbers.

No preamble, no headers, just the report as flowing prose."""


def generate_weekly_insights(language: str = "hi") -> str:
    """Runs the dedicated Insights Agent over the last two weeks of attendance data
    and returns a written trend report.
    Args:
        language: "hi" or "en"
    """
    if language not in ("hi", "en"):
        language = "hi"
    if language == "en":
        lang_line = "Write in simple, professional English."
    else:
        lang_line = "Write in simple Hindi."
    db = SessionLocal()

    try:
        today = datetime.date.today()
        this_week_start = today - datetime.timedelta(days=7)
        last_week_start = today - datetime.timedelta(days=14)

        rows = []

        for w in db.query(models.HealthWorker).all():
            this_week = [
                r for r in w.records
                if this_week_start <= r.date <= today
            ]

            last_week = [
                r for r in w.records
                if last_week_start <= r.date < this_week_start
            ]

            def pct(records):
                if not records:
                    return None

                return round(
                    sum(1 for r in records if r.status == "present")
                    / len(records)
                    * 100,
                    1,
                )

            rows.append(
                {
                    "name": w.name,
                    "center": w.center,
                    "this_week_pct": pct(this_week),
                    "last_week_pct": pct(last_week),
                }
            )

        data_summary = "\n".join(
            f"{r['name']} ({r['center']}): last week {r['last_week_pct']}% -> this week {r['this_week_pct']}%"
            for r in rows
        )

        try:
            response = gemini_generate(
                prompt=f"""
You are an attendance analytics expert.

Analyze the following week-over-week attendance data.

Attendance data:
{data_summary}

Instructions:
- Return ONLY plain text.
- Do NOT use Markdown.
- Do NOT use **, #, ## or bullet points.
- {lang_line}
- Mention workers whose attendance improved.
- Mention workers whose attendance declined.
- Mention workers needing follow-up.
- End with one practical recommendation.
- Keep the report within 6-8 lines.
""",
                system_instruction=get_insights_system_instruction(language),
            )

            return response.text

        except Exception as e:
            print(f"[Insights Gemini Error] {e}")

            if OPENROUTER_API_KEY:
                try:
                    return call_openrouter(
                        f"""
You are an attendance analytics expert.

Analyze the following week-over-week attendance data.

Attendance data:
{data_summary}

Return ONLY plain text.
Do NOT use Markdown.
{lang_line}
"""
                    )
                except Exception as router_err:
                    print(f"[Insights OpenRouter Error] {router_err}")

            # Deterministic local summary fallback when external LLM APIs fail
            return (
                "📊 Weekly Attendance Performance Insights\n\n"
                "Summary Trends (Week-over-Week):\n"
                f"{data_summary or 'No active worker records found for the past 14 days.'}\n\n"
                "Operational Recommendation:\n"
                "• Supervisors should conduct weekly check-ins with at-risk health workers to address field challenges."
            )

    finally:
        db.close()


# ---------------------- TOOLS ----------------------

TOOLS = [
    mark_attendance,
    get_attendance_summary,
    find_low_attendance_workers,
    list_workers,
    who_has_not_marked_today,
    generate_daily_broadcast,
    generate_weekly_insights,
    consult_medical_guidelines,
]


def _dispatch_local_attendance_tool(user_message: str) -> tuple[str, list[str]] | None:
    """
    Directly dispatches attendance and workforce tools when Gemini is unavailable,
    ensuring local development environments execute database tools rather than
    behaving as a generic chatbot without tools.
    """
    msg = user_message.strip()
    msg_lower = msg.lower()

    # 1. Who has not marked attendance today / pending workers
    if (
        ("not marked" in msg_lower and "today" in msg_lower)
        or "who has not marked" in msg_lower
        or "pending attendance" in msg_lower
        or "attendance nahi laga" in msg_lower
        or "nahi laga" in msg_lower
        or "kis kis ka attendance" in msg_lower
        or "kiska attendance baaki" in msg_lower
        or ("unmarked" in msg_lower and "today" in msg_lower)
    ):
        raw = who_has_not_marked_today()
        _actions_taken.append("Executed who_has_not_marked_today tool")
        report = (
            "📢 *Daily Operations Report*\n\n"
            f"{raw}\n\n"
            "Operational Recommendation:\n"
            "• Contact all pending health workers before the end of the shift to complete daily roster compliance."
        )
        return report, list(_actions_taken)

    # 2. Low attendance / workers needing attention
    if (
        "sabse kam" in msg_lower
        or "sab se kam" in msg_lower
        or "low attendance" in msg_lower
        or "lowest attendance" in msg_lower
        or "kam attendance" in msg_lower
        or "poor attendance" in msg_lower
        or "at risk" in msg_lower
        or "below 75" in msg_lower
        or ("attendance" in msg_lower and ("kam" in msg_lower or "low" in msg_lower or "risk" in msg_lower or "attention" in msg_lower))
        or "who needs attention" in msg_lower
    ):
        raw = find_low_attendance_workers()
        _actions_taken.append("Executed find_low_attendance_workers tool")
        report = (
            "📊 *Attendance Analysis Complete*\n\n"
            f"{raw}\n\n"
            "Operational Recommendation:\n"
            "• Supervisors should conduct weekly check-ins with at-risk health workers to address field challenges."
        )
        return report, list(_actions_taken)

    _actions_context.set([])
    # 3. Mark / Record Attendance Mutation
    if "mark" in msg_lower or "present" in msg_lower or "absent" in msg_lower or "leave" in msg_lower:
        status = None
        for s in ("present", "absent", "leave", "half-day", "half day"):
            if s in msg_lower:
                status = "Half Day" if "half" in s else s.capitalize()
                break

        date_str = "yesterday" if ("kal" in msg_lower or "yesterday" in msg_lower) else "today"

        db = SessionLocal()
        try:
            workers = db.query(models.HealthWorker).all()
            matched_worker = None
            for w in workers:
                if w.name.lower() in msg_lower:
                    matched_worker = w
                    break

            if matched_worker and status:
                res = mark_attendance(matched_worker.name, status, date_str)
                report = (
                    "✅ *Attendance Updated*\n\n"
                    f"Worker:\n{matched_worker.name}\n\n"
                    f"Role:\n{matched_worker.role}\n\n"
                    f"Centre:\n{matched_worker.center}\n\n"
                    f"Status:\n{status}\n\n"
                    f"Date:\n{date_str.capitalize()}\n\n"
                    f"Result:\n{res}\n\n"
                    "Recommendation:\nVerify that all field duties for the shift are logged appropriately."
                )
                return report, list(_actions_taken)
        finally:
            db.close()

    # 4. Daily Broadcast
    if (
        "daily broadcast" in msg_lower
        or "broadcast message" in msg_lower
        or "whatsapp broadcast" in msg_lower
        or "whatsapp update" in msg_lower
        or "daily update" in msg_lower
        or "aaj ka broadcast" in msg_lower
        or ("broadcast" in msg_lower and "attendance" in msg_lower)
    ):
        raw = generate_daily_broadcast()
        _actions_taken.append("Executed generate_daily_broadcast tool")
        return raw, list(_actions_taken)

    # 5. Weekly Insights
    if (
        "weekly insight" in msg_lower
        or "weekly insights" in msg_lower
        or "weekly trend" in msg_lower
        or "weekly performance" in msg_lower
        or "hafta ka report" in msg_lower
        or "pichhle hafte" in msg_lower
        or "week over week" in msg_lower
    ):
        raw = generate_weekly_insights()
        _actions_taken.append("Executed generate_weekly_insights tool")
        return raw, list(_actions_taken)

    # 6. List all workers
    if (
        "list workers" in msg_lower
        or "list of workers" in msg_lower
        or "all workers" in msg_lower
        or "show workers" in msg_lower
        or "saare workers" in msg_lower
        or "registered workers" in msg_lower
        or ("workers" in msg_lower and ("list" in msg_lower or "dikhao" in msg_lower or "show" in msg_lower))
    ):
        raw = list_workers()
        _actions_taken.append("Executed list_workers tool")
        return raw, list(_actions_taken)

    # 7. Attendance summary for specific worker or overall
    if (
        "attendance summary" in msg_lower
        or "summary" in msg_lower
        or "attendance record" in msg_lower
        or "attendance dikhao" in msg_lower
        or "attendance" in msg_lower
    ):
        db = SessionLocal()
        try:
            workers = db.query(models.HealthWorker).all()
            matched_worker = None
            for w in workers:
                if w.name.lower() in msg_lower:
                    matched_worker = w
                    break

            raw = get_attendance_summary(matched_worker.name if matched_worker else None)
            _actions_taken.append("Executed get_attendance_summary tool")
            return raw, list(_actions_taken)
        finally:
            db.close()

    return None


# ---------------------- CHAT AGENT ----------------------

                executed_actions = list(_actions_context.get())

                # If Gemini returned no text but a tool executed,
                # show executed actions.
                if not tool_output and executed_actions:
                    tool_output = "\n".join(executed_actions)
def classify_attendance_intent(user_message: str) -> tuple[str | None, dict]:
    """
    Classify user message into an attendance operational intent with extracted parameters.
    Handles Hindi, Hinglish, and English queries reliably.
    """
    msg = user_message.lower().strip()

    # 1. Low attendance queries
    if any(k in msg for k in [
        "kam attendance", "lowest attendance", "sabse kam", "low attendance",
        "attendance drop", "defaulter", "bad attendance", "poor attendance"
    ]):
        days = 30
        days_match = re.search(r"(\d+)\s*(?:days?|din)", msg)
        if days_match:
            days = int(days_match.group(1))
        elif "week" in msg or "hafta" in msg:
            days = 7
        return "LOW_ATTENDANCE", {"days": days}

    # 2. Who has not marked today / pending attendance
    if any(k in msg for k in [
        "nahi mark", "not marked", "pending attendance", "baki hai",
        "nahi lagayi", "kisne nahi", "kiska baki", "unmarked"
    ]):
        return "WHO_NOT_MARKED", {}

    # 3. Daily broadcast / WhatsApp status
    if any(k in msg for k in [
        "broadcast", "whatsapp", "daily update", "today ka summary",
        "aaj ka update", "daily report", "status update"
    ]):
        return "DAILY_BROADCAST", {}

    # 4. Weekly trend insights
    if any(k in msg for k in ["weekly insights", "weekly report", "hafta ka report", "trend report", "hafta report"]):
        lang = "en" if "english" in msg else "hi"
        return "WEEKLY_INSIGHTS", {"language": lang}

    # 5. List all workers
    if ("list" in msg and "worker" in msg) or "all workers" in msg or "sab workers" in msg or "roster" in msg or "workers list" in msg:
        return "LIST_WORKERS", {}

    # 6. Mark attendance
    if any(k in msg for k in ["mark", "lagao", "karo", "present", "absent", "leave", "half-day"]):
        if any(status_word in msg for status_word in ["present", "absent", "leave", "half-day", "chhutti", "half day"]):
            status = "present"
            if "absent" in msg:
                status = "absent"
            elif "leave" in msg or "chhutti" in msg:
                status = "leave"
            elif "half" in msg:
                status = "half-day"

            date_str = "today"
            if "yesterday" in msg or ("kal" in msg and "beeta" in msg):
                date_str = "yesterday"

            name_match = re.search(r"(?:mark|lagao|karo)?\s*([a-zA-Z\u0900-\u097F\s]{2,25}?)\s*(?:ko|ki)?\s*(?:aaj|kal|today|yesterday)?\s*(?:ko)?\s*(?:present|absent|leave|half|chhutti)", user_message, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else ""
            name = re.sub(r"^(?:please|kripya|mark|lagao|karo)\s+", "", name, flags=re.IGNORECASE).strip()
            if name:
                return "MARK_ATTENDANCE", {"worker_name": name, "status": status, "date_str": date_str}

    # 7. Attendance summary for specific worker
    if any(k in msg for k in ["summary", "record", "history", "details"]):
        name_match = re.search(r"([a-zA-Z\u0900-\u097F\s]{2,25}?)\s*(?:ka|ki|ke)?\s*(?:attendance)?\s*(?:summary|record|report)", user_message, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else ""
        name = re.sub(r"^(?:show|dikhao|get|batao)\s+", "", name, flags=re.IGNORECASE).strip()
        if name:
            return "ATTENDANCE_SUMMARY", {"worker_name": name, "days": 30}

    return None, {}


def execute_attendance_intent(intent: str, params: dict) -> tuple[str, list[str]]:
    """
    Directly execute the corresponding attendance tool based on classified intent.
    Provides bulletproof reliability when LLM tool dispatching fails or runs offline.
    """

    actions: list[str] = []
    _actions_var.set(actions)
    global _actions_taken
    _actions_taken = actions

    if intent == "LOW_ATTENDANCE":
        days = params.get("days", 30)
        res = find_low_attendance_workers(min_percent=75.0, days=days)
        actions = [f"Analyzed low attendance workers for the last {days} days"]
        return res, actions

    elif intent == "WHO_NOT_MARKED":
        res = who_has_not_marked_today()
        actions = ["Checked pending attendance records for today"]
        return res, actions

    elif intent == "DAILY_BROADCAST":
        res = generate_daily_broadcast()
        actions = ["Generated daily operational broadcast update"]
        return res, actions

    elif intent == "WEEKLY_INSIGHTS":
        lang = params.get("language", "hi")
        res = generate_weekly_insights(language=lang)
        actions = [f"Generated weekly trend insights ({lang})"]
        return res, actions

    elif intent == "LIST_WORKERS":
        res = list_workers()
        actions = ["Retrieved registered health workers roster"]
        return res, actions

    elif intent == "MARK_ATTENDANCE":
        name = params.get("worker_name", "")
        status = params.get("status", "present")
        date_str = params.get("date_str", "today")
        res = mark_attendance(worker_name=name, status=status, date_str=date_str)
        return res, list(_actions_taken)

    elif intent == "ATTENDANCE_SUMMARY":
        name = params.get("worker_name", "")
        days = params.get("days", 30)
        res = get_attendance_summary(worker_name=name, days=days)
        actions = [f"Retrieved attendance summary for {name or 'all workers'}"]
        return res, actions

    return "No matching operations tool found.", []

                print("\n====================================")
                print("USING KEY:", key[:10] + "...")
                print("USER:", user_message)
                print("RESPONSE:")
                print(tool_output)
                print("ACTIONS:", executed_actions)
                print("====================================\n")

                return tool_output, executed_actions

# ---------------------- CHAT AGENT ----------------------

def chat_with_agent(user_message: str) -> tuple[str, list[str]]:
    """
    Main AI Agent runtime.
    Features:
    - Multi-key and multi-model failover (Gemini 2.0 Flash / 1.5 Flash / 1.5 Pro)
    - Automatic function calling for dynamic conversations
    - Bilingual intent detection safeguard (prevents LLM translation fallback)
    - Deterministic offline execution if API is unreachable
    """
    clear_recorded_actions()

    intent, params = classify_attendance_intent(user_message)

    # 1. If Gemini keys are available, attempt tool-using agent
    if GEMINI_KEYS:
        for key in GEMINI_KEYS:
            for model_name in FALLBACK_MODELS:
                try:
                    genai.configure(api_key=key)

                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=TOOLS,
                    )

                    chat = model.start_chat(
                        enable_automatic_function_calling=True
                    )

                    response = chat.send_message(user_message)
                    tool_output = ""

                    try:
                        if response.text:
                            tool_output = response.text.strip()
                    except Exception:
                        tool_output = ""

                    # Safeguard: If Gemini returned text WITHOUT executing tools,
                    # but the user query was an attendance intent, execute the tool directly.
                    if not _actions_taken and intent:
                        print(f"[Safeguard Triggered] Gemini did not call tool for intent {intent}. Executing directly.")
                        return execute_attendance_intent(intent, params)

                    # If tools were executed but no text returned, show actions
                    if not tool_output and _actions_taken:
                        tool_output = "\n".join(_actions_taken)

                    if tool_output:
                        return tool_output, list(_actions_taken)

                except Exception as e:
                    print(f"[Gemini Failed] {key[:10]}... ({model_name}) -> {e}")
                    continue

    # 2. Offline / local fallback: If Gemini keys failed or are not configured,
    # and the user asked an attendance query, execute the tool directly!
    if intent:
        print(f"[Offline Intent Fallback] Executing {intent} directly.")
        return execute_attendance_intent(intent, params)

    # 3. General questions fallback via OpenRouter if configured
    if OPENROUTER_API_KEY:
        try:
            raw_reply = call_openrouter(user_message)
            return raw_reply, []
        except Exception as e:
            print(f"[OpenRouter Error] {e}")

        except Exception as e:
            print(f"[Gemini Error] {e}")

        # Local fallback intent parser and tool execution when API keys are missing or API fails locally
        msg_lower = user_message.lower()
        try:
            if "who" in msg_lower and ("mark" in msg_lower or "today" in msg_lower or "pending" in msg_lower):
                res = who_has_not_marked_today()
                return res, ["Executed who_has_not_marked_today tool"]
            elif "low" in msg_lower or "attention" in msg_lower or "risk" in msg_lower or "below" in msg_lower:
                res = find_low_attendance_workers()
                return res, ["Executed find_low_attendance_workers tool"]
            elif "broadcast" in msg_lower or "whatsapp" in msg_lower or "update" in msg_lower:
                res = generate_daily_broadcast()
                return res, ["Executed generate_daily_broadcast tool"]
            elif "insight" in msg_lower or "trend" in msg_lower or "weekly" in msg_lower:
                res = generate_weekly_insights()
                return res, ["Executed generate_weekly_insights tool"]
            elif "list" in msg_lower or "worker" in msg_lower:
                res = list_workers()
                return res, ["Executed list_workers tool"]
            elif "mark" in msg_lower or "attendance" in msg_lower or "summary" in msg_lower:
                res = get_attendance_summary()
                return res, ["Executed get_attendance_summary tool"]
        except Exception as fallback_err:
            print(f"[Local Tool Fallback Error] {fallback_err}")

    # Fallback to local database-backed tool dispatcher for attendance and roster tasks
    local_tool_res = _dispatch_local_attendance_tool(user_message)
    if local_tool_res is not None:
        return local_tool_res

    try:
        raw_reply = call_openrouter(user_message)
        return raw_reply, []

        except Exception as e:
            print(f"[OpenRouter Error] {e}")

            return (
                """❌ AI Operations Agent is currently unavailable.

Please try again after a few seconds.""",
                [],
            )
    finally:
        _actions_taken_var.reset(token)


def __getattr__(name: str):
    """Provides backward compatibility for direct access to `_actions_taken`."""
    if name == "_actions_taken":
        return list(_actions_context.get())
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

