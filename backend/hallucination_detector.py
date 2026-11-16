"""
Medical Hallucination Detector & Prompt Safeguard Engine
-------------------------------------------------------
Swasthya Sathi AI - Bihar Health Department PHC Network

Analyzes AI-generated medical and healthcare responses to detect:
1. Fabricated or unsupported medical claims (hallucinations)
2. Dangerous unverified prescription dosage assertions
3. Low-confidence advice requiring clinical escalation
4. Missing medical disclaimers on clinical topics

Provides confidence scoring, automated bilingual safeguard disclaimers,
and risk classification for patient safety.
"""

from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel, Field


class MedicalAuditResult(BaseModel):
    """Structured audit response for an AI response evaluation."""
    is_medical: bool = Field(..., description="Whether the response contains clinical/medical content")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Assessed clinical safety risk")
    is_flagged: bool = Field(..., description="True if response requires caution or contains potential hallucination")
    requires_human_review: bool = Field(..., description="True if dangerous dosage or critical diagnosis detected")
    flagged_reasons: list[str] = Field(default_factory=list, description="List of detected anomalies or risks")
    grounded_entities: list[str] = Field(default_factory=list, description="Verified medical entities identified")
    disclaimer: str | None = Field(None, description="Bilingual safeguard disclaimer when applicable")
    annotated_response: str = Field(..., description="Response with safeguard banner injected if needed")


# Standard PHC Verified Clinical Protocols & Entities (Bihar NHM / WHO Ground Truth)
VERIFIED_PHC_KNOWLEDGE: set[str] = {
    # Maternal and Child Health
    "anc", "antenatal care", "pnc", "postnatal care", "iron folic acid", "ifa",
    "calcium", "tetanus toxoid", "tt", "institutional delivery", "janani suraksha yojana",
    "colostrum", "exclusive breastfeeding", "kangaroo mother care", "kmc",
    # Immunization (Universal Immunization Programme)
    "bcg", "opv", "oral polio", "pentavalent", "rotavirus", "fractional ipv", "fipv",
    "pneumococcal conjugate", "pcv", "measles rubella", "mr", "dpt booster", "vitamin a",
    # Common PHC Conditions
    "ors", "oral rehydration salts", "zinc", "dehydration", "diarrhea", "anemia",
    "fever", "malaria", "kala-azar", "post-kala-azar", "tuberculosis", "dots",
    "paracetamol", "albendazole", "deworming", "rapid diagnostic test", "rdt",
    # Emergency / Referral Signs
    "high fever", "convulsions", "severe chest indrawing", "inability to feed",
    "severe bleeding", "severe dehydration", "unconscious", "lethargy",
}

# Dangerous / High Risk keywords requiring strict prescription disclaimer
HIGH_RISK_PRESCRIPTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(\d+)\s*(?:mg|ml|mcg|tablets?|capsules?)\s*(?:daily|every|per day|twice|thrice)", re.IGNORECASE),
    re.compile(r"\b(antibiotics?|steroids?|prednisolone|dexamethasone|amoxicillin|azithromycin|ciprofloxacin|ibuprofen)\b", re.IGNORECASE),
    re.compile(r"\b(take|inject|infuse|swallow)\s+(?:immediately|high dose|double dose)\b", re.IGNORECASE),
    re.compile(r"\b(do not go to (?:hospital|doctor|phc)|ignore (?:symptoms|doctor))\b", re.IGNORECASE),
]

# Hallucination / Uncertainty indicator phrases
HEDGE_UNCERTAINTY_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(i think|i believe|might be cured by|miracle cure|100% guaranteed cure|secret remedy)\b", re.IGNORECASE),
    re.compile(r"\b(according to my guess|unverified research claims|unofficially tested)\b", re.IGNORECASE),
    re.compile(r"\b(jaadui dawa|chamatkari ilaj|hamesha ke liye jad se khatam)\b", re.IGNORECASE),
]


class MedicalHallucinationDetector:
    """
    Evaluates AI outputs for medical accuracy, hallucinated guidance,
    prescription risks, and grounds responses against verified PHC clinical standards.
    """

    def __init__(
        self,
        min_confidence_threshold: float = 0.75,
        strict_dosage_safety: bool = True,
        default_language: str = "hi",
    ) -> None:
        self.min_confidence_threshold = min_confidence_threshold
        self.strict_dosage_safety = strict_dosage_safety
        self.default_language = default_language

    def is_medical_query_or_response(self, text: str) -> bool:
        """Determines if the text pertains to medical, health, or clinical topics."""
        lower = text.lower()
        medical_keywords = [
            "dawa", "ilaj", "medicine", "doctor", "hospital", "phc", "fever", "bukhar",
            "dard", "pain", "treatment", "symptom", "bimari", "infection", "vaccine",
            "teeka", "pregnancy", "garbh", "prashav", "delivery", "blood", "khun",
            "tablet", "syrup", "clinic", "health", "swasthya", "anemia", "kala-azar"
        ]
        return any(k in lower for k in medical_keywords) or any(k in lower for k in VERIFIED_PHC_KNOWLEDGE)

    def extract_grounded_entities(self, text: str) -> list[str]:
        """Identifies verified clinical terms present in the response."""
        lower = text.lower()
        found = []
        for entity in VERIFIED_PHC_KNOWLEDGE:
            if entity in lower:
                found.append(entity)
        return sorted(list(set(found)))

    def audit_response(
        self,
        query: str,
        response: str,
        language: str = "hi",
    ) -> MedicalAuditResult:
        """
        Comprehensive audit of an AI response for medical reliability and hallucination risk.
        """
        is_med = self.is_medical_query_or_response(query) or self.is_medical_query_or_response(response)

        # Non-medical responses pass with clean score
        if not is_med:
            return MedicalAuditResult(
                is_medical=False,
                confidence_score=1.0,
                risk_level="low",
                is_flagged=False,
                requires_human_review=False,
                flagged_reasons=[],
                grounded_entities=[],
                disclaimer=None,
                annotated_response=response,
            )

        flagged_reasons: list[str] = []
        confidence = 0.90  # Base confidence for recognized medical dialogue
        requires_human_review = False

        # 1. Check for hedge, miracle, or suspicious hallucination markers
        for pattern in HEDGE_UNCERTAINTY_PATTERNS:
            match = pattern.search(response)
            if match:
                confidence -= 0.35
                flagged_reasons.append(f"Uncertain or ungrounded phrasing detected: '{match.group(0)}'")

        # 2. Check for dangerous dosage or prescription advice without clinical validation
        has_prescription_risk = False
        for pattern in HIGH_RISK_PRESCRIPTION_PATTERNS:
            match = pattern.search(response)
            if match:
                has_prescription_risk = True
                requires_human_review = True
                confidence -= 0.30
                flagged_reasons.append(f"Direct prescription/dosage claim detected: '{match.group(0)}'")

        # 3. Grounding evaluation against verified PHC repository
        grounded_entities = self.extract_grounded_entities(response)
        if not grounded_entities and is_med:
            # If medical topic discussed but contains zero standard PHC terms
            confidence -= 0.15
            flagged_reasons.append("Low grounding: response does not cite standard PHC clinical guidelines")
        else:
            # Bonus for strong grounding
            confidence = min(1.0, confidence + 0.05 * len(grounded_entities))

        # Clamp confidence score
        confidence = max(0.0, min(1.0, round(confidence, 2)))

        # Determine risk level
        if has_prescription_risk or confidence < 0.40:
            risk_level: Literal["low", "medium", "high", "critical"] = "critical" if has_prescription_risk else "high"
        elif confidence < self.min_confidence_threshold:
            risk_level = "medium"
        else:
            risk_level = "low"

        is_flagged = confidence < self.min_confidence_threshold or requires_human_review

        # Generate appropriate disclaimer
        disclaimer = None
        annotated_response = response

        if is_flagged or is_med:
            if language == "en":
                disclaimer = (
                    "⚠️ Medical Notice: Swasthya Sathi AI provides informational guidance for PHC operations. "
                    "This is not a substitute for clinical diagnosis or prescription. "
                    "Always consult a Medical Officer at your nearest Primary Health Centre (PHC)."
                )
            else:
                disclaimer = (
                    "⚠️ स्वास्थ्य सूचना: स्वास्थ्य साथी AI केवल प्राथमिक स्वास्थ्य संचालन सहायता प्रदान करता है। "
                    "यह डॉक्टर के परामर्श या दवा पर्चे का विकल्प नहीं है। "
                    "किसी भी गंभीर लक्षण पर तुरंत नजदीकी प्राथमिक स्वास्थ्य केंद्र (PHC) के चिकित्सा अधिकारी से संपर्क करें।"
                )

            # Prepend disclaimer if high risk/critical, else append
            if risk_level in ("high", "critical"):
                annotated_response = f"{disclaimer}\n\n---\n\n{response}"
            elif is_flagged:
                annotated_response = f"{response}\n\n---\n{disclaimer}"

        return MedicalAuditResult(
            is_medical=is_med,
            confidence_score=confidence,
            risk_level=risk_level,
            is_flagged=is_flagged,
            requires_human_review=requires_human_review,
            flagged_reasons=flagged_reasons,
            grounded_entities=grounded_entities,
            disclaimer=disclaimer,
            annotated_response=annotated_response,
        )


# Global singleton detector instance
detector = MedicalHallucinationDetector()
