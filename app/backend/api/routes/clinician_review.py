from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.clinician_review import (
    ClinicianReviewRequest,
    ClinicianReviewResponse,
)
from app.backend.services.audit_service import build_audit_details
from app.backend.services.text_formatting import clean_human_readable_text

router = APIRouter(prefix="/clinician-review", tags=["clinician-review"])


def _normalize_review_status(action: str) -> str:
    if action == "override":
        return "overridden"
    if action == "accept":
        return "accepted"
    return "pending"


@router.post("", response_model=ClinicianReviewResponse)
def submit_clinician_review(
    review: ClinicianReviewRequest,
    db: Session = Depends(get_db),
) -> ClinicianReviewResponse:
    assessment = repositories.get_assessment_by_id(db, review.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    latest_prediction = repositories.get_latest_prediction_for_assessment(
        db,
        review.assessment_id,
    )
    if review.action == "accept" and latest_prediction and latest_prediction.final_esi:
        if review.final_esi is not None and review.final_esi != latest_prediction.final_esi:
            raise HTTPException(
                status_code=422,
                detail="Accepted final_esi must match the model final_esi.",
            )
        review = review.model_copy(update={"final_esi": latest_prediction.final_esi})

    review_record = repositories.create_clinician_review(db, review)
    status = "needs_review" if review.action == "needs_review" else "review_completed"
    review_status_normalized = _normalize_review_status(review.action)
    repositories.update_assessment_status(db, review.assessment_id, status)
    audit_event = repositories.create_audit_log(
        db=db,
        assessment_id=review.assessment_id,
        actor_id=review.clinician_id,
        action=f"clinician_review_{review.action}",
        details=build_audit_details(
            action=review.action,
            payload=review.model_dump(),
        ),
    )

    review_note = clean_human_readable_text(
        review_record.override_reason or review_record.notes
    )

    return ClinicianReviewResponse(
        review_id=review_record.id,
        assessment_id=review.assessment_id,
        clinician_decision=review.action,
        clinician_final_esi=review_record.final_esi,
        final_esi=review_record.final_esi,
        review_note=review_note,
        status=status,
        review_status=review_status_normalized,
        review_status_normalized=review_status_normalized,
        review_status_raw=status,
        reviewer=review.clinician_id,
        reviewer_role=None,
        reviewed=status == "review_completed",
        reviewed_at=review_record.created_at,
        audit_event_created=audit_event is not None,
        message="Clinician review saved and audit trail updated.",
        is_placeholder=False,
        timestamp=review_record.created_at,
    )
