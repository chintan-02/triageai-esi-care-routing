"""Clinician review schemas."""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class ClinicianReviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assessment_id: str
    clinician_id: str = Field(
        default="clinician-reviewer",
        validation_alias=AliasChoices("clinician_id", "reviewer_name"),
    )
    action: Literal["accept", "override", "needs_review"] = Field(
        validation_alias=AliasChoices("action", "clinician_decision")
    )
    final_esi: int | None = Field(
        default=None,
        ge=1,
        le=5,
        validation_alias=AliasChoices("final_esi", "clinician_final_esi"),
    )
    override_reason: str | None = None
    notes: str | None = Field(
        default=None,
        validation_alias=AliasChoices("notes", "review_note"),
    )

    @model_validator(mode="after")
    def validate_override_fields(self) -> "ClinicianReviewRequest":
        if self.action != "override":
            return self

        if self.final_esi is None:
            raise ValueError("final_esi is required when overriding final_esi")

        if not self.override_reason or not self.override_reason.strip():
            raise ValueError("override_reason is required when overriding final_esi")
        return self


class ClinicianReviewResponse(BaseModel):
    review_id: str
    assessment_id: str
    clinician_decision: str
    clinician_final_esi: int | None = Field(default=None, ge=1, le=5)
    final_esi: int | None = Field(default=None, ge=1, le=5)
    review_note: str | None = None
    status: str
    review_status: str | None = None
    review_status_normalized: str | None = None
    review_status_raw: str | None = None
    reviewer: str | None = None
    reviewer_role: str | None = None
    reviewed: bool
    reviewed_at: datetime | None = None
    audit_event_created: bool = False
    message: str
    is_placeholder: bool
    timestamp: datetime | None = None
