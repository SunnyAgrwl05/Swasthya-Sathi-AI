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

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# HallucinationDetector unit tests
# ---------------------------------------------------------------------------

from hallucination_detector import HallucinationDetector, RiskLevel, verify_medical_response


@pytest.fixture()
def detector():
    return HallucinationDetector()


class TestCleanNHMGroundedResponse:
    """Well-grounded NHM clinical advice should pass without flagging."""

    def test_immunization_response_not_flagged(self, detector):
        text = (
            "According to NHM guidelines, BCG and OPV should be given at birth. "
            "The pentavalent vaccine covers diphtheria, pertussis, tetanus, hepatitis B and Hib. "
            "Ensure the due list is updated after every VHSND session."
        )
        report = detector.assess_response(text)
        assert report.is_flagged is False
        assert report.risk_level == RiskLevel.LOW
        assert report.confidence_score >= 0.80

    def test_maternal_health_response_not_flagged(self, detector):
        text = (
            "Ensure the mother takes IFA tablets with water, not milk or tea. "
            "Four ANC visits are mandatory. Check for preeclampsia signs like high blood pressure. "
            "Calcium and albendazole supplements should be given as per PMSMA schedule."
        )
        report = detector.assess_response(text)
        assert report.is_flagged is False
        assert report.risk_level == RiskLevel.LOW

    def test_childhood_diarrhea_guidance_not_flagged(self, detector):
        text = (
            "Give ORS solution for rehydration and zinc for 14 days even after diarrhea stops. "
            "If signs of dehydration persist, refer to PHC immediately."
        )
        report = detector.assess_response(text)
        assert report.is_flagged is False


class TestUnauthorizedPrescriptions:
    """Responses containing prescription/procedure red-flags must be HIGH risk."""

    def test_iv_injection_flagged(self, detector):
        text = "You can give IV normal saline at home to stabilise the patient."
        report = detector.assess_response(text)
        assert report.is_flagged is True
        assert report.risk_level == RiskLevel.HIGH
        assert any("iv" in r.lower() for r in report.flagged_reasons)

    def test_prescribe_antibiotics_flagged(self, detector):
        text = "The ASHA worker can prescribe antibiotics for the infection."
        report = detector.assess_response(text)
        assert report.is_flagged is True
        assert report.risk_level == RiskLevel.HIGH

    def test_prescribe_amoxicillin_flagged(self, detector):
        text = "Prescribe amoxicillin 250 mg three times a day for five days."
        report = detector.assess_response(text)
        assert report.is_flagged is True

    def test_administer_steroids_flagged(self, detector):
        text = "Administer steroids immediately to reduce inflammation."
        report = detector.assess_response(text)
        assert report.is_flagged is True


class TestDangerousContradictions:
    """Protocol violations must trigger flagging."""

    def test_ifa_with_tea_flagged(self, detector):
        text = "It is fine to take IFA tablets with a cup of tea in the morning."
        report = detector.assess_response(text)
        assert report.is_flagged is True
        assert any("tea" in r.lower() or "ifa" in r.lower() for r in report.flagged_reasons)

    def test_zinc_stopped_early_flagged(self, detector):
        text = "Stop zinc after 1 day once the stool becomes normal."
        report = detector.assess_response(text)
        assert report.is_flagged is True

    def test_no_anc_needed_flagged(self, detector):
        text = "Some studies show no ANC needed for healthy women in rural areas."
        report = detector.assess_response(text)
        assert report.is_flagged is True


class TestOperationalAdministrativeQueries:
    """Attendance / roster / broadcast responses should not be flagged."""

    def test_attendance_report_not_flagged(self, detector):
        text = (
            "Today 12 out of 15 workers are marked present. "
            "3 workers are absent. The attendance roster has been updated."
        )
        report = detector.assess_response(text)
        assert report.is_flagged is False
        assert report.risk_level == RiskLevel.LOW

    def test_broadcast_message_not_flagged(self, detector):
        text = (
            "Daily broadcast sent to all workers at PHC Sector 4. "
            "Workers on leave have been recorded in today's shift report."
        )
        report = detector.assess_response(text)
        assert report.is_flagged is False


class TestEdgeCases:
    """Empty / whitespace / very short responses."""

    def test_empty_string_flagged(self, detector):
        report = detector.assess_response("")
        assert report.is_flagged is True
        assert report.risk_level == RiskLevel.HIGH
        assert report.confidence_score == 0.0

    def test_whitespace_only_flagged(self, detector):
        report = detector.assess_response("   \n\t  ")
        assert report.is_flagged is True
        assert report.risk_level == RiskLevel.HIGH

    def test_confidence_score_bounded(self, detector):
        """Confidence must always be in [0, 1]."""
        for text in ["", "hello", "bcg opv rotavirus ors zinc iron folic acid anc antenatal imnci"]:
            report = detector.assess_response(text)
            assert 0.0 <= report.confidence_score <= 1.0


class TestVerifyMedicalResponseHelper:
    """Convenience wrapper returns serialisable dict."""

    def test_returns_dict(self):
        result = verify_medical_response("ORS and zinc for 14 days. Refer to PHC.", "diarrhea")
        assert isinstance(result, dict)
        assert "confidence_score" in result
        assert "risk_level" in result
        assert "is_flagged" in result
        assert "flagged_reasons" in result
        assert "grounded_terms" in result

    def test_dict_values_serializable(self):
        result = verify_medical_response("Give IV injection at home.", "treatment")
        assert isinstance(result["confidence_score"], float)
        assert isinstance(result["is_flagged"], bool)
        assert isinstance(result["flagged_reasons"], list)


# ---------------------------------------------------------------------------
# API endpoint tests (TestClient)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    from main import app
    return TestClient(app)


class TestSafetyVerifyEndpoint:
    """POST /api/safety/verify integration tests."""

    def test_clean_nhm_text_returns_low_risk(self, client):
        resp = client.post(
            "/api/safety/verify",
            json={"response_text": "BCG at birth, OPV, pentavalent as per NHM schedule.", "query": "vaccines"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] in ("LOW", "MEDIUM")
        assert "confidence_score" in data

    def test_flagged_text_returns_high_risk(self, client):
        resp = client.post(
            "/api/safety/verify",
            json={"response_text": "Give IV antibiotics immediately.", "query": "infection"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_flagged"] is True
        assert data["risk_level"] == "HIGH"

    def test_empty_text_returns_high_risk(self, client):
        resp = client.post("/api/safety/verify", json={"response_text": "", "query": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_flagged"] is True
        assert data["risk_level"] == "HIGH"

    def test_response_schema_complete(self, client):
        resp = client.post(
            "/api/safety/verify",
            json={"response_text": "Refer patient to PHC.", "query": "referral"},
        )
        assert resp.status_code == 200
        data = resp.json()
        required_keys = {"confidence_score", "risk_level", "is_flagged", "flagged_reasons", "grounded_terms"}
        assert required_keys.issubset(data.keys())

    def test_missing_query_field_defaults_gracefully(self, client):
        """query is optional; omitting it should not cause a 422."""
        resp = client.post(
            "/api/safety/verify",
            json={"response_text": "Workers marked present today."},
        )
        assert resp.status_code == 200
