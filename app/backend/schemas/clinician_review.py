"""Clinician review schemas."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ClinicianReviewRequest(BaseModel):
    assessment_id: str
    clinician_id: str
    action: Literal["accept", "override", "needs_review"]
    final_esi: int | None = Field(default=None, ge=1, le=5)
    override_reason: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def require_override_reason_for_override(self) -> "ClinicianReviewRequest":
        if self.action == "override" and self.final_esi is not None and not self.override_reason:
            raise ValueError("override_reason is required when overriding final_esi")
        return self


class ClinicianReviewResponse(BaseModel):
    review_id: str
    assessment_id: str
    status: str
    message: str
    is_placeholder: bool
