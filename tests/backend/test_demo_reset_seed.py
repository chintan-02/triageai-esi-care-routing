from pathlib import Path

import pytest

from scripts import demo_reset_seed


def test_sqlite_db_path_accepts_local_sqlite_url(tmp_path: Path) -> None:
    db_path = tmp_path / "demo.sqlite"

    resolved = demo_reset_seed.sqlite_db_path(f"sqlite:///{db_path}")

    assert resolved == db_path.resolve()


def test_sqlite_db_path_rejects_non_sqlite_url() -> None:
    with pytest.raises(ValueError, match="Refusing non-SQLite"):
        demo_reset_seed.sqlite_db_path("postgresql://user:pass@example.com/db")


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

    assert len(cases) == 5
    assert cases[0].review_action == "accept"
    assert cases[1].intake.oxygen_saturation < 92
    assert cases[2].review_action == "override"
    assert cases[2].override_reason
    assert cases[4].review_action is None
