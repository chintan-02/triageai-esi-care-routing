"""Structured patient intake request schemas."""

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


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
    evidence: list[NlpEvidenceItem] = Field(default_factory=list, max_length=100)
    disclaimer: str


class PatientIntakeRequest(BaseModel):
    model_config = ConfigDict(str_max_length=10000)
    patient_name: str | None = Field(default=None, max_length=128)
    mrn: str | None = Field(default=None, max_length=64)
    patient_age: int = Field(..., ge=0, le=120)
    sex: str | None = None
    chief_complaint: str = Field(..., min_length=3, max_length=1000)
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
    risk_flags: list[Annotated[str, Field(max_length=128)]] | None = Field(default=None, max_length=32)
    comorbidities: list[Annotated[str, Field(max_length=128)]] | None = Field(default=None, max_length=32)
    nlp_extraction_audit: NlpExtractionAudit | None = None
