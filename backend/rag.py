"""
Retrieval-Augmented Generation (RAG) Engine for Swasthya Sathi AI
-----------------------------------------------------------------
Bihar Health Department - Primary Health Centre (PHC) Network

Provides grounded context retrieval from validated Bihar NHM and WHO
clinical guidelines to prevent hallucinations and supply verified operational
and medical SOPs for health workers.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pydantic import BaseModel, Field


class MedicalDocument(BaseModel):
    """A verified medical/operational knowledge document."""
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document or protocol title")
    category: str = Field(..., description="Medical or operational domain")
    content: str = Field(..., description="Verified guideline content")
    source: str = Field(..., description="Authoritative source attribution (e.g. Bihar NHM, WHO, MoHFW)")
    keywords: list[str] = Field(default_factory=list, description="Associated Hindi and English retrieval keywords")


class RAGRetrievalResult(BaseModel):
    """Result of a RAG query lookup."""
    query: str
    documents: list[MedicalDocument] = Field(default_factory=list)
    similarity_scores: list[float] = Field(default_factory=list)
    augmented_context: str = Field("", description="Pre-formatted context ready for LLM prompt injection")
    sources: list[str] = Field(default_factory=list)


# Curated, authoritative medical guidelines for Bihar PHCs
PHC_KNOWLEDGE_BASE: list[dict] = [
    {
        "doc_id": "PHC-MAT-001",
        "title": "Antenatal Care (ANC) & Maternal Health Protocol",
        "category": "Maternal Health",
        "content": (
            "Every pregnant woman must receive at least 4 Antenatal Care (ANC) checkups at the PHC or Sub-centre. "
            "Essential interventions include: Blood pressure monitoring, hemoglobin testing for anemia, "
            "abdominal examination, two doses of Tetanus Toxoid (TT) vaccine, and a minimum of 180 Iron & Folic Acid "
            "(IFA) tablets along with 360 Calcium tablets. High-risk pregnancy indicators: severe anemia (Hb < 7 g/dL), "
            "hypertension (BP >= 140/90 mmHg), gestational diabetes, or multiple gestations."
        ),
        "source": "Bihar National Health Mission (NHM) - Maternal Health Guidelines",
        "keywords": ["anc", "pregnancy", "garbh", "maternal", "ifa", "iron", "calcium", "tetanus", "tt", "anemia", "prashav"],
    },
    {
        "doc_id": "PHC-IMM-002",
        "title": "Universal Immunization Programme (UIP) Schedule",
        "category": "Immunization",
        "content": (
            "Universal Immunization Programme schedule for infants: "
            "At birth: BCG, OPV-0, Hepatitis B birth dose. "
            "At 6 weeks, 10 weeks, and 14 weeks: Pentavalent (DPT+HepB+Hib), Rotavirus vaccine, Fractional IPV (fIPV), and PCV. "
            "At 9-12 months: Measles-Rubella (MR) 1st dose, JE (in endemic districts), PCV booster, Vitamin A 1st dose. "
            "At 16-24 months: MR 2nd dose, DPT booster-1, OPV booster. "
            "All vaccines must be stored in the Cold Chain (ILR) between +2°C and +8°C."
        ),
        "source": "MoHFW Universal Immunization Guidelines & Bihar State Health Society",
        "keywords": ["immunization", "teeka", "vaccine", "bcg", "polio", "opv", "pentavalent", "rotavirus", "mr", "measles", "cold chain"],
    },
    {
        "doc_id": "PHC-DIA-003",
        "title": "Childhood Diarrhea & Dehydration Management Protocol",
        "category": "Child Health",
        "content": (
            "Standard protocol for acute watery diarrhea in children under 5: "
            "1. Oral Rehydration Salts (ORS): Dissolve 1 sachet in 1 litre of clean drinking water; give after each loose stool. "
            "2. Zinc Supplementation: 10 mg/day for infants under 6 months; 20 mg/day for children 6 months to 5 years, for 14 continuous days. "
            "3. Continued feeding and breastfeeding during diarrhea. "
            "Danger signs requiring emergency referral to PHC/District Hospital: blood in stool, vomiting everything, "
            "sunken eyes, skin pinch goes back very slowly, lethargy or unconsciousness."
        ),
        "source": "WHO / UNICEF Integrated Management of Neonatal and Childhood Illness (IMNCI)",
        "keywords": ["diarrhea", "dast", "ors", "zinc", "dehydration", "paani ki kami", "vomiting", "ulti", "child", "baccha"],
    },
    {
        "doc_id": "PHC-KALA-004",
        "title": "Visceral Leishmaniasis (Kala-Azar) Diagnosis & Elimination Guidelines",
        "category": "Endemic Disease",
        "content": (
            "Visceral Leishmaniasis (Kala-Azar) clinical diagnosis in Bihar: "
            "Suspect Kala-Azar in any patient with fever lasting more than 15 days not responding to antimalarials or antibiotics, "
            "accompanied by splenomegaly (enlarged spleen) and anemia. "
            "Confirmed at PHC using the rK-39 Rapid Diagnostic Test (RDT) kit. "
            "First-line single-dose treatment is Liposomal Amphotericin B (AmBisome) 10 mg/kg IV infusion administered under medical supervision."
        ),
        "source": "National Center for Vector Borne Diseases Control (NCVBDC) & Bihar Health Department",
        "keywords": ["kala-azar", "leishmaniasis", "fever", "bukhar", "rk39", "spleen", "ambisome", "sandfly", "vector"],
    },
    {
        "doc_id": "PHC-OPS-005",
        "title": "ASHA and ANM Health Operations & Attendance Tracking Protocol",
        "category": "Operations",
        "content": (
            "Accredited Social Health Activists (ASHAs) and Auxiliary Nurse Midwives (ANMs) are the frontline public health agents. "
            "Responsibilities: Mobilizing village health sanitation and nutrition days (VHSND), tracking pregnant women, "
            "conducting home visits for newborn care (HBNC), and maintaining daily attendance. "
            "PHC Supervisors must record attendance daily and flag any worker maintaining less than 75% attendance over 30 days for counselling."
        ),
        "source": "National Rural Health Mission (NRHM) Bihar Guidelines",
        "keywords": ["asha", "anm", "attendance", "haziri", "vhsnd", "hbnc", "phc", "supervisor", "anganwadi", "worker"],
    },
]


def tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into searchable keyword tokens."""
    tokens = re.findall(r"\w+", text.lower())
    stop_words = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "for", "to",
        "of", "by", "with", "ka", "ki", "ke", "hai", "ko", "me", "kya", "aur", "se"
    }
    return [t for t in tokens if t not in stop_words and len(t) > 1]


class MedicalRAG:
    """
    Lightweight, high-performance RAG retriever and context augmentor.
    Uses TF-IDF cosine vector similarity over curated PHC medical knowledge.
    """

    def __init__(self, documents: list[dict] | None = None) -> None:
        raw_docs = documents or PHC_KNOWLEDGE_BASE
        self.documents: list[MedicalDocument] = [MedicalDocument(**doc) for doc in raw_docs]
        self._build_index()

    def _build_index(self) -> None:
        """Compute document token frequencies and inverse document frequencies (IDF)."""
        self.doc_vectors: list[dict[str, float]] = []
        df: Counter = Counter()

        # Build document term frequencies
        doc_tfs: list[Counter] = []
        for doc in self.documents:
            text = f"{doc.title} {doc.category} {doc.content} {' '.join(doc.keywords)}"
            tokens = tokenize(text)
            tf = Counter(tokens)
            doc_tfs.append(tf)
            for token in set(tokens):
                df[token] += 1

        total_docs = len(self.documents)
        self.idf: dict[str, float] = {
            token: math.log((total_docs + 1) / (count + 1)) + 1.0
            for token, count in df.items()
        }

        # Compute TF-IDF normalized vector for each document
        for tf in doc_tfs:
            vec: dict[str, float] = {}
            norm_sq = 0.0
            for token, count in tf.items():
                val = count * self.idf.get(token, 1.0)
                vec[token] = val
                norm_sq += val * val
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            for token in vec:
                vec[token] /= norm
            self.doc_vectors.append(vec)

    def retrieve(self, query: str, top_k: int = 2, min_score: float = 0.08) -> RAGRetrievalResult:
        """
        Retrieve the most relevant medical protocols for a given query.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return RAGRetrievalResult(query=query)

        query_tf = Counter(query_tokens)
        query_vec: dict[str, float] = {}
        norm_sq = 0.0
        for token, count in query_tf.items():
            val = count * self.idf.get(token, 1.0)
            query_vec[token] = val
            norm_sq += val * val
        norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
        for token in query_vec:
            query_vec[token] /= norm

        # Compute cosine similarities
        scores: list[tuple[int, float]] = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            dot = sum(val * doc_vec.get(token, 0.0) for token, val in query_vec.items())
            if dot >= min_score:
                scores.append((idx, round(dot, 4)))

        # Sort by highest similarity
        scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = scores[:top_k]

        matched_docs: list[MedicalDocument] = []
        matched_scores: list[float] = []
        sources: list[str] = []
        context_parts: list[str] = []

        for idx, score in top_matches:
            doc = self.documents[idx]
            matched_docs.append(doc)
            matched_scores.append(score)
            sources.append(f"{doc.title} ({doc.source})")
            context_parts.append(
                f"[Source: {doc.title} | {doc.source}]\n{doc.content}"
            )

        augmented_context = "\n\n".join(context_parts)

        return RAGRetrievalResult(
            query=query,
            documents=matched_docs,
            similarity_scores=matched_scores,
            augmented_context=augmented_context,
            sources=list(set(sources)),
        )

    def generate_grounded_prompt(self, query: str, system_prompt: str = "") -> str:
        """
        Inject retrieved verified medical context into an LLM prompt.
        """
        retrieval = self.retrieve(query)
        if not retrieval.augmented_context:
            return query

        return f"""VERIFIED PHC CLINICAL CONTEXT:
{retrieval.augmented_context}

INSTRUCTIONS:
Answer the following user query strictly using the verified context above.
Include source citations when applicable.

USER QUERY:
{query}"""


# Global singleton instance
rag_engine = MedicalRAG()
