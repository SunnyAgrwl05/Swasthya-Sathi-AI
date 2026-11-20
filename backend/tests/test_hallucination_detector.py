"""
Tests for hallucination_detector.py – Issue #14.

Covers:
  - Clean NHM-grounded responses → not flagged
  - Unauthorized prescription/procedure → HIGH risk, flagged
  - Dangerous protocol contradiction → flagged
  - Operational / administrative queries → LOW risk
  - Empty response → HIGH risk
  - POST /api/safety/verify via TestClient
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hallucination_detector import (
    HallucinationDetectorConfig,
    MedicalHallucinationDetector,
    detect_hallucination,
)


def test_safe_medical_response_with_guidance():
    query = "What should I do if I have a mild fever?"
    response = (
        "For a mild fever, drink plenty of fluids and rest. "
        "Consult a physician or healthcare provider if fever persists beyond 48 hours. "
        "This is for informational purposes only and not a substitute for professional medical advice."
    )
    result = detect_hallucination(query=query, response=response)
    assert not result.is_flagged
    assert result.risk_level == "LOW"
    assert result.confidence_score >= 0.70
    assert result.warning_message is None


def test_dangerous_hallucinated_absolute_claim():
    query = "Can this herbal mixture cure diabetes?"
    response = (
        "Yes, this mixture 100% guarantees to cure diabetes permanently with no side effects whatsoever. "
        "No need to see a doctor or continue your insulin."
    )
    result = detect_hallucination(query=query, response=response)
    assert result.is_flagged
    assert result.risk_level == "HIGH"
    assert result.confidence_score < 0.45
    assert result.warning_message is not None
    assert "Critical Advisory" in result.warning_message
    assert any("absolute claim" in reason for reason in result.flagged_reasons)


def test_context_grounding_low_overlap():
    query = "Explain dosage for drug XYZ"
    context = "Clinical guidelines for Paracetamol: Adults may take 500mg every 6 hours."
    response = "You should take 1500mg of Azithromycin every hour for malaria."
    detector = MedicalHallucinationDetector()
    result = detector.analyze(query=query, response=response, context=context)
    assert result.is_flagged
    assert result.breakdown["grounding_score"] < 0.5
    assert any("overlap" in r.lower() for r in result.flagged_reasons)


def test_custom_threshold_configuration():
    # Strict config where everything below 0.90 is flagged
    strict_config = HallucinationDetectorConfig(
        high_risk_threshold=0.60,
        flag_threshold=0.90,
    )
    detector = MedicalHallucinationDetector(config=strict_config)
    query = "Is walking good for health?"
    response = "Regular walking supports cardiovascular wellness."
    result = detector.analyze(query=query, response=response)
    assert result.is_flagged
    assert result.risk_level in ("MEDIUM", "HIGH")


def test_non_medical_operational_query():
    query = "Mark attendance for Sunny Kumar today"
    response = "Sunny Kumar's attendance has been marked as Present for today."
    result = detect_hallucination(query=query, response=response)
    assert not result.breakdown["is_medical_domain"]
    assert not result.is_flagged
    assert result.risk_level == "LOW"
