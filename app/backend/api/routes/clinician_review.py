from fastapi import APIRouter

from app.backend.schemas.clinician_review import (
    ClinicianReviewRequest,
    ClinicianReviewResponse,
)
from app.backend.utils.ids import new_id

router = APIRouter(prefix="/clinician-review", tags=["clinician-review"])


@router.post("", response_model=ClinicianReviewResponse)
def submit_clinician_review(
    review: ClinicianReviewRequest,
) -> ClinicianReviewResponse:
    return ClinicianReviewResponse(
        review_id=new_id(),
        assessment_id=review.assessment_id,
        status="recorded_placeholder",
        message="Clinician review contract is ready. No review is persisted yet.",
        is_placeholder=True,
    )
