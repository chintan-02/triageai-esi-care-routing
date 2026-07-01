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
            name="Case A - Typical ESI 3 accepted",
            intake=PatientIntakeRequest(
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
                additional_context="Stable appearance, no syncope, no altered mental status.",
            ),
            review_action="accept",
            review_notes="Accepted model/safety recommendation for typical ESI 3 demo case.",
        ),
        DemoCase(
            name="Case B - Safety-rule escalation accepted",
            intake=PatientIntakeRequest(
                patient_age=56,
                sex="male",
                chief_complaint="Chest discomfort",
                symptom_duration="1 hour",
                pain_score=5,
                temperature_c=36.8,
                heart_rate=115,
                respiratory_rate=22,
                systolic_bp=135,
                diastolic_bp=85,
                oxygen_saturation=87.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="Reports shortness of breath with low oxygen saturation.",
            ),
            review_action="accept",
            review_notes="Accepted safety-rule escalation due to oxygen saturation below 92%.",
        ),
        DemoCase(
            name="Case C - Clinician override",
            intake=PatientIntakeRequest(
                patient_age=60,
                sex="female",
                chief_complaint="Chest pain",
                symptom_duration="30 minutes",
                pain_score=6,
                temperature_c=36.9,
                heart_rate=112,
                respiratory_rate=22,
                systolic_bp=135,
                diastolic_bp=85,
                oxygen_saturation=96.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="No shortness of breath documented at intake.",
            ),
            review_action="override",
            override_final_esi=2,
            override_reason="Additional clinical context indicates higher-risk presentation.",
            review_notes="Escalated for high-priority clinician review.",
        ),
        DemoCase(
            name="Case D - Lower-acuity style case",
            intake=PatientIntakeRequest(
                patient_age=28,
                sex="female",
                chief_complaint="Mild itchy rash",
                symptom_duration="2 days",
                pain_score=1,
                temperature_c=36.7,
                heart_rate=78,
                respiratory_rate=16,
                systolic_bp=118,
                diastolic_bp=76,
                oxygen_saturation=99.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="No fever, no swelling, no breathing symptoms.",
            ),
            review_action="accept",
            review_notes="Accepted lower-acuity style demo case after clinician review.",
        ),
        DemoCase(
            name="Case E - Pending review",
            intake=PatientIntakeRequest(
                patient_age=35,
                sex="male",
                chief_complaint="Ankle pain",
                symptom_duration="4 hours",
                pain_score=4,
                temperature_c=36.8,
                heart_rate=82,
                respiratory_rate=16,
                systolic_bp=122,
                diastolic_bp=78,
                oxygen_saturation=99.0,
                consciousness_level="alert",
                pregnancy=False,
                arrival_mode="Walk-in",
                additional_context="Twisted ankle while walking; no deformity reported.",
            ),
            review_action=None,
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
        prediction = predict_esi_for_intake(case.intake)
        prediction.assessment_id = assessment.id
        repositories.create_prediction(db, assessment.id, prediction)
        decision = _save_review(db, assessment.id, case, prediction.final_esi)
        db.refresh(assessment)
        summaries.append(
            {
                "case": case.name,
                "assessment_id": assessment.id,
                "chief_complaint": assessment.chief_complaint,
                "predicted_esi": prediction.predicted_esi,
                "final_esi": prediction.final_esi,
                "clinician_decision": decision or "pending",
                "status": assessment.status,
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
            "- {case}: assessment_id={assessment_id}, chief_complaint={chief_complaint}, "
            "predicted_esi={predicted_esi}, final_esi={final_esi}, "
            "clinician_decision={clinician_decision}, status={status}, "
            "safety_rules_triggered={safety}".format(
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
