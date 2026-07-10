from fastapi.testclient import TestClient

from app.backend.api.main import app
from app.backend.services.clinical_nlp.extractor import extract_clinical_intake


client = TestClient(app)


def test_chest_pain_note_with_vitals_extracts_expected_fields():
    note = (
        "62-year-old male with chest pain and shortness of breath. "
        "HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy."
    )

    result = extract_clinical_intake(note)

    assert result.age == 62
    assert result.gender == "Male"
    assert result.chief_complaint == "chest pain"
    assert "shortness of breath" in result.symptoms

    assert result.vitals.hr == 118
    assert result.vitals.sbp == 92
    assert result.vitals.dbp == 60
    assert result.vitals.rr is None
    assert result.vitals.o2 == 91
    assert result.vitals.temp == 38.2

    assert "chest pain" in result.safety_cues
    assert "shortness of breath" in result.safety_cues
    assert "low oxygen" in result.safety_cues
    assert "tachycardia" in result.safety_cues
    assert "respiratory rate" in result.missing_fields
    assert result.requires_clinician_review is True


def test_bp_slash_format_is_extracted():
    result = extract_clinical_intake("Patient has BP 92/60 and HR 110.")

    assert result.vitals.sbp == 92
    assert result.vitals.dbp == 60


def test_bp_over_format_is_extracted():
    result = extract_clinical_intake("Blood pressure 92 over 60 with dizziness.")

    assert result.vitals.sbp == 92
    assert result.vitals.dbp == 60


def test_oxygen_percent_format_is_extracted():
    result = extract_clinical_intake("O2 91% on arrival.")

    assert result.vitals.o2 == 91
    assert "low oxygen" in result.safety_cues


def test_oxygen_saturation_format_is_extracted():
    result = extract_clinical_intake("oxygen saturation 91 on arrival.")

    assert result.vitals.o2 == 91
    assert "low oxygen" in result.safety_cues


def test_missing_respiratory_rate_is_reported():
    result = extract_clinical_intake("HR 88, BP 120/80, O2 98%, temp 37.0.")

    assert result.vitals.rr is None
    assert "respiratory rate" in result.missing_fields


def test_mental_health_cue_suicidal_ideation_is_detected():
    result = extract_clinical_intake("Patient reports suicidal ideation.")

    assert "suicidal ideation" in result.symptoms
    assert "suicidal ideation" in result.safety_cues
    assert result.requires_clinician_review is True


def test_pregnancy_and_abdominal_pain_safety_cue_is_detected():
    result = extract_clinical_intake("Pregnant patient with abdominal pain.")

    assert "pregnancy" in result.symptoms
    assert "abdominal pain" in result.symptoms
    assert "pregnancy + abdominal pain" in result.safety_cues


def test_empty_note_returns_validation_error_from_api():
    response = client.post("/nlp/extract-intake", json={"note_text": ""})

    assert response.status_code == 422


def test_response_does_not_include_diagnosis_or_treatment_fields():
    response = client.post(
        "/nlp/extract-intake",
        json={"note_text": "62-year-old male with chest pain. HR 118, BP 92/60."},
    )

    assert response.status_code == 200

    payload = response.json()

    assert "diagnosis" not in payload
    assert "treatment" not in payload
    assert "treatment_recommendation" not in payload
    assert "final_esi" not in payload
    assert "predicted_esi" not in payload


def test_requires_clinician_review_is_always_true():
    response = client.post(
        "/nlp/extract-intake",
        json={"note_text": "Patient reports headache. HR 80."},
    )

    assert response.status_code == 200
    assert response.json()["requires_clinician_review"] is True