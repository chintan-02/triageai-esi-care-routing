from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException

from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.assessment import (
    AssessmentCreateResponse,
    AssessmentDetailResponse,
)
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.utils.ids import new_id

router = APIRouter(prefix="/assessments", tags=["assessments"])


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
        message="Assessment loaded from database.",
        is_placeholder=False,
    )
