from pathlib import Path

import pytest

from app.backend.db.session import SessionLocal
from app.backend.db.models import Report
from app.backend.db import repositories
from scripts import demo_reset_seed


def test_sqlite_db_path_accepts_local_sqlite_url(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"

    resolved = demo_reset_seed.sqlite_db_path(f"sqlite:///{db_path}")

    assert resolved == db_path.resolve()


def test_sqlite_db_path_rejects_non_sqlite_url() -> None:
    with pytest.raises(ValueError, match="Refusing non-SQLite"):
        demo_reset_seed.sqlite_db_path("postgresql://user:pass@example.com/db")


def test_backup_database_copies_existing_sqlite_file(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"
    db_path.write_bytes(b"sqlite-data")
    backup_dir = tmp_path / "backups"

    backup_path = demo_reset_seed.backup_database(db_path, backup_dir=backup_dir)

    assert backup_path is not None
    assert backup_path.parent == backup_dir
    assert backup_path.name.startswith("triageai_demo_backup_")
    assert backup_path.read_bytes() == b"sqlite-data"


def test_reset_requires_yes(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        demo_reset_seed.settings,
        "DATABASE_URL",
        "sqlite:///./triageai_test_demo.sqlite",
    )
    monkeypatch.setattr(
        demo_reset_seed,
        "init_db",
        lambda: (_ for _ in ()).throw(AssertionError("init_db should not run")),
    )
    monkeypatch.setattr("sys.argv", ["demo_reset_seed.py", "--reset"])

    exit_code = demo_reset_seed.main()
    output = capsys.readouterr().out

    assert exit_code == 2
    assert "--reset is destructive and requires --yes" in output


def test_demo_seed_payloads_are_valid() -> None:
    cases = demo_reset_seed.demo_cases()

    assert len(cases) == 6
    assert cases[0].review_action == "accept"
    assert cases[0].intake.patient_name == "Demo Patient"
    assert cases[0].intake.mrn == "MRN-DEMO-1001"
    assert cases[2].review_action is None
    assert cases[3].review_action is None
    assert cases[4].intake.oxygen_saturation < 92
    assert all(case.intake.patient_name for case in cases)
    assert all(case.intake.mrn for case in cases)


def test_seed_demo_data_creates_expected_isolated_cases() -> None:
    with SessionLocal() as db:
        summaries = demo_reset_seed.seed_demo_data(db)
        dashboard = repositories.get_dashboard_summary(db)
        report_count = db.query(Report).count()

    assert len(summaries) == 6
    assert {summary["status"] for summary in summaries} == {
        "pending_review",
        "review_completed",
    }
    assert all(summary["patient_name"] != "Unknown patient" for summary in summaries)
    assert all(summary["mrn"] != "N/A" for summary in summaries)
    assert all(summary["final_esi"] is not None for summary in summaries)
    assert all(summary["latency_ms"] is not None for summary in summaries)
    assert all(summary["report_id"] for summary in summaries)
    assert summaries[2]["clinician_decision"] == "pending"
    assert summaries[3]["clinician_decision"] == "pending"
    assert summaries[4]["safety_rules_triggered"]
    assert dashboard["total_assessments"] == 6
    assert dashboard["pending_reviews"] == 2
    assert dashboard["completed_reviews"] == 4
    assert len(dashboard["recent_assessments"]) == 6
    assert report_count == 6
