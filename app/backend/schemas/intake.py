"""Structured patient intake request schemas."""

from typing import Any

from pydantic import BaseModel, Field


class NlpEvidenceItem(BaseModel):
    field: str
    value: int | float | str | list[str] | None
    text: str


class NlpExtractionAudit(BaseModel):
    reviewed: bool = False
    source: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    safety_cues: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    evidence: list[NlpEvidenceItem] = Field(default_factory=list)
    disclaimer: str


class PatientIntakeRequest(BaseModel):
    patient_name: str | None = None
    mrn: str | None = None
    patient_age: int = Field(..., ge=0, le=120)
    sex: str | None = None
    chief_complaint: str = Field(..., min_length=3)
    symptom_duration: str | None = None
    pain_score: int | None = Field(default=None, ge=0, le=10)
    temperature_c: float | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    oxygen_saturation: float | None = Field(default=None, ge=0, le=100)
    consciousness_level: str | None = None
    pregnancy: bool | None = None
    arrival_mode: str | None = None
    additional_context: str | None = None
    nlp_extraction_audit: NlpExtractionAudit | None = None
