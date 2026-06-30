"""Small repository helpers for database-backed API routes."""

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.backend.db.models import (
    Assessment,
    AuditLog,
    ClinicianReview,
    Patient,
    Prediction,
    Report,
)
from app.backend.schemas.clinician_review import ClinicianReviewRequest
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import ESIPredictionResponse
from app.backend.schemas.report import ReportRequest


def create_patient_from_intake(db: Session, intake: PatientIntakeRequest) -> Patient:
    patient = Patient(age=intake.patient_age, sex=intake.sex)
    db.add(patient)
    db.flush()
    return patient


def create_assessment(db: Session, intake: PatientIntakeRequest) -> Assessment:
    patient = create_patient_from_intake(db, intake)
    assessment = Assessment(
        patient_id=patient.id,
        chief_complaint=intake.chief_complaint,
        symptom_duration=intake.symptom_duration,
        pain_score=intake.pain_score,
        temperature_c=intake.temperature_c,
        heart_rate=intake.heart_rate,
        respiratory_rate=intake.respiratory_rate,
        systolic_bp=intake.systolic_bp,
        diastolic_bp=intake.diastolic_bp,
        oxygen_saturation=intake.oxygen_saturation,
        consciousness_level=intake.consciousness_level,
        pregnancy=intake.pregnancy,
        arrival_mode=intake.arrival_mode,
        additional_context=intake.additional_context,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def get_assessment_by_id(db: Session, assessment_id: str) -> Assessment | None:
    return db.get(Assessment, assessment_id)


def list_recent_assessments(db: Session, limit: int = 10) -> list[Assessment]:
    statement = (
        select(Assessment)
        .order_by(Assessment.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def create_prediction(
    db: Session,
    assessment_id: str,
    prediction_response: ESIPredictionResponse,
) -> Prediction:
    prediction = Prediction(
        assessment_id=assessment_id,
        acuity_scale=prediction_response.acuity_scale,
        model_version=prediction_response.model_version,
        model_loaded=prediction_response.model_loaded,
        predicted_esi=prediction_response.predicted_esi,
        final_esi=prediction_response.final_esi,
        confidence_score=prediction_response.confidence_score,
        probabilities_json=json.dumps(prediction_response.probabilities),
        safety_rules_json=json.dumps(
            [rule.model_dump() for rule in prediction_response.safety_rules_triggered]
        ),
        final_source=prediction_response.final_source,
        recommendation=prediction_response.recommendation,
        explanation=prediction_response.explanation,
        clinician_summary=prediction_response.clinician_summary,
        is_placeholder=prediction_response.is_placeholder,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def create_clinician_review(
    db: Session,
    review_request: ClinicianReviewRequest,
) -> ClinicianReview:
    review = ClinicianReview(
        assessment_id=review_request.assessment_id,
        clinician_id=review_request.clinician_id,
        action=review_request.action,
        final_esi=review_request.final_esi,
        override_reason=review_request.override_reason,
        notes=review_request.notes,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def update_assessment_status(
    db: Session,
    assessment_id: str,
    status: str,
) -> Assessment | None:
    assessment = get_assessment_by_id(db, assessment_id)
    if assessment is None:
        return None

    assessment.status = status
    db.commit()
    db.refresh(assessment)
    return assessment


def create_audit_log(
    db: Session,
    assessment_id: str | None,
    actor_id: str | None,
    action: str,
    details: dict[str, Any] | None,
) -> AuditLog:
    audit_log = AuditLog(
        assessment_id=assessment_id,
        actor_id=actor_id,
        action=action,
        details_json=json.dumps(details) if details is not None else None,
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def create_report_record(db: Session, report_request: ReportRequest) -> Report:
    report = Report(
        assessment_id=report_request.assessment_id,
        report_status="queued",
        download_url=None,
        include_audit=report_request.include_audit,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_dashboard_summary(db: Session) -> dict[str, Any]:
    total_assessments = db.scalar(select(func.count()).select_from(Assessment)) or 0
    pending_reviews = (
        db.scalar(
            select(func.count())
            .select_from(Assessment)
            .where(Assessment.status.in_(["pending_review", "needs_review"]))
        )
        or 0
    )
    completed_reviews = (
        db.scalar(
            select(func.count())
            .select_from(Assessment)
            .where(Assessment.status == "review_completed")
        )
        or 0
    )

    predictions = list(
        db.scalars(
            select(Prediction).order_by(
                Prediction.assessment_id.asc(),
                Prediction.created_at.desc(),
            )
        ).all()
    )
    latest_by_assessment: dict[str, Prediction] = {}
    for prediction in predictions:
        latest_by_assessment.setdefault(prediction.assessment_id, prediction)

    esi_distribution: dict[str, int] = {}
    high_risk_flags = 0
    for prediction in latest_by_assessment.values():
        if prediction.final_esi is None:
            continue

        esi_key = str(prediction.final_esi)
        esi_distribution[esi_key] = esi_distribution.get(esi_key, 0) + 1
        if prediction.final_esi <= 2:
            high_risk_flags += 1

    recent_assessments = []
    for assessment in list_recent_assessments(db):
        latest_prediction = latest_by_assessment.get(assessment.id)
        recent_assessments.append(
            {
                "assessment_id": assessment.id,
                "patient_id": assessment.patient_id,
                "chief_complaint": assessment.chief_complaint,
                "status": assessment.status,
                "created_at": assessment.created_at,
                "final_esi": latest_prediction.final_esi if latest_prediction else None,
            }
        )

    return {
        "total_assessments": total_assessments,
        "pending_reviews": pending_reviews,
        "completed_reviews": completed_reviews,
        "high_risk_flags": high_risk_flags,
        "esi_distribution": esi_distribution,
        "recent_assessments": recent_assessments,
        "is_placeholder": False,
    }
