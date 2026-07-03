from app.frontend.streamlit_app import ui_theme


def test_public_card_helpers_render_without_returning_html(monkeypatch) -> None:
    rendered: list[str] = []

    monkeypatch.setattr(ui_theme.st, "html", rendered.append)

    assert (
        ui_theme.render_action_card("Review Dashboard", "Open workflow history.")
        is None
    )
    assert (
        ui_theme.render_kpi_card("Pending review", "Not triggered", tone="green")
        is None
    )
    assert (
        ui_theme.render_info_card("Audit trail", "Ready for review.", tone="blue")
        is None
    )

    assert len(rendered) == 3
    assert all("<div" in html for html in rendered)
    assert all("</div>" in html for html in rendered)


def test_display_formatting_helpers() -> None:
    assert (
        ui_theme.format_datetime_for_display("2026-07-03T02:45:49.205707")
        == "Jul 03, 2026 · 2:45 AM"
    )
    assert ui_theme.format_datetime_for_display("") == "Not documented"
    assert ui_theme.format_datetime_for_display("not-a-date") == "not-a-date"
    assert ui_theme.short_id("assessment-abcdef123456") == "assessme"
    assert ui_theme.short_id(None) == "Unavailable"


def test_humanize_label_helpers() -> None:
    assert ui_theme.humanize_label("review_completed") == "Review completed"
    assert ui_theme.humanize_label("pending_review") == "Pending review"
    assert ui_theme.humanize_label("safety_rule_override") == "Safety-rule escalation"
    assert ui_theme.humanize_label("model_tuned") == "Tuned model"
    assert ui_theme.humanize_label(True) == "Yes"
    assert ui_theme.humanize_label(False) == "No"
