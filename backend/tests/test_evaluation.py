"""
Unit tests for AI Response Evaluation Framework (Issue #13)
-----------------------------------------------------------
Tests metric functions, dataset schema validity, and evaluation runner execution.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure evaluation directory is importable
BASE_DIR = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = BASE_DIR / "evaluation"
sys.path.insert(0, str(EVAL_DIR))

from metrics import (  # noqa: E402
    compute_bilingual_alignment,
    compute_composite_quality_score,
    compute_entity_coverage,
    compute_safety_score,
    compute_tool_accuracy,
)
from evaluate import run_evaluation  # noqa: E402


def test_tool_accuracy_metric():
    # Exact match
    assert compute_tool_accuracy("mark_attendance", ["mark_attendance"]) == 1.0
    # Partial match
    assert compute_tool_accuracy("mark_attendance", ["mark_attendance: Kajal present"]) == 1.0
    # Mismatch
    assert compute_tool_accuracy("mark_attendance", ["list_workers"]) == 0.0
    # Expected None, no tools called -> 1.0
    assert compute_tool_accuracy(None, []) == 1.0
    # Expected None, tool called -> 0.5 penalty
    assert compute_tool_accuracy(None, ["mark_attendance"]) == 0.5


def test_entity_coverage_metric():
    text = "BCG is given at birth, and Hepatitis B within 24 hours. OPV 0 is also oral."
    # Full coverage
    assert compute_entity_coverage(["BCG", "Hepatitis B", "OPV"], text) == 1.0
    # Partial coverage
    assert compute_entity_coverage(["BCG", "Pentavalent", "OPV"], text) == 0.6667
    # Zero coverage
    assert compute_entity_coverage(["Zinc", "ORS"], text) == 0.0
    # Empty expected entities
    assert compute_entity_coverage([], text) == 1.0
    # Empty response
    assert compute_entity_coverage(["BCG"], "") == 0.0


def test_safety_score_metric():
    clean_text = "Refer patient to the PHC Medical Officer for antibiotic prescription."
    assert compute_safety_score(["unauthorized injection", "give 500mg IV"], clean_text) == 1.0

    violating_text = "You can give unauthorized injection directly."
    assert compute_safety_score(["unauthorized injection"], violating_text) == 0.0

    # No forbidden terms
    assert compute_safety_score([], violating_text) == 1.0


def test_bilingual_alignment_metric():
    devanagari_text = "हाँ, नवजात शिशु को बीसीजी का टीका लगाया जाता है।"
    english_text = "Yes, BCG vaccine is administered to the newborn child."
    hinglish_text = "Navjaat shishu ko BCG vaccine diya jata hai."

    assert compute_bilingual_alignment("hi", devanagari_text) == 1.0
    assert compute_bilingual_alignment("en", english_text) == 0.9
    assert compute_bilingual_alignment("hinglish", hinglish_text) == 1.0


def test_composite_quality_score():
    score = compute_composite_quality_score(
        tool_accuracy=1.0,
        entity_coverage=1.0,
        safety_score=1.0,
        bilingual_score=1.0,
    )
    assert score == 100.0

    penalty_score = compute_composite_quality_score(
        tool_accuracy=0.0,
        entity_coverage=0.5,
        safety_score=0.0,
        bilingual_score=0.8,
    )
    # (0 * 0.35) + (0.5 * 0.35) + (0 * 0.20) + (0.8 * 0.10) = 0.175 + 0.08 = 0.255 -> 25.5%
    assert penalty_score == 25.5


def test_eval_dataset_schema():
    dataset_file = EVAL_DIR / "dataset" / "eval_dataset.json"
    assert dataset_file.exists(), "Dataset file must exist"

    with open(dataset_file, encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) >= 20, "Evaluation suite must contain at least 20 benchmark test cases"

    required_keys = {"id", "query", "category", "language", "expected_tool", "expected_entities", "forbidden_terms", "expected_intent"}
    ids = set()

    for item in data:
        assert required_keys.issubset(item.keys()), f"Item {item.get('id')} missing required keys"
        assert item["id"] not in ids, f"Duplicate ID: {item['id']}"
        ids.add(item["id"])
        assert isinstance(item["expected_entities"], list)
        assert isinstance(item["forbidden_terms"], list)


def test_run_evaluation_mock_execution(tmp_path):
    report = run_evaluation(mode="mock", output_dir=tmp_path, limit=5)
    assert report is not None
    assert report["summary"]["total_test_cases"] == 5
    assert report["summary"]["overall_composite_score"] > 80.0
    assert (tmp_path / "eval_report.json").exists()
    assert (tmp_path / "eval_report.csv").exists()
