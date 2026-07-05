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
import os
import datetime
import requests
from difflib import get_close_matches

from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import Session

from database import SessionLocal
import models
 
load_dotenv()


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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
        try:
            genai.configure(api_key=key)

            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=system_instruction,
                tools=tools,
            )

            return model.generate_content(prompt)

        except Exception as e:
            print(f"[Gemini Failed] {key[:10]}... -> {e}")
            last_error = e
            continue

    raise Exception(f"All Gemini API Keys failed: {last_error}")

# actions_taken is filled by tools during a single chat turn so the API
# response can show the user a small audit trail of what the agent did.
_actions_taken: list[str] = []


def _resolve_worker(db: Session, name: str):
    """Fuzzy-match a spoken/typed worker name to a DB row."""
    workers = db.query(models.HealthWorker).all()
    if not workers:
        return None
    names = {w.name.lower(): w for w in workers}
    if name.lower() in names:
        return names[name.lower()]
    match = get_close_matches(name.lower(), names.keys(), n=1, cutoff=0.6)
    return names[match[0]] if match else None


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


def mark_attendance(worker_name: str, status: str, date_str: str = "today", note: str = "") -> str:
    """Marks attendance for a health worker on a given date.

    Args:
        worker_name: Full or partial name of the health worker.
        status: One of 'present', 'absent', 'half-day', 'leave'.
        date_str: Date in YYYY-MM-DD, or 'today' / 'yesterday'.
        note: Optional short remark, e.g. reason for absence.
    """
    db = SessionLocal()

    try:
        worker = _resolve_worker(db, worker_name)

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

        _actions_taken.append(
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


def get_attendance_summary(worker_name: str = "", days: int = 30) -> str:
    """Gets an attendance summary (present/absent/half-day/leave counts) for one worker
    or, if worker_name is empty, for every worker, over the last N days.

    Args:
        worker_name: Worker name, or leave blank for all workers.
        days: Lookback window in days (default 30).
    """
    db = SessionLocal()
    try:
        since = datetime.date.today() - datetime.timedelta(days=days)
        query = db.query(models.HealthWorker)
        if worker_name:
            w = _resolve_worker(db, worker_name)
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

        for w in db.query(models.HealthWorker).all():

            records = [r for r in w.records if r.date >= since]

            if not records:
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
            return (
                "📊 Attendance Analysis\n\n"
                f"All health workers have maintained attendance above {min_percent}% "
                f"during the last {days} days.\n\n"
                "✅ No follow-up required."
            )

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
        missing = [w.name for w in workers if w.id not in {r.worker_id for r in marked_today}]

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

        if missing:
            lines.append("")
            lines.append(f"📋 Pending Attendance ({len(missing)} Workers)")
            lines.append("")

            for worker in workers:
                if worker.name in missing:
                    lines.append(f"• {worker.name}")
                    lines.append(f"  {worker.role}")
                    lines.append(f"  {worker.center}")
                    lines.append("")

        if flagged:
            lines.append("⚠ Workers Requiring Follow-up")
            lines.append("")

            for worker in workers:
                pct = round(
                    sum(
                        1
                        for r in worker.records
                        if r.date >= since and r.status == "present"
                    )
                    / max(
                        1,
                        len([r for r in worker.records if r.date >= since]),
                    )
                    * 100,
                    1,
                )

                if pct < 75:
                    lines.append(f"• {worker.name} ({pct}%)")

            lines.append("")

        lines.append("✅ Operational Recommendation")
        lines.append("")
        lines.append("• Contact all pending workers before end of shift.")
        lines.append("• Escalate unresolved cases to the PHC Supervisor.")
        lines.append("• Verify attendance records before daily reporting closes.")

        return "\n".join(lines)

    finally:
        db.close()

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


INSIGHTS_SYSTEM_INSTRUCTION = """You are the Insights Agent for Swasthya Sathi AI, a
specialist that ONLY writes short analytical reports for a PHC supervisor in Bihar.
You do not take actions or call tools. You are given this week's and last week's
attendance numbers per health worker. Write a concise report (5-8 sentences, Hinglish
or English matching context) that: (1) calls out any worker whose attendance is
trending down week-over-week, (2) calls out any worker improving, (3) gives one
concrete, practical recommendation for the supervisor. Be specific with numbers.
No preamble, no headers, just the report as flowing prose."""


def generate_weekly_insights() -> str:
    """Runs the dedicated Insights Agent over the last two weeks of attendance data
    and returns a written trend report."""

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
- Write in simple Hindi.
- Mention workers whose attendance improved.
- Mention workers whose attendance declined.
- Mention workers needing follow-up.
- End with one practical recommendation.
- Keep the report within 6-8 lines.
""",
                system_instruction=INSIGHTS_SYSTEM_INSTRUCTION,
            )

            return response.text

        except Exception as e:
            print(f"[Insights Gemini Error] {e}")

            return call_openrouter(
                f"""
You are an attendance analytics expert.

Analyze the following week-over-week attendance data.

Attendance data:
{data_summary}

Return ONLY plain text.
Do NOT use Markdown.
Write in simple Hindi.
"""
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
]


# ---------------------- CHAT AGENT ----------------------

def chat_with_agent(user_message: str) -> tuple[str, list[str]]:
    """
    Main AI Agent runtime.
    """

    global _actions_taken
    _actions_taken = []

    try:
        last_error = None

        for key in GEMINI_KEYS:
            try:
                genai.configure(api_key=key)

                model = genai.GenerativeModel(
                    model_name=GEMINI_MODEL,
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

                # If Gemini returned no text but a tool executed,
                # show executed actions.
                if not tool_output and _actions_taken:
                    tool_output = "\n".join(_actions_taken)

                # If nothing came back, try next key.
                elif not tool_output:
                    raise Exception("Gemini returned empty response.")

                print("\n====================================")
                print("USING KEY:", key[:10] + "...")
                print("USER:", user_message)
                print("RESPONSE:")
                print(tool_output)
                print("ACTIONS:", _actions_taken)
                print("====================================\n")

                return tool_output, list(_actions_taken)

            except Exception as e:
                print(f"[Gemini Failed] {key[:10]}... -> {e}")
                last_error = e
                continue

        raise Exception(f"All Gemini API Keys failed: {last_error}")

    except Exception as e:
        print(f"[Gemini Error] {e}")

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

