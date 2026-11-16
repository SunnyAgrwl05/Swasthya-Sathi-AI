from hallucination_detector import MedicalHallucinationDetector, detector


def test_non_medical_query():
    res = detector.audit_response(
        query="What is the capital of Bihar?",
        response="The capital of Bihar is Patna.",
        language="en",
    )
    assert not res.is_medical
    assert res.confidence_score == 1.0
    assert not res.is_flagged
    assert not res.requires_human_review
    assert res.disclaimer is None


def test_grounded_phc_medical_guidance():
    query = "Bacche ko dast aur ulti hai, kya karein?"
    response = (
        "Bacche ko ORS ka ghol dein aur zinc tablet dein dehydration se bachane ke liye. "
        "Yadi sthiti gambhir ho to turant PHC par doctor se consult karein."
    )
    res = detector.audit_response(query=query, response=response, language="hi")
    assert res.is_medical
    assert res.confidence_score >= 0.80
    assert "ors" in res.grounded_entities
    assert "zinc" in res.grounded_entities
    assert res.risk_level == "low"
    assert not res.requires_human_review


def test_detect_miracle_cure_hallucination():
    query = "Dast ka turant ilaj batao"
    response = (
        "Dast ke liye yeh chamatkari ilaj hai aur miracle cure hai jo 100% guaranteed cure karta hai."
    )
    res = detector.audit_response(query=query, response=response, language="hi")
    assert res.is_medical
    assert res.is_flagged
    assert res.confidence_score < 0.75
    assert any("phrasing detected" in r for r in res.flagged_reasons)
    assert res.disclaimer is not None
    assert "स्वास्थ्य सूचना" in res.annotated_response


def test_detect_dangerous_prescription_dosage():
    query = "Bukhar ke liye dawai ka dose batao"
    response = (
        "Take 500 mg amoxicillin antibiotics twice daily for 5 days. Do not go to hospital."
    )
    res = detector.audit_response(query=query, response=response, language="en")
    assert res.is_medical
    assert res.requires_human_review
    assert res.risk_level == "critical"
    assert res.is_flagged
    assert any("prescription/dosage claim" in r for r in res.flagged_reasons)
    assert "Medical Notice" in res.annotated_response


def test_configurable_threshold():
    custom_detector = MedicalHallucinationDetector(min_confidence_threshold=0.98)
    query = "Fever treatment"
    response = "Drink warm fluids and rest. Visit the primary health centre if fever persists."
    res = custom_detector.audit_response(query=query, response=response, language="en")
    assert res.is_medical
    # With a very high threshold of 0.98, it should flag for verification
    assert res.is_flagged


def test_english_disclaimer():
    query = "How to treat severe dehydration?"
    response = "Use oral rehydration salts and seek medical care."
    res = detector.audit_response(query=query, response=response, language="en")
    assert res.disclaimer is not None
    assert "Medical Notice" in res.disclaimer
