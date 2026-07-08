"""Local-only demo database backup, reset, and seed utility.

This script is for local SQLite demo data only. It uses the existing model
prediction service and repository functions so seeded rows reflect the real
workflow rather than fake hard-coded model outputs.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from urllib.parse import unquote

from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.backend.core.config import settings
from app.backend.db import repositories
from app.backend.db.base import init_db
from app.backend.db.models import (
    Assessment,
    AuditLog,
    ClinicianReview,
    Patient,
    Prediction,
    Report,
)
from app.backend.db.session import SessionLocal
from app.backend.schemas.clinician_review import ClinicianReviewRequest
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.api.routes.reports import get_or_generate_assessment_report_pdf
from app.backend.services.audit_service import build_audit_details
from app.backend.services.prediction_service import predict_esi_for_intake


BACKUP_DIR = Path("backups/demo_db")
LOCAL_ONLY_MESSAGE = "This script is for local demo SQLite data only."


@dataclass(frozen=True)
class DemoCase:
    name: str
    intake: PatientIntakeRequest
    review_action: str | None = None
    override_final_esi: int | None = None
    override_reason: str | None = None
    review_notes: str | None = None


def sqlite_db_path(database_url: str) -> Path:
    """Return the local SQLite DB path or raise ValueError for unsafe URLs."""
    url = make_url(database_url)
    if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise ValueError(f"Refusing non-SQLite DATABASE_URL: {url.drivername}")

    database = unquote(url.database or "")
    if not database or database == ":memory:":
        raise ValueError("Refusing in-memory or missing SQLite database path.")

    path = Path(database)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def backup_database(db_path: Path, backup_dir: Path = BACKUP_DIR) -> Path | None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        print(f"No existing SQLite DB found at {db_path}; backup skipped.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"triageai_demo_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Backed up local SQLite DB to {backup_path}")
    return backup_path


def reset_demo_data(db: Session) -> None:
    for model in [Report, AuditLog, ClinicianReview, Prediction, Assessment, Patient]:
        db.query(model).delete()
    db.commit()
    print("Cleared local demo workflow tables.")


def demo_cases() -> list[DemoCase]:
    return [
        DemoCase(
            name="Demo Patient - Chest pain - accepted",
            intake=PatientIntakeRequest(
                patient_name="Demo Patient",
                mrn="MRN-DEMO-1001",
                patient_age=52,
                sex="male",
                chief_complaint="Chest pain",
                symptom_duration="45 minutes",
                pain_score=6,
                temperature_c=37.1,
                heart_rate=112,
                respiratory_rate=22,
                systolic_bp=135,
                diastolic_bp=85,
                oxygen_saturation=96.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context=(
                    "Substernal chest pain without syncope. Stable appearance; "
                    "requires structured ESI care routing and clinician review."
                ),
            ),
            review_action="accept",
            review_notes="Accepted final routing decision after clinician review.",
        ),
        DemoCase(
            name="Rahul Patel - Low-acuity symptom - accepted",
            intake=PatientIntakeRequest(
                patient_name="Rahul Patel",
                mrn="MRN-DEMO-1002",
                patient_age=34,
                sex="male",
                chief_complaint="Mild sore throat",
                symptom_duration="2 days",
                pain_score=1,
                temperature_c=36.9,
                heart_rate=74,
                respiratory_rate=15,
                systolic_bp=118,
                diastolic_bp=74,
                oxygen_saturation=99.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="Mild upper respiratory symptoms; no dyspnea, chest pain, or abnormal vital signs.",
            ),
            review_action="accept",
            review_notes="Accepted lower-acuity final routing decision after clinician review.",
        ),
        DemoCase(
            name="Jamie Rivera - Abdominal pain - pending review",
            intake=PatientIntakeRequest(
                patient_name="Jamie Rivera",
                mrn="MRN-DEMO-1003",
                patient_age=41,
                sex="other",
                chief_complaint="Abdominal pain",
                symptom_duration="8 hours",
                pain_score=6,
                temperature_c=37.4,
                heart_rate=96,
                respiratory_rate=18,
                systolic_bp=124,
                diastolic_bp=80,
                oxygen_saturation=98.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="Cramping abdominal pain with nausea; awaiting clinician review.",
            ),
            review_action=None,
        ),
        DemoCase(
            name="Maya Chen - Fever - pending review",
            intake=PatientIntakeRequest(
                patient_name="Maya Chen",
                mrn="MRN-DEMO-1004",
                patient_age=7,
                sex="female",
                chief_complaint="Fever",
                symptom_duration="1 day",
                pain_score=2,
                temperature_c=38.4,
                heart_rate=108,
                respiratory_rate=20,
                systolic_bp=102,
                diastolic_bp=66,
                oxygen_saturation=98.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Referral",
                additional_context="Fever with reduced appetite; alert and interactive during intake.",
            ),
            review_action=None,
        ),
        DemoCase(
            name="Omar Khan - Shortness of breath safety escalation - accepted",
            intake=PatientIntakeRequest(
                patient_name="Omar Khan",
                mrn="MRN-DEMO-1005",
                patient_age=56,
                sex="male",
                chief_complaint="Chest discomfort with shortness of breath",
                symptom_duration="1 hour",
                pain_score=5,
                temperature_c=36.8,
                heart_rate=116,
                respiratory_rate=24,
                systolic_bp=136,
                diastolic_bp=84,
                oxygen_saturation=88.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Ambulance",
                additional_context="Chest discomfort with dyspnea and low oxygen saturation; safety escalation expected.",
            ),
            review_action="accept",
            review_notes="Accepted safety-rule escalation for urgent clinician review.",
        ),
        DemoCase(
            name="Sofia Martinez - Minor injury - accepted",
            intake=PatientIntakeRequest(
                patient_name="Sofia Martinez",
                mrn="MRN-DEMO-1006",
                patient_age=29,
                sex="female",
                chief_complaint="Minor wrist injury",
                symptom_duration="3 hours",
                pain_score=3,
                temperature_c=36.8,
                heart_rate=82,
                respiratory_rate=16,
                systolic_bp=122,
                diastolic_bp=78,
                oxygen_saturation=99.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="Wrist pain after a fall; no deformity, normal sensation, and stable vital signs.",
            ),
            review_action="accept",
            review_notes="Accepted final routing decision for minor injury demo case.",
        ),
    ]


def _save_review(db: Session, assessment_id: str, case: DemoCase, model_final_esi: int | None) -> str | None:
    if case.review_action is None:
        return None

    final_esi = case.override_final_esi if case.review_action == "override" else model_final_esi
    review_request = ClinicianReviewRequest(
        assessment_id=assessment_id,
        clinician_id="demo-clinician",
        action=case.review_action,
        final_esi=final_esi,
        override_reason=case.override_reason,
        notes=case.review_notes,
    )
    review_record = repositories.create_clinician_review(db, review_request)
    status = "needs_review" if review_request.action == "needs_review" else "review_completed"
    repositories.update_assessment_status(db, assessment_id, status)
    repositories.create_audit_log(
        db=db,
        assessment_id=assessment_id,
        actor_id=review_request.clinician_id,
        action=f"clinician_review_{review_request.action}",
        details=build_audit_details(
            action=review_request.action,
            payload=review_request.model_dump(),
        ),
    )
    return review_record.action


def seed_demo_data(db: Session) -> list[dict[str, object]]:
    summaries = []
    for case in demo_cases():
        assessment = repositories.create_assessment(db, case.intake)
        started_at = perf_counter()
        prediction = predict_esi_for_intake(case.intake)
        prediction.latency_ms = max(0, round((perf_counter() - started_at) * 1000))
        prediction.assessment_id = assessment.id
        repositories.create_prediction(db, assessment.id, prediction)
        decision = _save_review(db, assessment.id, case, prediction.final_esi)
        get_or_generate_assessment_report_pdf(assessment.id, db)
        db.refresh(assessment)
        report_record = repositories.get_latest_generated_report_for_assessment(
            db,
            assessment.id,
        )
        summaries.append(
            {
                "case": case.name,
                "patient_name": case.intake.patient_name,
                "mrn": case.intake.mrn,
                "assessment_id": assessment.id,
                "chief_complaint": assessment.chief_complaint,
                "predicted_esi": prediction.predicted_esi,
                "final_esi": prediction.final_esi,
                "latency_ms": prediction.latency_ms,
                "clinician_decision": decision or "pending",
                "status": assessment.status,
                "report_id": report_record.id if report_record else None,
                "safety_rules_triggered": [
                    rule.rule_id for rule in prediction.safety_rules_triggered if rule.triggered
                ],
            }
        )
    return summaries


def print_seed_summary(summaries: list[dict[str, object]]) -> None:
    print("\nSeed summary:")
    for summary in summaries:
        safety = summary["safety_rules_triggered"] or []
        print(
            "- {case}: patient={patient_name}, mrn={mrn}, assessment_id={assessment_id}, "
            "chief_complaint={chief_complaint}, "
            "predicted_esi={predicted_esi}, final_esi={final_esi}, "
            "latency_ms={latency_ms}, clinician_decision={clinician_decision}, "
            "status={status}, report_id={report_id}, safety_rules_triggered={safety}".format(
                **summary,
                safety=", ".join(safety) if safety else "none",
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reset and seed local TriageAI demo data.")
    parser.add_argument("--backup", action="store_true", help="Back up current local SQLite DB.")
    parser.add_argument("--reset", action="store_true", help="Clear local demo workflow tables.")
    parser.add_argument("--seed", action="store_true", help="Seed demo scenarios.")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive local reset.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    print(LOCAL_ONLY_MESSAGE)

    try:
        db_path = sqlite_db_path(settings.DATABASE_URL)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"SQLite DB path: {db_path}")

    if args.reset and not args.yes:
        print("ERROR: --reset is destructive and requires --yes.")
        return 2

    if not any([args.backup, args.reset, args.seed]):
        parser.print_help()
        return 0

    if args.backup:
        backup_database(db_path)

    init_db()
    with SessionLocal() as db:
        if args.reset:
            reset_demo_data(db)
        if args.seed:
            print_seed_summary(seed_demo_data(db))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
