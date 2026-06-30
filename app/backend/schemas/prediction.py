"""ESI prediction response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class ESIProbability(BaseModel):
    esi_level: int = Field(..., ge=1, le=5)
    probability: float = Field(..., ge=0, le=1)


class SafetyRuleResult(BaseModel):
    rule_id: str
    triggered: bool
    message: str
    is_placeholder: bool = True


class ESIPredictionResponse(BaseModel):
    request_id: str
    assessment_id: str | None = None
    acuity_scale: Literal["ESI"] = "ESI"
    model_version: str | None = None
    model_loaded: bool
    predicted_esi: int | None = Field(default=None, ge=1, le=5)
    final_esi: int | None = Field(default=None, ge=1, le=5)
    confidence_score: float | None = Field(default=None, ge=0, le=1)
    probabilities: dict[str, float]
    safety_rules_triggered: list[SafetyRuleResult]
    final_source: str
    recommendation: str
    explanation: str
    clinician_summary: str
    is_placeholder: bool
    disclaimer: str
