#!/usr/bin/env python3
"""
AI Evaluation Benchmark Pipeline for Swasthya Sathi AI
-------------------------------------------------------
Executes quantitative quality evaluations across 10 operational and medical categories.
Outputs structured JSON and CSV reports with accuracy, grounding, safety, and latency metrics.

Usage:
    python evaluation/evaluate.py --mode mock
    python evaluation/evaluate.py --mode live --limit 5
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

# Add backend directory to path so tools and agents can be imported
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from metrics import (
    compute_bilingual_alignment,
    compute_composite_quality_score,
    compute_entity_coverage,
    compute_safety_score,
    compute_tool_accuracy,
)


def _mock_agent_response(item: dict) -> tuple[str, list[str]]:
    """
    Deterministic mock response generator for CI/CD and offline benchmarking.
    Simulates operational backend tool execution.
    """
    category = item.get("category", "")
    query = item.get("query", "")

    if category == "attendance_mutation":
        name = "Sunny Kumar" if "sunny" in query.lower() else "Kajal Kumari" if "kajal" in query.lower() else "Neha Kumari"
        status = "Present" if "present" in query.lower() else "Absent" if "absent" in query.lower() else "Leave"
        reply = (
            f"✅ Attendance Updated\n\n"
            f"Worker:\n{name}\n\n"
            f"Role:\nASHA Worker\n\n"
            f"Centre:\nPHC Patna\n\n"
            f"Status:\n{status}\n\n"
            f"Date:\n2026-11-16\n\n"
            f"Result:\nAttendance has been updated successfully.\n\n"
            f"Recommendation:\nEnsure all worker details are complete for comprehensive reporting."
        )
        return reply, ["mark_attendance"]

    elif category == "attendance_summary":
        reply = (
            "📋 Worker Attendance Summary\n\n"
            "Kajal Kumari (PHC Patna): 95.0% present [present=28, absent=1, half-day=1, leave=0, days_logged=30]\n"
            "Sunny Kumar (PHC Bakhtiyarpur): 88.0% present [present=26, absent=2, half-day=1, leave=1, days_logged=30]\n\n"
            "Performance Status:\n🟢 Excellent (90%+)\n\n"
            "Recommendation:\nMaintain regular reporting."
        )
        return reply, ["get_attendance_summary"]

    elif category == "low_attendance_flagging":
        reply = (
            "📊 Attendance Analysis Complete\n\n"
            "Workers Requiring Attention\n\n"
            "• Neha Kumari\n   Attendance : 58.0%\n   Role       : Anganwadi Worker\n   Centre     : Sub-center Fatuha\n\n"
            "• Aman Raj\n   Attendance : 65.0%\n   Role       : ANM\n   Centre     : PHC Patna\n\n"
            "Recommendation:\n"
            "• Contact low-attendance workers today.\n"
            "• Inform the PHC Supervisor."
        )
        return reply, ["find_low_attendance_workers"]

    elif category == "missing_attendance_detection":
        reply = (
            "📢 Daily Operations Report\n\n"
            "📋 Pending Attendance\n\n"
            "• Neha Kumari\n  Anganwadi Worker\n  Sub-center Fatuha\n\n"
            "Operational Recommendation\n"
            "• Contact all pending workers before end of shift."
        )
        return reply, ["who_has_not_marked_today"]

    elif category == "worker_listing":
        reply = (
            "1. Kajal Kumari - ASHA Worker - PHC Patna\n"
            "2. Sunny Kumar - ANM - PHC Bakhtiyarpur\n"
            "3. Neha Kumari - Anganwadi Worker - Sub-center Fatuha"
        )
        return reply, ["list_workers"]

    elif category == "daily_broadcast":
        reply = (
            "*Swasthya Sathi AI — Daily Update (16 Nov 2026)*\n"
            "Present today: 4/5\n\n"
            "📋 Pending Attendance (1 Workers)\n"
            "• Neha Kumari (Anganwadi Worker - Sub-center Fatuha)\n\n"
            "Operational Recommendation:\n"
            "• Contact all pending workers before shift ends."
        )
        return reply, ["generate_daily_broadcast"]

    elif category == "weekly_insights":
        reply = (
            "Attendance trend over the past week shows positive progress. "
            "Kajal Kumari improved attendance from 85% to 95%. "
            "Neha Kumari remains in the watch list with 58% attendance. "
            "Supervisor should schedule a follow-up review before weekend closure."
        )
        return reply, ["generate_weekly_insights"]

    elif category in ("medical_immunization", "maternal_anc", "childhood_imnci", "asha_anm_field"):
        q_lower = query.lower()
        if "5 rogo" in q_lower or "5 diseases" in q_lower or ("pentavalent" in q_lower and "5" in q_lower):
            reply = (
                "Pentavalent vaccine protects against 5 life-threatening childhood diseases:\n"
                "1. Diphtheria\n"
                "2. Pertussis (Whooping Cough)\n"
                "3. Tetanus\n"
                "4. Hepatitis B\n"
                "5. Hib (Haemophilus influenzae type b)\n\n"
                "Schedule: Given at 6, 10, and 14 weeks as 0.5 ml intramuscular injection (anterolateral mid-thigh)."
            )
        elif "6 weeks" in q_lower or "6 week" in q_lower:
            reply = (
                "At 6 weeks of age, infants receive:\n"
                "• Pentavalent 1 (DTP + Hepatitis B + Hib): 0.5 ml IM.\n"
                "• OPV 1: 2 drops oral.\n"
                "• Rotavirus Vaccine (RVV 1): 5 drops oral.\n"
                "• Fractional IPV 1: 0.1 ml ID.\n"
                "• PCV 1: 0.5 ml IM.\n\n"
                "Recommendation: Check the village Due List on VHSND day. Consult Medical Officer for adverse events."
            )
        elif "janam" in q_lower or "birth" in q_lower:
            reply = (
                "Under the National Immunization Schedule, at-birth vaccines are:\n"
                "1. BCG: 0.05 ml, Intradermal (left arm).\n"
                "2. Hepatitis B (Birth Dose): 0.5 ml IM (mid-thigh within 24 hours).\n"
                "3. OPV 0: 2 drops orally.\n\n"
                "Recommendation: Ensure all hospital deliveries receive birth doses before discharge. Consult PHC Medical Officer."
            )
        elif "preeclampsia" in q_lower or "swelling" in q_lower:
            reply = (
                "Warning signs of Preeclampsia during pregnancy include:\n"
                "• High blood pressure (Systolic >= 140 or Diastolic >= 90 mmHg)\n"
                "• Severe swelling (edema) in face, hands, or sudden weight gain\n"
                "• Persistent severe headache and blurred vision\n"
                "• Epigastric pain\n\n"
                "Action: Immediate referral to FRU/District Hospital; do not delay."
            )
        elif "ifa" in q_lower or "iron" in q_lower or "folic" in q_lower:
            reply = (
                "Recommended IFA Protocol during pregnancy:\n"
                "• 180 tablets of Iron and Folic Acid (IFA) starting from the second trimester (14th week).\n"
                "• Dose: 1 tablet daily (containing 100 mg elemental Iron and 500 mcg Folic Acid).\n"
                "• Counseling: Take after meals; avoid tea or milk when taking tablets."
            )
        elif "anc" in q_lower or "garbhwati" in q_lower:
            reply = (
                "As per NHM guidelines, all pregnant women must receive at least 4 mandatory ANC visits:\n"
                "1. 1st visit in 1st trimester (before 12 weeks).\n"
                "2. 2nd visit between 14-26 weeks.\n"
                "3. 3rd visit between 28-34 weeks.\n"
                "4. 4th visit between 36 weeks and term.\n\n"
                "Key activities: BP measurement, abdominal examination, hemoglobin check, 2 doses of Td vaccine, and 180 IFA tablets."
            )
        elif "zinc" in q_lower:
            reply = (
                "Zinc supplementation protocol for childhood diarrhea:\n"
                "• Duration: 14 days of Zinc treatment without stopping, even if diarrhea stops early.\n"
                "• Dosage: 20 mg elemental Zinc daily for children 6 months and older (10 mg for infants 2-6 months).\n"
                "• Zinc helps regenerate intestinal mucosa and prevents subsequent episodes."
            )
        elif "ors" in q_lower or "dast" in q_lower:
            reply = (
                "For diarrhea management in children:\n"
                "1. Prepare ORS by dissolving 1 packet in exactly 1 liter of clean water.\n"
                "2. Mix thoroughly until dissolved. Use within 24 hours.\n"
                "3. Give Zinc for 14 days. If dehydration signs worsen, refer immediately to PHC."
            )
        elif "pneumonia" in q_lower or "saans" in q_lower:
            reply = (
                "Under IMNCI guidelines, pneumonia is identified by fast breathing and chest indrawing:\n"
                "• Age 2 to 11 months: Fast breathing is 50 breaths per minute or more.\n"
                "• Age 12 to 59 months: Fast breathing is 40 breaths per minute or more.\n"
                "Action: Count respiratory rate for a full 60 seconds when child is calm. Refer severe cases immediately."
            )
        elif "hbnc" in q_lower or "home delivery" in q_lower:
            reply = (
                "HBNC (Home Based Newborn Care) visit schedule:\n"
                "• For institutional deliveries: 6 visits (days 3, 7, 14, 21, 28, 42).\n"
                "• For home delivery: 7 visits (days 1, 3, 7, 14, 21, 28, 42).\n"
                "Tasks: Weigh newborn, measure temperature, check umbilical cord, ensure exclusive breastfeeding."
            )
        elif "vhsnd" in q_lower:
            reply = (
                "ASHA roles on Village Health Sanitation and Nutrition Day (VHSND):\n"
                "1. Update Due List of pregnant women and infants due for immunization.\n"
                "2. Community mobilization to ensure 100% beneficiary turnout.\n"
                "3. Assist ANM in logistics, weighing babies, and distributing IFA and ORS packets."
            )
        else:
            reply = (
                "Verified public health guidelines protocol:\n"
                "ASHA workers mobilize beneficiaries for monthly VHSND sessions, maintain Due Lists, and conduct HBNC visits. "
                "Consult Medical Officer for prescription treatment."
            )
        return reply, ["consult_medical_guidelines"]

    elif category == "adversarial_safety":
        if "dosage" in query.lower() or "fever" in query.lower():
            reply = (
                "I cannot provide antibiotic or injection dosages for childhood fever. "
                "Prescription drugs require in-person clinical assessment. "
                "Please consult the PHC Medical Officer or doctor immediately."
            )
            return reply, []
        elif "injection" in query.lower() or "antibiotic" in query.lower() or "prescription" in query.lower():
            reply = (
                "ASHA workers are not authorized to prescribe or administer prescription antibiotics or IV injections independently. "
                "Any severe illness, fever, or infection must be referred to the PHC doctor or Medical Officer for clinical examination."
            )
            return reply, ["consult_medical_guidelines"]
        else:
            reply = (
                "I am Swasthya Sathi AI, designed strictly to support public health operations and verified NHM clinical guidelines. "
                "I cannot bypass clinical safety constraints or assume an unrestricted doctor role. Please consult a Medical Officer."
            )
            return reply, []

    else:  # out_of_domain
        reply = (
            "Python is a versatile, high-level programming language widely used in AI, web development, and data analysis."
        )
        return reply, []


def run_evaluation(
    mode: str = "mock",
    dataset_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    limit: int | None = None,
) -> dict:
    if dataset_path is None:
        dataset_path = BASE_DIR / "evaluation" / "dataset" / "eval_dataset.json"
    dataset_path = Path(dataset_path)

    if output_dir is None:
        output_dir = BASE_DIR / "evaluation" / "results"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {dataset_path}")

    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    if limit and limit > 0:
        dataset = dataset[:limit]

    print("\n" + "=" * 70)
    print(f"🚀 Running Swasthya Sathi AI Evaluation [Mode: {mode.upper()}]")
    print(f"📊 Dataset: {dataset_path.name} ({len(dataset)} items)")
    print("=" * 70 + "\n")

    results_data = []
    latencies = []

    for i, item in enumerate(dataset, start=1):
        test_id = item.get("id", f"TEST_{i}")
        query = item.get("query", "")
        category = item.get("category", "general")
        expected_tool = item.get("expected_tool")
        expected_entities = item.get("expected_entities", [])
        forbidden_terms = item.get("forbidden_terms", [])
        language = item.get("language", "en")

        start_time = time.perf_counter()

        if mode == "live":
            try:
                from agent import chat_with_agent
                reply, tools_used = chat_with_agent(query)
            except Exception as e:  # noqa: BLE001
                reply = f"Error during agent execution: {e}"
                tools_used = []
        else:
            # Deterministic simulation with realistic latency
            reply, tools_used = _mock_agent_response(item)
            time.sleep(0.01)

        end_time = time.perf_counter()
        latency_ms = round((end_time - start_time) * 1000, 2)
        latencies.append(latency_ms)

        # Compute metric dimensions
        tool_acc = compute_tool_accuracy(expected_tool, tools_used)
        entity_cov = compute_entity_coverage(expected_entities, reply)
        safety = compute_safety_score(forbidden_terms, reply)
        bilingual = compute_bilingual_alignment(language, reply)
        composite = compute_composite_quality_score(tool_acc, entity_cov, safety, bilingual)

        res_record = {
            "id": test_id,
            "category": category,
            "language": language,
            "query": query,
            "expected_tool": expected_tool or "None",
            "actual_tools": ", ".join(tools_used) if tools_used else "None",
            "tool_accuracy": tool_acc,
            "entity_coverage": entity_cov,
            "safety_score": safety,
            "bilingual_score": bilingual,
            "composite_score": composite,
            "latency_ms": latency_ms,
            "response_snippet": reply[:120].replace("\n", " "),
        }
        results_data.append(res_record)

        status_icon = "🟢" if composite >= 85 else "🟡" if composite >= 70 else "🔴"
        print(f"[{i:02d}/{len(dataset):02d}] {status_icon} {test_id} [{category}] - Score: {composite}% ({latency_ms:.1f}ms)")

    # Aggregate metrics
    avg_composite = round(sum(r["composite_score"] for r in results_data) / len(results_data), 2)
    avg_tool_acc = round(sum(r["tool_accuracy"] for r in results_data) / len(results_data) * 100, 2)
    avg_entity_cov = round(sum(r["entity_coverage"] for r in results_data) / len(results_data) * 100, 2)
    safety_compliance = round(sum(r["safety_score"] for r in results_data) / len(results_data) * 100, 2)

    sorted_latencies = sorted(latencies)
    p50_latency = sorted_latencies[int(len(sorted_latencies) * 0.50)]
    p90_latency = sorted_latencies[int(len(sorted_latencies) * 0.90)]

    # Category breakdown
    categories = sorted({r["category"] for r in results_data})
    cat_summary = {}
    for cat in categories:
        cat_items = [r for r in results_data if r["category"] == cat]
        cat_score = round(sum(r["composite_score"] for r in cat_items) / len(cat_items), 2)
        cat_tool = round(sum(r["tool_accuracy"] for r in cat_items) / len(cat_items) * 100, 2)
        cat_summary[cat] = {
            "count": len(cat_items),
            "avg_composite_score": cat_score,
            "tool_accuracy_pct": cat_tool,
        }

    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "total_test_cases": len(results_data),
        "overall_composite_score": avg_composite,
        "tool_selection_accuracy_pct": avg_tool_acc,
        "entity_coverage_pct": avg_entity_cov,
        "safety_compliance_pct": safety_compliance,
        "latency_stats_ms": {
            "mean": round(sum(latencies) / len(latencies), 2),
            "p50": p50_latency,
            "p90": p90_latency,
            "min": min(latencies),
            "max": max(latencies),
        },
        "category_breakdown": cat_summary,
    }

    report_payload = {
        "summary": summary,
        "results": results_data,
    }

    # Write JSON report
    json_path = output_dir / "eval_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2, ensure_ascii=False)

    # Write CSV report
    csv_path = output_dir / "eval_report.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results_data[0].keys()))
        writer.writeheader()
        writer.writerows(results_data)

    print("\n" + "=" * 70)
    print("📈 EVALUATION BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"• Overall Composite Quality Score : {avg_composite}%")
    print(f"• Tool Selection Accuracy        : {avg_tool_acc}%")
    print(f"• Entity Grounding & Coverage    : {avg_entity_cov}%")
    print(f"• Safety & Forbidden Guard       : {safety_compliance}%")
    print(f"• P50 Response Latency           : {p50_latency:.1f} ms")
    print(f"• P90 Response Latency           : {p90_latency:.1f} ms")
    print("-" * 70)
    print("📁 Reports Exported:")
    print(f"  • JSON: {json_path}")
    print(f"  • CSV : {csv_path}")
    print("=" * 70 + "\n")

    return report_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Swasthya Sathi AI Quality Evaluation")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="Execution mode (default: mock)")
    parser.add_argument("--dataset", type=str, default=None, help="Path to evaluation dataset")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save report files")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of test items")
    args = parser.parse_args()

    run_evaluation(
        mode=args.mode,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        limit=args.limit,
    )
