"""Assessment persistence schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

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


class AssessmentPredictionDetail(BaseModel):
    prediction_id: str
    model_version: str | None = None
    model_loaded: bool
    predicted_esi: int | None = Field(default=None, ge=1, le=5)
    final_esi: int | None = Field(default=None, ge=1, le=5)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    probabilities: dict[str, float] = Field(default_factory=dict)
    safety_rules_triggered: list[dict[str, Any]] = Field(default_factory=list)
    final_source: str
    recommendation: str
    explanation: str
    clinician_summary: str
    is_placeholder: bool
    created_at: datetime | None = None


class AssessmentClinicianReviewDetail(BaseModel):
    review_id: str
    clinician_id: str
    clinician_decision: str
    clinician_final_esi: int | None = Field(default=None, ge=1, le=5)
    override_reason: str | None = None
    review_note: str | None = None
    reviewed: bool
    created_at: datetime | None = None


class AssessmentAuditEvent(BaseModel):
    audit_id: str
    actor_id: str | None = None
    action: str
    details: dict[str, Any] | None = None
    created_at: datetime | None = None
    event_type: str | None = None
    message: str | None = None
    actor: str | None = None
    timestamp: datetime | None = None


class AssessmentListItem(BaseModel):
    assessment_id: str
    patient_id: str | None = None
    patient_name: str | None = None
    mrn: str | None = None
    age: int | None = None
    sex: str | None = None
    arrival_mode: str | None = None
    chief_complaint: str | None = None
    symptom_narrative: str | None = None
    final_esi: int | None = Field(default=None, ge=1, le=5)
    model_predicted_esi: int | None = Field(default=None, ge=1, le=5)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    latency_ms: int | None = None
    safety_escalated: bool = False
    safety_gate_status: str | None = None
    status: str | None = None
    review_status: str | None = None
    review_status_normalized: str | None = None
    reviewer: str | None = None
    reviewer_role: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AssessmentAuditTrailResponse(BaseModel):
    assessment_id: str
    events: list[AssessmentAuditEvent] = Field(default_factory=list)


class AssessmentDetailResponse(BaseModel):
    request_id: str
    assessment_id: str
    patient_id: str | None = None
    patient_name: str | None = None
    mrn: str | None = None
    age: int | None = None
    sex: str | None = None
    status: str
    chief_complaint: str | None = None
    symptom_duration: str | None = None
    symptom_narrative: str | None = None
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
    vitals: dict[str, Any] = Field(default_factory=dict)
    risk_flags: list[str] = Field(default_factory=list)
    comorbidities: list[str] = Field(default_factory=list)
    final_esi: int | None = Field(default=None, ge=1, le=5)
    model_predicted_esi: int | None = Field(default=None, ge=1, le=5)
    safety_escalated: bool = False
    safety_gate_status: str | None = None
    probabilities: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    latency_ms: int | None = None
    model_version: str | None = None
    request_id_value: str | None = None
    review_status: str | None = None
    review_status_normalized: str | None = None
    reviewer: str | None = None
    reviewer_role: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    intake: PatientIntakeRequest | None = None
    latest_prediction: AssessmentPredictionDetail | None = None
    latest_clinician_review: AssessmentClinicianReviewDetail | None = None
    audit_trail: list[AssessmentAuditEvent] = Field(default_factory=list)
    report_ids: list[str] = Field(default_factory=list)
    message: str
    is_placeholder: bool
