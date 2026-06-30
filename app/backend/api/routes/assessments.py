from fastapi import APIRouter

from app.backend.schemas.assessment import (
    AssessmentCreateResponse,
    AssessmentDetailResponse,
)
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.utils.ids import new_id

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentCreateResponse)
def create_assessment(intake: PatientIntakeRequest) -> AssessmentCreateResponse:
    return AssessmentCreateResponse(
        request_id=new_id(),
        assessment_id=new_id(),
        status="created_placeholder",
        intake=intake,
        message="Assessment persistence contract is ready. No database record is created yet.",
        is_placeholder=True,
    )


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(assessment_id: str) -> AssessmentDetailResponse:
    return AssessmentDetailResponse(
        request_id=new_id(),
        assessment_id=assessment_id,
        status="placeholder_detail",
        intake=None,
        message="Assessment detail contract is ready. No persisted assessment is loaded yet.",
        is_placeholder=True,
    )
