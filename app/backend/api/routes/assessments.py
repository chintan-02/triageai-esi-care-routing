import json
from typing import Any

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.assessment import (
    AssessmentAuditEvent,
    AssessmentClinicianReviewDetail,
    AssessmentCreateResponse,
    AssessmentDetailResponse,
    AssessmentPredictionDetail,
)
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.utils.ids import new_id

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _json_or_default(raw_value: str | None, default: Any) -> Any:
    if not raw_value:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


@router.post("", response_model=AssessmentCreateResponse)
def create_assessment(
    intake: PatientIntakeRequest,
    db: Session = Depends(get_db),
) -> AssessmentCreateResponse:
    assessment = repositories.create_assessment(db, intake)

    return AssessmentCreateResponse(
        request_id=new_id(),
        assessment_id=assessment.id,
        patient_id=assessment.patient_id,
        status=assessment.status,
        created_at=assessment.created_at,
        intake=intake,
        message="Assessment created and stored for ESI review.",
        is_placeholder=False,
    )


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> AssessmentDetailResponse:
    assessment = repositories.get_assessment_by_id(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    intake = PatientIntakeRequest(
        patient_age=assessment.patient.age,
        sex=assessment.patient.sex,
        chief_complaint=assessment.chief_complaint,
        symptom_duration=assessment.symptom_duration,
        pain_score=assessment.pain_score,
        temperature_c=assessment.temperature_c,
        heart_rate=assessment.heart_rate,
        respiratory_rate=assessment.respiratory_rate,
        systolic_bp=assessment.systolic_bp,
        diastolic_bp=assessment.diastolic_bp,
        oxygen_saturation=assessment.oxygen_saturation,
        consciousness_level=assessment.consciousness_level,
        pregnancy=assessment.pregnancy,
        arrival_mode=assessment.arrival_mode,
        additional_context=assessment.additional_context,
    )

    latest_prediction = repositories.get_latest_prediction_for_assessment(
        db,
        assessment_id,
    )
    prediction_detail = None
    if latest_prediction:
        prediction_detail = AssessmentPredictionDetail(
            prediction_id=latest_prediction.id,
            model_version=latest_prediction.model_version,
            model_loaded=latest_prediction.model_loaded,
            predicted_esi=latest_prediction.predicted_esi,
            final_esi=latest_prediction.final_esi,
            confidence_score=latest_prediction.confidence_score,
            probabilities=_json_or_default(latest_prediction.probabilities_json, {}),
            safety_rules_triggered=_json_or_default(
                latest_prediction.safety_rules_json,
                [],
            ),
            final_source=latest_prediction.final_source,
            recommendation=latest_prediction.recommendation,
            explanation=latest_prediction.explanation,
            clinician_summary=latest_prediction.clinician_summary,
            is_placeholder=latest_prediction.is_placeholder,
            created_at=latest_prediction.created_at,
        )

    latest_review = repositories.get_latest_clinician_review_for_assessment(
        db,
        assessment_id,
    )
    review_detail = None
    if latest_review:
        review_detail = AssessmentClinicianReviewDetail(
            review_id=latest_review.id,
            clinician_id=latest_review.clinician_id,
            clinician_decision=latest_review.action,
            clinician_final_esi=latest_review.final_esi,
            override_reason=latest_review.override_reason,
            review_note=latest_review.notes,
            reviewed=assessment.status == "review_completed",
            created_at=latest_review.created_at,
        )

    audit_trail = [
        AssessmentAuditEvent(
            audit_id=f"assessment:{assessment.id}",
            actor_id=None,
            action="assessment_created",
            details={"status": assessment.status},
            created_at=assessment.created_at,
        )
    ]
    if latest_prediction:
        audit_trail.append(
            AssessmentAuditEvent(
                audit_id=f"prediction:{latest_prediction.id}",
                actor_id=None,
                action="prediction_generated",
                details={
                    "predicted_esi": latest_prediction.predicted_esi,
                    "final_esi": latest_prediction.final_esi,
                    "final_source": latest_prediction.final_source,
                },
                created_at=latest_prediction.created_at,
            )
        )
    for audit_log in repositories.list_audit_logs_for_assessment(db, assessment_id):
        audit_trail.append(
            AssessmentAuditEvent(
                audit_id=audit_log.id,
                actor_id=audit_log.actor_id,
                action=audit_log.action,
                details=_json_or_default(audit_log.details_json, None),
                created_at=audit_log.created_at,
            )
        )

    return AssessmentDetailResponse(
        request_id=new_id(),
        assessment_id=assessment.id,
        patient_id=assessment.patient_id,
        status=assessment.status,
        chief_complaint=assessment.chief_complaint,
        symptom_duration=assessment.symptom_duration,
        pain_score=assessment.pain_score,
        temperature_c=assessment.temperature_c,
        heart_rate=assessment.heart_rate,
        respiratory_rate=assessment.respiratory_rate,
        systolic_bp=assessment.systolic_bp,
        diastolic_bp=assessment.diastolic_bp,
        oxygen_saturation=assessment.oxygen_saturation,
        consciousness_level=assessment.consciousness_level,
        pregnancy=assessment.pregnancy,
        arrival_mode=assessment.arrival_mode,
        additional_context=assessment.additional_context,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        intake=intake,
        latest_prediction=prediction_detail,
        latest_clinician_review=review_detail,
        audit_trail=audit_trail,
        message="Assessment loaded from database.",
        is_placeholder=False,
    )
