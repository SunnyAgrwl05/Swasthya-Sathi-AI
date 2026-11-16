from rag import MedicalRAG, rag_engine


def test_rag_retrieves_diarrhea_protocol():
    result = rag_engine.retrieve("Bacche ko dast aur ulti hai ORS kaise dein?")
    assert len(result.documents) > 0
    doc_ids = [d.doc_id for d in result.documents]
    assert "PHC-DIA-003" in doc_ids
    assert "ORS" in result.augmented_context
    assert any("IMNCI" in s for s in result.sources)


def test_rag_retrieves_immunization_protocol():
    result = rag_engine.retrieve("Birth par kaun se vaccine lagte hain?")
    assert len(result.documents) > 0
    doc_ids = [d.doc_id for d in result.documents]
    assert "PHC-IMM-002" in doc_ids
    assert "BCG" in result.augmented_context


def test_rag_retrieves_maternal_anc_protocol():
    result = rag_engine.retrieve("Garbhawastha me kitne ANC checkup aur IFA tablets zaroori hain?")
    assert len(result.documents) > 0
    doc_ids = [d.doc_id for d in result.documents]
    assert "PHC-MAT-001" in doc_ids
    assert "180" in result.augmented_context


def test_rag_retrieves_kala_azar_protocol():
    result = rag_engine.retrieve("15 din se bukhar hai aur spleen badh gaya hai, Kala-azar test kaise karein?")
    assert len(result.documents) > 0
    doc_ids = [d.doc_id for d in result.documents]
    assert "PHC-KALA-004" in doc_ids
    assert "rK-39" in result.augmented_context


def test_rag_empty_or_irrelevant_query():
    result = rag_engine.retrieve("What is python programming language?")
    assert len(result.documents) == 0
    assert result.augmented_context == ""


def test_generate_grounded_prompt():
    prompt = rag_engine.generate_grounded_prompt("ORS preparation guide")
    assert "VERIFIED PHC CLINICAL CONTEXT:" in prompt
    assert "USER QUERY:" in prompt
    assert "ORS" in prompt


def test_custom_rag_indexing():
    custom_docs = [
        {
            "doc_id": "TEST-001",
            "title": "Custom Test Disease",
            "category": "Testing",
            "content": "Special cure procedure for test infection.",
            "source": "Test Source",
            "keywords": ["test", "infection"],
        }
    ]
    engine = MedicalRAG(documents=custom_docs)
    res = engine.retrieve("How to treat test infection?")
    assert len(res.documents) == 1
    assert res.documents[0].doc_id == "TEST-001"
