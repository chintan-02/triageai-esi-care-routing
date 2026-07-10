from app.backend.schemas.nlp import (
    ClinicalIntakeExtractionResponse,
    IntakeEvidence,
    IntakeVitals,
)

from .patterns import (
    AGE_PATTERNS,
    BP_PATTERNS,
    COMPLAINT_PATTERNS,
    GENDER_PATTERNS,
    HR_PATTERNS,
    OXYGEN_PATTERNS,
    RR_PATTERNS,
    TEMP_PATTERNS,
)


DISCLAIMER = "Decision support only. Extracted fields require clinician review before prediction."


def _normalize_gender(raw_gender: str) -> str:
    value = raw_gender.strip().lower()

    if value in {"m", "male", "man"}:
        return "Male"

    if value in {"f", "female", "woman"}:
        return "Female"

    return raw_gender.strip().title()


def _add_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _extract_age(note: str, evidence: list[IntakeEvidence]) -> int | None:
    for pattern in AGE_PATTERNS:
        match = pattern.search(note)
        if match:
            age = int(match.group("age"))
            evidence.append(
                IntakeEvidence(field="age", value=age, text=match.group(0))
            )
            return age

    return None


def _extract_gender(note: str, evidence: list[IntakeEvidence]) -> str | None:
    for pattern in GENDER_PATTERNS:
        match = pattern.search(note)
        if match:
            gender = _normalize_gender(match.group("gender"))
            evidence.append(
                IntakeEvidence(field="gender", value=gender, text=match.group(0))
            )
            return gender

    return None


def _extract_hr(note: str, evidence: list[IntakeEvidence]) -> int | None:
    for pattern in HR_PATTERNS:
        match = pattern.search(note)
        if match:
            hr = int(match.group("hr"))
            evidence.append(
                IntakeEvidence(field="triage_vital_hr", value=hr, text=match.group(0))
            )
            return hr

    return None


def _extract_bp(note: str, evidence: list[IntakeEvidence]) -> tuple[int | None, int | None]:
    for pattern in BP_PATTERNS:
        match = pattern.search(note)
        if match:
            sbp = int(match.group("sbp"))
            dbp = int(match.group("dbp"))
            raw_text = match.group(0)

            evidence.append(
                IntakeEvidence(field="triage_vital_sbp", value=sbp, text=raw_text)
            )
            evidence.append(
                IntakeEvidence(field="triage_vital_dbp", value=dbp, text=raw_text)
            )
            return sbp, dbp

    return None, None


def _extract_rr(note: str, evidence: list[IntakeEvidence]) -> int | None:
    for pattern in RR_PATTERNS:
        match = pattern.search(note)
        if match:
            rr = int(match.group("rr"))
            evidence.append(
                IntakeEvidence(field="triage_vital_rr", value=rr, text=match.group(0))
            )
            return rr

    return None


def _extract_o2(note: str, evidence: list[IntakeEvidence]) -> int | None:
    for pattern in OXYGEN_PATTERNS:
        match = pattern.search(note)
        if match:
            o2 = int(match.group("o2"))
            evidence.append(
                IntakeEvidence(field="triage_vital_o2", value=o2, text=match.group(0))
            )
            return o2

    return None


def _extract_temp(note: str, evidence: list[IntakeEvidence]) -> float | None:
    for pattern in TEMP_PATTERNS:
        match = pattern.search(note)
        if match:
            temp = float(match.group("temp"))
            evidence.append(
                IntakeEvidence(field="triage_vital_temp", value=temp, text=match.group(0))
            )
            return temp

    return None


def _extract_symptoms_and_complaint(
    note: str,
    evidence: list[IntakeEvidence],
) -> tuple[str | None, list[str]]:
    symptoms: list[str] = []
    chief_complaint: str | None = None

    for label, patterns in COMPLAINT_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(note)
            if not match:
                continue

            _add_unique(symptoms, label)

            evidence.append(
                IntakeEvidence(
                    field="symptom",
                    value=label,
                    text=match.group(0),
                )
            )

            if chief_complaint is None and label not in {"pregnancy", "fever"}:
                chief_complaint = label

            break

    return chief_complaint, symptoms


def _detect_safety_cues(
    *,
    age: int | None,
    symptoms: list[str],
    vitals: IntakeVitals,
) -> list[str]:
    cues: list[str] = []

    if "chest pain" in symptoms:
        _add_unique(cues, "chest pain")

    if "shortness of breath" in symptoms:
        _add_unique(cues, "shortness of breath")

    if vitals.o2 is not None and vitals.o2 <= 92:
        _add_unique(cues, "low oxygen")

    if vitals.sbp is not None and vitals.sbp <= 90:
        _add_unique(cues, "low blood pressure")

    if vitals.hr is not None and vitals.hr >= 110:
        _add_unique(cues, "tachycardia")

    if "stroke symptoms" in symptoms:
        _add_unique(cues, "stroke symptoms")

    if "unresponsive" in symptoms:
        _add_unique(cues, "unresponsive")

    if "seizure" in symptoms:
        _add_unique(cues, "seizure")

    if "suicidal ideation" in symptoms:
        _add_unique(cues, "suicidal ideation")

    if "pregnancy" in symptoms and "abdominal pain" in symptoms:
        _add_unique(cues, "pregnancy + abdominal pain")

    if "severe trauma" in symptoms:
        _add_unique(cues, "severe trauma")

    if age is not None and age >= 65 and "fever" in symptoms:
        _add_unique(cues, "fever in elderly")

    return cues


def _detect_missing_fields(vitals: IntakeVitals) -> list[str]:
    missing: list[str] = []

    if vitals.rr is None:
        missing.append("respiratory rate")

    if vitals.o2 is None:
        missing.append("oxygen saturation")

    if vitals.sbp is None or vitals.dbp is None:
        missing.append("blood pressure")

    if vitals.hr is None:
        missing.append("heart rate")

    if vitals.temp is None:
        missing.append("temperature")

    return missing


def extract_clinical_intake(note_text: str) -> ClinicalIntakeExtractionResponse:
    note = note_text.strip()
    evidence: list[IntakeEvidence] = []

    age = _extract_age(note, evidence)
    gender = _extract_gender(note, evidence)

    chief_complaint, symptoms = _extract_symptoms_and_complaint(note, evidence)

    hr = _extract_hr(note, evidence)
    sbp, dbp = _extract_bp(note, evidence)
    rr = _extract_rr(note, evidence)
    o2 = _extract_o2(note, evidence)
    temp = _extract_temp(note, evidence)

    vitals = IntakeVitals(
        hr=hr,
        sbp=sbp,
        dbp=dbp,
        rr=rr,
        o2=o2,
        temp=temp,
    )

    safety_cues = _detect_safety_cues(
        age=age,
        symptoms=symptoms,
        vitals=vitals,
    )

    missing_fields = _detect_missing_fields(vitals)

    return ClinicalIntakeExtractionResponse(
        age=age,
        gender=gender,
        chief_complaint=chief_complaint,
        symptoms=symptoms,
        vitals=vitals,
        safety_cues=safety_cues,
        missing_fields=missing_fields,
        evidence=evidence,
        requires_clinician_review=True,
        disclaimer=DISCLAIMER,
    )