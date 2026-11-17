from fastapi.testclient import TestClient

from knowledge.rag_service import get_health_knowledge_base
from main import app
from agent import consult_medical_guidelines

client = TestClient(app)


def test_knowledge_base_indexing():
    """Verify that guideline documents are indexed into chunks."""
    kb = get_health_knowledge_base()
    assert kb.total_docs > 0
    assert len(kb.chunks) >= 4
    files = {c.source_file for c in kb.chunks}
    assert "immunization_schedule.md" in files
    assert "maternal_child_health.md" in files
    assert "childhood_illness_imnci.md" in files
    assert "asha_anm_field_protocols.md" in files


def test_rag_immunization_query():
    """Verify retrieval of Pentavalent and 6-week infant immunization."""
    kb = get_health_knowledge_base()
    results = kb.search("pentavalent 6 weeks teeka", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "immunization_schedule.md" in top["source_file"]
    content_lower = top["content"].lower()
    assert "pentavalent" in content_lower or "6 weeks" in content_lower


def test_rag_maternal_anc_query():
    """Verify retrieval of maternal ANC and IFA supplementation."""
    kb = get_health_knowledge_base()
    results = kb.search("garbhwati mahila anc checkup ifa tablets", top_k=3)
    assert len(results) > 0
    sources = [r["source_file"] for r in results]
    assert "maternal_child_health.md" in sources


def test_rag_diarrhea_ors_zinc():
    """Verify retrieval of ORS and Zinc diarrhea protocol."""
    kb = get_health_knowledge_base()
    results = kb.search("dast loose motion ors zinc", top_k=3)
    assert len(results) > 0
    assert "childhood_illness_imnci.md" in results[0]["source_file"]
    assert "ors" in results[0]["content"].lower()


def test_consult_medical_guidelines_tool():
    """Verify that the agent tool returns structured markdown guidance."""
    output = consult_medical_guidelines("BCG vaccine at birth")
    assert "📖" in output
    assert "BCG" in output or "birth" in output.lower()


def test_consult_medical_guidelines_unknown_topic():
    """Verify safe fallback when topic has no matches."""
    output = consult_medical_guidelines("quantum computing in space")
    assert "Medical Officer" in output


def test_api_knowledge_search_endpoint():
    """Verify GET /api/knowledge/search endpoint."""
    response = client.get("/api/knowledge/search?q=pentavalent")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert "document_title" in data["results"][0]


def test_api_knowledge_search_empty_query():
    """Verify GET /api/knowledge/search with empty query returns empty results."""
    response = client.get("/api/knowledge/search?q=")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
