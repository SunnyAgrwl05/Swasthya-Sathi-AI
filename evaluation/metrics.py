"""
Evaluation Metrics for AI Medical Response Quality
--------------------------------------------------
Swasthya Sathi AI - Bihar Health Department PHC Network

Computes quantitative benchmarks across:
1. Clinical Accuracy (Presence of verified protocols, penalty for forbidden claims)
2. Semantic Relevance (Alignment with user query)
3. Information Completeness (Coverage of gold-standard reference points)
4. Response Consistency (Pairwise stability across perturbations)
5. Response Latency Scoring (Execution speed penalty curve)
"""

from __future__ import annotations

import re


def _tokenize(text: str) -> set[str]:
    """Extract lowercase alphanumeric tokens."""
    tokens = re.findall(r"\w+", text.lower())
    stop_words = {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "in", "for", "to",
        "of", "by", "with", "ka", "ki", "ke", "hai", "ko", "me", "kya", "aur", "se", "hain"
    }
    return {t for t in tokens if t not in stop_words and len(t) > 1}


def calculate_relevance_score(query: str, response: str) -> float:
    """
    Computes semantic query-response token overlap relevance (0.0 to 1.0).
    """
    query_tokens = _tokenize(query)
    response_tokens = _tokenize(response)

    if not query_tokens or not response_tokens:
        return 0.0

    overlap = query_tokens.intersection(response_tokens)
    score = len(overlap) / len(query_tokens)
    return round(min(1.0, score), 3)


def calculate_clinical_accuracy_score(
    response: str,
    key_entities: list[str],
    forbidden_claims: list[str] | None = None,
) -> float:
    """
    Measures presence of required clinical concepts and penalizes forbidden claims.
    Score: 0.0 to 1.0
    """
    resp_lower = response.lower()

    if not key_entities:
        return 1.0

    # Entity presence check
    matched_entities = sum(1 for entity in key_entities if entity.lower() in resp_lower)
    base_score = matched_entities / len(key_entities)

    # Forbidden claim penalty
    penalty = 0.0
    if forbidden_claims:
        for claim in forbidden_claims:
            if claim.lower() in resp_lower:
                penalty += 0.35

    final_score = max(0.0, base_score - penalty)
    return round(min(1.0, final_score), 3)


def calculate_completeness_score(
    response: str,
    reference_answer: str,
    key_entities: list[str],
) -> float:
    """
    Evaluates whether all essential clinical guidelines from the reference are covered.
    Score: 0.0 to 1.0
    """
    resp_tokens = _tokenize(response)
    ref_tokens = _tokenize(reference_answer)

    if not ref_tokens:
        return 1.0

    token_coverage = len(resp_tokens.intersection(ref_tokens)) / len(ref_tokens)
    resp_lower = response.lower()
    entity_coverage = (
        sum(1 for ent in key_entities if ent.lower() in resp_lower) / len(key_entities)
        if key_entities else 1.0
    )

    combined = 0.5 * token_coverage + 0.5 * entity_coverage
    return round(min(1.0, combined), 3)


def calculate_consistency_score(responses: list[str]) -> float:
    """
    Evaluates consistency across multiple responses for the same scenario.
    Score: 0.0 to 1.0
    """
    if len(responses) < 2:
        return 1.0

    token_sets = [_tokenize(r) for r in responses]
    jaccards: list[float] = []

    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            union = token_sets[i].union(token_sets[j])
            if not union:
                continue
            inter = token_sets[i].intersection(token_sets[j])
            jaccards.append(len(inter) / len(union))

    return round(sum(jaccards) / len(jaccards), 3) if jaccards else 1.0


def calculate_latency_score(latency_ms: float, target_latency_ms: float = 1500.0) -> float:
    """
    Scores latency performance. Scores 1.0 for responses <= target_latency_ms,
    gracefully decaying for slower responses.
    """
    if latency_ms <= target_latency_ms:
        return 1.0
    if latency_ms >= 5000.0:
        return 0.2
    decay = 1.0 - ((latency_ms - target_latency_ms) / 3500.0) * 0.8
    return round(max(0.2, decay), 3)


def compute_composite_quality_score(
    accuracy: float,
    relevance: float,
    completeness: float,
    latency_score: float,
) -> float:
    """
    Computes weighted quality score on a 0 - 100 scale.
    Weights: Accuracy 40%, Relevance 25%, Completeness 25%, Latency 10%.
    """
    composite = (
        0.40 * accuracy +
        0.25 * relevance +
        0.25 * completeness +
        0.10 * latency_score
    ) * 100.0
    return round(composite, 2)
