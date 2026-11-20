import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_root = os.path.dirname(backend_dir)
eval_dir = os.path.join(repo_root, "evaluation")
if eval_dir not in sys.path:
    sys.path.insert(0, eval_dir)

from evaluate import run_evaluation  # noqa: E402
from metrics import (  # noqa: E402
    calculate_clinical_accuracy_score,
    calculate_completeness_score,
    calculate_consistency_score,
    calculate_latency_score,
    calculate_relevance_score,
    compute_composite_quality_score,
)


def test_relevance_metric():
    query = "Bacche ko dast aur ulti hai"
    response = "Bacche ko dast hone par ORS ka ghol pilayein."
    score = calculate_relevance_score(query, response)
    assert 0.0 < score <= 1.0


def test_clinical_accuracy_with_entities():
    response = "Bachon ko diarrhea me ORS aur zinc dena chahiye aur PHC refer karein."
    key_entities = ["ors", "zinc", "refer"]
    score = calculate_clinical_accuracy_score(response, key_entities)
    assert score == 1.0


def test_clinical_accuracy_forbidden_claim_penalty():
    response = "Bachon ko 500 mg amoxicillin antibiotics without test dein."
    key_entities = ["ors", "zinc"]
    forbidden = ["antibiotics without test", "500 mg amoxicillin"]
    score = calculate_clinical_accuracy_score(response, key_entities, forbidden)
    assert score == 0.0


def test_completeness_metric():
    response = "BCG, OPV and Hepatitis B birth dose are given at birth."
    reference = "At birth: BCG, OPV birth dose, Hepatitis B birth dose."
    key_entities = ["bcg", "opv", "hepatitis b"]
    score = calculate_completeness_score(response, reference, key_entities)
    assert score >= 0.70


def test_consistency_metric():
    resp1 = "Give ORS and zinc for diarrhea treatment."
    resp2 = "For diarrhea, administer ORS solution and zinc tablets."
    score = calculate_consistency_score([resp1, resp2])
    assert score > 0.20


def test_latency_scoring():
    fast_score = calculate_latency_score(800.0)
    assert fast_score == 1.0

    slow_score = calculate_latency_score(4500.0)
    assert slow_score < 1.0
    assert slow_score >= 0.2


def test_composite_quality_score():
    q = compute_composite_quality_score(1.0, 1.0, 1.0, 1.0)
    assert q == 100.0


def test_evaluation_pipeline_execution():
    dataset_path = os.path.join(eval_dir, "dataset", "medical_qa.json")
    summary = run_evaluation(dataset_path=dataset_path, use_live_agent=False)
    assert summary["total_evaluated"] >= 5
    assert "mean_clinical_accuracy" in summary
    assert "overall_composite_score" in summary
    assert len(summary["details"]) == summary["total_evaluated"]
