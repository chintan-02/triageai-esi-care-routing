from pydantic import BaseModel, Field


class IntakeVitals(BaseModel):
    hr: int | None = None
    sbp: int | None = None
    dbp: int | None = None
    rr: int | None = None
    o2: int | None = None
    temp: float | None = None


class IntakeEvidence(BaseModel):
    field: str
    value: int | float | str | list[str] | None
    text: str


class ClinicalIntakeExtractionRequest(BaseModel):
    note_text: str = Field(min_length=1, max_length=10000)


class ClinicalIntakeExtractionResponse(BaseModel):
    age: int | None = None
    gender: str | None = None
    chief_complaint: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    vitals: IntakeVitals = Field(default_factory=IntakeVitals)
    safety_cues: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    evidence: list[IntakeEvidence] = Field(default_factory=list)
    requires_clinician_review: bool = True
    disclaimer: str = (
        "Decision support only. Extracted fields require clinician review before prediction."
    )