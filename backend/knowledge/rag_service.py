"""
Retrieval-Augmented Generation (RAG) Service for Swasthya Sathi AI
-------------------------------------------------------------------
Loads, chunks, and indexes verified Indian public health guidelines
(Immunization, Maternal & Child Health, ASHA/ANM protocols, IMNCI)
and provides fast, grounded vector retrieval for AI operations.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_title: str
    section_title: str
    content: str
    source_file: str
    tokens: list[str]


STOPWORDS = {
    # English
    "in", "and", "the", "for", "of", "to", "at", "a", "an", "is", "on", "as",
    "or", "by", "with", "from", "it", "its", "are", "be", "this", "that", "all",
    "any", "can", "may", "has", "have", "had", "under", "per", "into",
    # Hindi / Hinglish stopwords
    "ka", "ki", "ke", "ko", "me", "mein", "hai", "hain", "se", "aur", "ye",
    "yeh", "par", "kya", "karein", "karo", "kab", "kisko", "kahan", "kaise",
    "bhi", "wala", "wali", "wale", "diya", "hona", "chahiye",
}

HEALTH_SYNONYMS: dict[str, list[str]] = {
    "teeka": ["vaccine", "immunization", "tika", "teekakaran"],
    "teekakaran": ["vaccine", "immunization", "schedule", "uip"],
    "vaccine": ["teeka", "immunization", "schedule", "injection"],
    "tika": ["vaccine", "immunization", "teeka"],
    "pentavalent": ["pentavalent", "dtp", "hib", "6 weeks"],
    "bcg": ["bcg", "tuberculosis", "birth", "scar"],
    "polio": ["opv", "ipv", "fipv", "polio", "drops"],
    "rotavirus": ["rotavirus", "rvv", "diarrhea", "drops"],
    "measles": ["mr", "rubella", "measles", "9 months"],
    "garbhwati": ["pregnant", "pregnancy", "anc", "maternal", "trimester"],
    "garbh": ["pregnancy", "maternal", "anc"],
    "anc": ["antenatal", "checkup", "trimester", "pmsma", "pregnancy"],
    "ifa": ["iron", "folic acid", "tablets", "anemia", "supplementation"],
    "iron": ["ifa", "folic acid", "anemia", "hemoglobin"],
    "dast": ["diarrhea", "loose motion", "ors", "zinc", "dehydration"],
    "diarrhea": ["dast", "ors", "zinc", "dehydration", "loose stool"],
    "ors": ["oral rehydration", "packet", "dast", "diarrhea", "1 liter"],
    "zinc": ["zinc", "14 days", "diarrhea", "dast", "supplementation"],
    "asha": ["asha", "field worker", "vhsnd", "hbnc", "incentive"],
    "anm": ["anm", "auxiliary nurse", "vhsnd", "sub-center", "phc"],
    "vhsnd": ["village health", "session", "anganwadi", "nutrition day"],
    "pneumonia": ["breathing", "fast breathing", "respiratory", "chest indrawing", "ari"],
    "khansi": ["cough", "cold", "pneumonia", "breathing"],
}


def _tokenize(text: str) -> list[str]:
    """Tokenizes text into meaningful words, filtering out common stopwords."""
    cleaned = re.sub(r"[^\w\s\u0900-\u097F]", " ", text.lower())
    tokens = [
        t.strip()
        for t in cleaned.split()
        if len(t.strip()) > 1 and t.strip() not in STOPWORDS
    ]
    return tokens


class HealthKnowledgeBase:
    """In-memory vector and TF-IDF retrieval engine for public health guidelines."""

    def __init__(self, guidelines_dir: Path | str | None = None):
        if guidelines_dir is None:
            base_dir = Path(__file__).resolve().parent
            guidelines_dir = base_dir / "guidelines"
        self.guidelines_dir = Path(guidelines_dir)
        self.chunks: list[KnowledgeChunk] = []
        self.doc_frequencies: dict[str, int] = {}
        self.total_docs: int = 0
        self._is_indexed: bool = False
        self.load_and_index()

    def load_and_index(self) -> None:
        """Parses markdown guidelines into semantic chunks and builds index."""
        if not self.guidelines_dir.exists():
            return

        self.chunks = []
        self.doc_frequencies = {}

        for file_path in sorted(self.guidelines_dir.glob("*.md")):
            try:
                content = file_path.read_text(encoding="utf-8")
                doc_title = self._extract_title(content, file_path.stem)
                sections = self._split_sections(content)

                for idx, (section_title, section_text) in enumerate(sections):
                    chunk_id = f"{file_path.stem}_{idx}"
                    full_text = f"{doc_title}\n{section_title}\n{section_text}"
                    tokens = _tokenize(full_text)

                    chunk = KnowledgeChunk(
                        chunk_id=chunk_id,
                        document_title=doc_title,
                        section_title=section_title,
                        content=section_text.strip(),
                        source_file=file_path.name,
                        tokens=tokens,
                    )
                    self.chunks.append(chunk)
            except Exception as e:
                print(f"[RAG] Error loading {file_path}: {e}")

        self.total_docs = len(self.chunks)
        for chunk in self.chunks:
            unique_terms = set(chunk.tokens)
            for term in unique_terms:
                self.doc_frequencies[term] = self.doc_frequencies.get(term, 0) + 1

        self._is_indexed = True

    def _extract_title(self, content: str, default: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return default.replace("_", " ").title()

    def _split_sections(self, content: str) -> list[tuple[str, str]]:
        """Splits markdown on '## ' and '### ' headers for fine-grained chunking."""
        lines = content.splitlines()
        sections: list[tuple[str, str]] = []
        current_h2 = "Overview"
        current_title = "Overview"
        current_lines: list[str] = []

        for line in lines:
            if line.startswith("## "):
                if current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.append((current_title, text))
                current_h2 = line[3:].strip()
                current_title = current_h2
                current_lines = [line]
            elif line.startswith("### "):
                if current_lines:
                    text = "\n".join(current_lines).strip()
                    if text:
                        sections.append((current_title, text))
                sub_title = line[4:].strip()
                current_title = f"{current_h2} — {sub_title}"
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            text = "\n".join(current_lines).strip()
            if text:
                sections.append((current_title, text))

        return sections

    def _compute_idf(self, term: str) -> float:
        df = self.doc_frequencies.get(term, 0)
        if df == 0:
            return 0.0
        return math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Retrieves the top-k most relevant guideline chunks for a given query.
        Returns empty list if no chunks have significant token overlap.
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        # Expand query with clinical/bilingual synonyms
        expanded_terms = set(query_tokens)
        for token in query_tokens:
            if token in HEALTH_SYNONYMS:
                for syn in HEALTH_SYNONYMS[token]:
                    for syn_t in _tokenize(syn):
                        expanded_terms.add(syn_t)

        scores: list[tuple[float, KnowledgeChunk]] = []

        for chunk in self.chunks:
            chunk_token_set = set(chunk.tokens)
            matched_terms = expanded_terms.intersection(chunk_token_set)

            if not matched_terms:
                continue

            score = 0.0
            section_lower = chunk.section_title.lower()
            doc_lower = chunk.document_title.lower()
            content_lower = chunk.content.lower()

            for term in matched_terms:
                tf = chunk.tokens.count(term) / len(chunk.tokens)
                idf = self._compute_idf(term)

                # Relevance multipliers
                boost = 1.0
                if term in section_lower:
                    boost += 3.0
                if term in doc_lower:
                    boost += 1.5
                if term in query_tokens:  # Direct user word match
                    boost += 2.0

                score += (tf * idf) * boost

            # Extra exact phrase / n-gram match bonus
            for token in query_tokens:
                if token in content_lower:
                    score += 0.05
                if token in section_lower:
                    score += 0.15

            if score > 0.01:
                scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_results = scores[:top_k]

        return [
            {
                "chunk_id": chunk.chunk_id,
                "document_title": chunk.document_title,
                "section_title": chunk.section_title,
                "content": chunk.content,
                "source_file": chunk.source_file,
                "relevance_score": round(score, 4),
            }
            for score, chunk in top_results
        ]

    def get_formatted_context(self, query: str, top_k: int = 2) -> str:
        """Returns clean markdown formatted context block to ground LLM generations."""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        context_blocks = []
        for i, res in enumerate(results, start=1):
            context_blocks.append(
                f"### [Verified Protocol {i}] {res['document_title']} — {res['section_title']}\n"
                f"{res['content']}\n"
                f"*(Source: {res['source_file']})*"
            )

        return "\n\n".join(context_blocks)


_knowledge_base_instance: HealthKnowledgeBase | None = None


def get_health_knowledge_base() -> HealthKnowledgeBase:
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        _knowledge_base_instance = HealthKnowledgeBase()
    return _knowledge_base_instance
