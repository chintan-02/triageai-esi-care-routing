import json
from typing import Any

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.backend.api.routes.reports import get_or_generate_assessment_report_pdf
from app.backend.db import repositories
from app.backend.db.session import get_db
from app.backend.schemas.assessment import (
    AssessmentAuditEvent,
    AssessmentAuditTrailResponse,
    AssessmentClinicianReviewDetail,
    AssessmentCreateResponse,
    AssessmentDetailResponse,
    AssessmentListItem,
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


def _normalize_review_status(assessment_status: str, latest_review: Any | None) -> str:
    if latest_review is not None:
        if latest_review.action == "override":
            return "overridden"
        if latest_review.action == "accept":
            return "accepted"
        if latest_review.action in {"needs_review", "pending_review"}:
            return "pending"

    if assessment_status in {"review_completed", "accepted", "completed"}:
        return "accepted"
    if assessment_status in {"pending_review", "needs_review", "review_pending"}:
        return "pending"
    return "pending"


def _review_status_details(assessment: Any, latest_review: Any | None) -> tuple[str, str]:
    normalized_value = _normalize_review_status(assessment.status, latest_review)
    return normalized_value, normalized_value


def _audit_event(
    *,
    audit_id: str,
    action: str,
    created_at: Any,
    actor_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> AssessmentAuditEvent:
    message = None
    if details:
        detail_message = details.get("message") or details.get("reason")
        if isinstance(detail_message, str):
            message = detail_message

    return AssessmentAuditEvent(
        audit_id=audit_id,
        actor_id=actor_id,
        action=action,
        details=details,
        created_at=created_at,
        event_type=action,
        message=message,
        actor=actor_id,
        timestamp=created_at,
    )


def _risk_flags_from_safety_rules(safety_rules: list[Any]) -> list[str]:
    flags: list[str] = []
    for rule in safety_rules:
        if isinstance(rule, dict):
            flag = rule.get("rule_id") or rule.get("rule_name") or rule.get("name")
            if flag:
                flags.append(str(flag))
        elif rule is not None:
            flags.append(str(rule))
    return flags


def _patient_name(assessment: Any) -> str:
    name = getattr(getattr(assessment, "patient", None), "name", None)
    return name if isinstance(name, str) and name.strip() else "Unknown patient"


def _patient_mrn(assessment: Any) -> str:
    mrn = getattr(getattr(assessment, "patient", None), "mrn", None)
    return mrn if isinstance(mrn, str) and mrn.strip() else "N/A"


def _build_assessment_audit_events(
    db: Session,
    assessment: Any,
    latest_prediction: Any | None = None,
) -> list[AssessmentAuditEvent]:
    events = [
        _audit_event(
            audit_id=f"assessment:{assessment.id}",
            action="assessment_created",
            details={
                "status": "pending_review",
                "message": "Assessment created and queued for clinician review.",
            },
            created_at=assessment.created_at,
        )
    ]
    if latest_prediction:
        events.append(
            _audit_event(
                audit_id=f"prediction:{latest_prediction.id}",
                action="prediction_generated",
                details={
                    "predicted_esi": latest_prediction.predicted_esi,
                    "final_esi": latest_prediction.final_esi,
                    "latency_ms": latest_prediction.latency_ms,
                    "final_source": latest_prediction.final_source,
                    "message": (
                        "Model prediction generated. "
                        f"Predicted ESI {latest_prediction.predicted_esi}, "
                        f"final ESI {latest_prediction.final_esi}."
                    ),
                },
                created_at=latest_prediction.created_at,
            )
        )
    for audit_log in repositories.list_audit_logs_for_assessment(db, assessment.id):
        events.append(
            _audit_event(
                audit_id=audit_log.id,
                actor_id=audit_log.actor_id,
                action=audit_log.action,
                details=_json_or_default(audit_log.details_json, None),
                created_at=audit_log.created_at,
            )
        )

    return sorted(
        events,
        key=lambda event: event.created_at.isoformat() if event.created_at else "",
    )


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


@router.get("", response_model=list[AssessmentListItem])
def list_assessments(db: Session = Depends(get_db)) -> list[AssessmentListItem]:
    items: list[AssessmentListItem] = []
    for assessment in repositories.list_assessments(db):
        latest_prediction = repositories.get_latest_prediction_for_assessment(
            db,
            assessment.id,
        )
        latest_review = repositories.get_latest_clinician_review_for_assessment(
            db,
            assessment.id,
        )
        review_status, review_status_normalized = _review_status_details(
            assessment,
            latest_review,
        )
        safety_rules = (
            _json_or_default(latest_prediction.safety_rules_json, [])
            if latest_prediction
            else []
        )
        safety_escalated = bool(safety_rules)
        final_esi = (
            latest_review.final_esi
            if latest_review and latest_review.final_esi is not None
            else latest_prediction.final_esi if latest_prediction else None
        )
        items.append(
            AssessmentListItem(
                assessment_id=assessment.id,
                patient_id=assessment.patient_id,
                patient_name=_patient_name(assessment),
                mrn=_patient_mrn(assessment),
                age=assessment.patient.age if assessment.patient else None,
                sex=assessment.patient.sex if assessment.patient else None,
                arrival_mode=assessment.arrival_mode,
                chief_complaint=assessment.chief_complaint,
                symptom_narrative=assessment.additional_context or None,
                final_esi=final_esi,
                model_predicted_esi=latest_prediction.predicted_esi if latest_prediction else None,
                confidence_score=latest_prediction.confidence_score if latest_prediction else None,
                latency_ms=latest_prediction.latency_ms if latest_prediction else None,
                safety_escalated=safety_escalated,
                safety_gate_status="escalated" if safety_escalated else "clear",
                status=assessment.status,
                review_status=review_status_normalized,
                review_status_normalized=review_status_normalized,
                reviewer=latest_review.clinician_id if latest_review else None,
                reviewer_role=None,
                created_at=assessment.created_at,
                updated_at=assessment.updated_at,
                report_ids=[
                    report.id
                    for report in repositories.list_reports_for_assessment(db, assessment.id)
                ],
            )
        )
    return items


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> AssessmentDetailResponse:
    assessment = repositories.get_assessment_by_id(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    intake = PatientIntakeRequest(
        patient_name=assessment.patient.name if assessment.patient else None,
        mrn=assessment.patient.mrn if assessment.patient else None,
        patient_age=assessment.patient.age if assessment.patient else None,
        sex=assessment.patient.sex if assessment.patient else None,
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
            latency_ms=latest_prediction.latency_ms,
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

    audit_trail = _build_assessment_audit_events(db, assessment, latest_prediction)

    safety_rules = (
        _json_or_default(latest_prediction.safety_rules_json, [])
        if latest_prediction
        else []
    )
    safety_escalated = bool(safety_rules)
    review_status, review_status_normalized = _review_status_details(
        assessment,
        latest_review,
    )
    final_esi = (
        latest_review.final_esi
        if latest_review and latest_review.final_esi is not None
        else latest_prediction.final_esi if latest_prediction else None
    )

    request_id = new_id()
    return AssessmentDetailResponse(
        request_id=request_id,
        assessment_id=assessment.id,
        patient_id=assessment.patient_id,
        patient_name=_patient_name(assessment),
        mrn=_patient_mrn(assessment),
        age=assessment.patient.age if assessment.patient else None,
        sex=assessment.patient.sex if assessment.patient else None,
        status=assessment.status,
        chief_complaint=assessment.chief_complaint,
        symptom_duration=assessment.symptom_duration,
        symptom_narrative=assessment.additional_context or None,
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
        vitals={
            "temperature_c": assessment.temperature_c,
            "heart_rate": assessment.heart_rate,
            "respiratory_rate": assessment.respiratory_rate,
            "systolic_bp": assessment.systolic_bp,
            "diastolic_bp": assessment.diastolic_bp,
            "oxygen_saturation": assessment.oxygen_saturation,
        },
        risk_flags=_risk_flags_from_safety_rules(safety_rules),
        comorbidities=[],
        final_esi=final_esi,
        model_predicted_esi=latest_prediction.predicted_esi if latest_prediction else None,
        safety_escalated=safety_escalated,
        safety_gate_status="escalated" if safety_escalated else "clear",
        probabilities=(
            _json_or_default(latest_prediction.probabilities_json, {})
            if latest_prediction
            else {}
        ),
        confidence=latest_prediction.confidence_score if latest_prediction else None,
        latency_ms=latest_prediction.latency_ms if latest_prediction else None,
        model_version=latest_prediction.model_version if latest_prediction else None,
        request_id_value=request_id,
        review_status=review_status,
        review_status_normalized=review_status_normalized,
        reviewer=latest_review.clinician_id if latest_review else None,
        reviewer_role=None,
        created_at=assessment.created_at,
        updated_at=assessment.updated_at,
        intake=intake,
        latest_prediction=prediction_detail,
        latest_clinician_review=review_detail,
        audit_trail=audit_trail,
        report_ids=[
            report.id
            for report in repositories.list_reports_for_assessment(db, assessment.id)
        ],
        message="Assessment loaded from database.",
        is_placeholder=False,
    )


@router.get("/{assessment_id}/audit", response_model=AssessmentAuditTrailResponse)
def get_assessment_audit(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> AssessmentAuditTrailResponse:
    assessment = repositories.get_assessment_by_id(db, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    latest_prediction = repositories.get_latest_prediction_for_assessment(db, assessment_id)
    events = _build_assessment_audit_events(db, assessment, latest_prediction)

    return AssessmentAuditTrailResponse(assessment_id=assessment.id, events=events)


@router.get("/{assessment_id}/report/pdf")
def download_assessment_report_pdf(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    return get_or_generate_assessment_report_pdf(assessment_id, db)
