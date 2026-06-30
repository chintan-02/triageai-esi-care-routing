"""Assessment persistence schemas."""

from datetime import datetime

from pydantic import BaseModel

from app.backend.schemas.intake import PatientIntakeRequest


class AssessmentCreateResponse(BaseModel):
    request_id: str
    assessment_id: str
    patient_id: str | None = None
    status: str
    created_at: datetime | None = None
    intake: PatientIntakeRequest | None = None
    message: str
    is_placeholder: bool


class AssessmentDetailResponse(BaseModel):
    request_id: str
    assessment_id: str
    patient_id: str | None = None
    status: str
    chief_complaint: str | None = None
    symptom_duration: str | None = None
    pain_score: int | None = None
    temperature_c: float | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    oxygen_saturation: float | None = None
    consciousness_level: str | None = None
    pregnancy: bool | None = None
    arrival_mode: str | None = None
    additional_context: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    intake: PatientIntakeRequest | None = None
    message: str
    is_placeholder: bool
