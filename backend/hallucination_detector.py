"""
Hallucination Detection & Medical Safety Assurance Engine
---------------------------------------------------------
Validates AI-generated medical responses for public health frontline workers.
Scores factual grounding against National Health Mission (NHM) guidelines and
detects unauthorized clinical assertions, unverified drug prescriptions, and risky advice.

Closes Issue #14.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class HallucinationReport:
    """Structured evaluation report for an AI medical response."""
    confidence_score: float
    risk_level: RiskLevel
    is_flagged: bool
    warning_message: str | None
    flagged_reasons: list[str] = field(default_factory=list)
    grounded_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "confidence_score": round(self.confidence_score, 2),
            "risk_level": self.risk_level.value,
            "is_flagged": self.is_flagged,
            "warning_message": self.warning_message,
            "flagged_reasons": self.flagged_reasons,
            "grounded_terms": self.grounded_terms,
        }


class HallucinationDetector:
    """
    Evaluates medical response reliability using multi-layer clinical rule checking,
    lexical guideline grounding, and contraindication scanning.
    """

    # Clinical red flags: advice frontline workers (ASHAs/ANMs) must NEVER provide independently
    UNAUTHORIZED_PRESCRIPTION_TERMS = [
        "give iv",
        "intravenous injection",
        "inject iv",
        "prescribe antibiotics",
        "prescribe amoxicillin",
        "prescribe azithromycin",
        "prescribe ciprofloxacin",
        "administer steroids",
        "give dexamethasone",
        "schedule h drug",
        "perform incision",
        "independently prescribe",
    ]

    # Contradictory medical claims that violate standard protocols.
    # Each entry is a (regex_pattern, human_readable_explanation) tuple.
    # Patterns are matched case-insensitively against the full response text.
    DANGEROUS_CONTRADICTIONS = [
        (r"with\s+(?:a\s+cup\s+of\s+)?tea", "Iron/IFA should not be consumed with tea or milk"),
        (r"with\s+(?:a\s+glass\s+of\s+)?milk", "Iron/IFA should not be consumed with dairy"),
        (r"stop\s+zinc\s+after\s+1\s+day", "Zinc must be given for full 14 days in diarrhea"),
        (r"stop\s+zinc\s+when\s+diarrhea\s+stops", "Zinc course is strictly 14 days"),
        (r"skip\s+bcg\s+at\s+birth", "BCG must be administered at birth or within 1 year"),
        (r"no\s+anc\s+needed", "At least 4 ANC visits are mandatory"),
    ]

    # Verified clinical anchor vocabulary (NHM guidelines)
    VERIFIED_ANCHORS = {
        "immunization": [
            "bcg", "hepatitis b", "opv", "pentavalent", "rotavirus", "rvv",
            "fipv", "pcv", "mr", "je", "dpt", "td", "national immunization schedule"
        ],
        "maternal": [
            "anc", "antenatal", "preeclampsia", "blood pressure", "ifa",
            "iron", "folic acid", "pmsma", "calcium", "albendazole", "tetanus"
        ],
        "childhood": [
            "ors", "zinc", "diarrhea", "dehydration", "pneumonia", "fast breathing",
            "chest indrawing", "imnci", "exclusive breastfeeding", "colostrum"
        ],
        "field_protocols": [
            "vhsnd", "due list", "hbnc", "home based newborn care", "otc kit",
            "medical officer", "phc", "sub-center", "referral"
        ]
    }

    def __init__(
        self,
        high_confidence_threshold: float = 0.80,
        low_confidence_threshold: float = 0.60,
    ):
        self.high_threshold = float(
            os.getenv("HALLUCINATION_HIGH_THRESHOLD", str(high_confidence_threshold))
        )
        self.low_threshold = float(
            os.getenv("HALLUCINATION_LOW_THRESHOLD", str(low_confidence_threshold))
        )

    def assess_response(self, response_text: str, query: str = "") -> HallucinationReport:
        """
        Calculates a clinical confidence score (0.0 - 1.0) and generates warnings.
        """
        if not response_text or not response_text.strip():
            return HallucinationReport(
                confidence_score=0.0,
                risk_level=RiskLevel.HIGH,
                is_flagged=True,
                warning_message="⚠️ Warning: Empty AI response.",
                flagged_reasons=["Empty response text"],
            )

        text_lower = response_text.lower()
        flagged_reasons: list[str] = []
        grounded_terms: list[str] = []

        # 1. Scan for critical unauthorized prescription or procedure red flags
        for term in self.UNAUTHORIZED_PRESCRIPTION_TERMS:
            if term in text_lower:
                flagged_reasons.append(f"Unauthorized clinical procedure or prescription detected: '{term}'")

        # 2. Scan for dangerous contradictory assertions (regex-based)
        for pattern, explanation in self.DANGEROUS_CONTRADICTIONS:
            if re.search(pattern, text_lower):
                flagged_reasons.append(f"Protocol violation: {explanation}")

        # 3. Assess positive grounding against verified NHM anchors
        matched_anchors = 0
        all_anchors = []
        for category, terms in self.VERIFIED_ANCHORS.items():
            all_anchors.extend(terms)
            for term in terms:
                if term in text_lower:
                    matched_anchors += 1
                    if term not in grounded_terms:
                        grounded_terms.append(term)

        # 4. Compute baseline confidence score
        if flagged_reasons:
            # Critical clinical violations immediately drop confidence below safety threshold
            confidence = max(0.10, 0.45 - (0.15 * len(flagged_reasons)))
        elif len(grounded_terms) >= 3:
            confidence = 0.95
        elif len(grounded_terms) >= 1:
            confidence = 0.82
        elif self._is_administrative_or_operational(text_lower):
            # Operational queries (roster, attendance, timestamps) are non-clinical
            confidence = 0.90
            grounded_terms.append("operational_roster")
        else:
            # Response lacks verified guideline terminology
            confidence = 0.55
            flagged_reasons.append("Low guideline lexical grounding; claims could not be matched against NHM protocols")

        confidence = round(min(1.0, max(0.0, confidence)), 2)

        # 5. Determine Risk Level & Warning
        if confidence < self.low_threshold:
            risk = RiskLevel.HIGH
            is_flagged = True
            warning = (
                "⚠️ Clinical Safety Warning: This response contains medical claims or recommendations that could not be verified "
                "against official National Health Mission (NHM) guidelines. Always consult the PHC Medical Officer or doctor before acting."
            )
        elif confidence < self.high_threshold:
            risk = RiskLevel.MEDIUM
            is_flagged = True
            warning = (
                "ℹ️ Notice: Review guideline recommendations with the local PHC supervisor. Ensure protocols match local VHSND schedules."
            )
        else:
            risk = RiskLevel.LOW
            is_flagged = False
            warning = None

        return HallucinationReport(
            confidence_score=confidence,
            risk_level=risk,
            is_flagged=is_flagged,
            warning_message=warning,
            flagged_reasons=flagged_reasons,
            grounded_terms=grounded_terms,
        )

    def _is_administrative_or_operational(self, text: str) -> bool:
        """Identifies standard administrative messages that do not require clinical grounding."""
        admin_keywords = [
            "attendance", "worker", "roster", "phc", "marked", "present",
            "absent", "leave", "broadcast", "report", "summary", "shift"
        ]
        return sum(1 for kw in admin_keywords if kw in text) >= 2


# Singleton instance for quick application access
_detector_instance: HallucinationDetector | None = None


def get_detector() -> HallucinationDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = HallucinationDetector()
    return _detector_instance


def verify_medical_response(text: str, query: str = "") -> dict:
    """Convenience helper returning dict payload."""
    detector = get_detector()
    report = detector.assess_response(text, query)
    return report.to_dict()
