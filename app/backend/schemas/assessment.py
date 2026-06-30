"""Assessment persistence placeholder schemas."""

from pydantic import BaseModel

from app.backend.schemas.intake import PatientIntakeRequest


class AssessmentCreateResponse(BaseModel):
    request_id: str
    assessment_id: str
    status: str
    intake: PatientIntakeRequest
    message: str
    is_placeholder: bool


class AssessmentDetailResponse(BaseModel):
    request_id: str
    assessment_id: str
    status: str
    intake: PatientIntakeRequest | None = None
    message: str
    is_placeholder: bool
