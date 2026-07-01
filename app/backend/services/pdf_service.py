"""PDF generation service for persisted assessment reports."""

from __future__ import annotations

import json
import unicodedata
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.backend.db.models import Assessment, AuditLog, ClinicianReview, Prediction


REPORT_DISCLAIMER = (
    "This report is for clinical decision-support workflow testing only and is "
    "not a diagnosis or a substitute for clinician judgment."
)

MODEL_VS_CLINICIAN_NOTE = (
    "Model recommendation was based on structured intake data. The clinician final "
    "ESI may differ when additional clinical context, safety concerns, or patient "
    "presentation justify an override. Overrides require a reason and are stored "
    "in the audit trail."
)


def report_file_name(report_id: str) -> str:
    return f"triageai_report_{report_id}.pdf"


def report_file_path(output_dir: str | Path, report_id: str) -> Path:
    return Path(output_dir) / report_file_name(report_id)


def generate_assessment_report_pdf(
    *,
    assessment: Assessment,
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    audit_logs: list[AuditLog],
    report_id: str,
    output_dir: str | Path,
    include_audit: bool = True,
) -> Path:
    output_path = report_file_path(output_dir, report_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.55 * inch,
        title=f"TriageAI Assessment Report {assessment.id}",
    )
    styles = _styles()
    story: list[Any] = []

    _add_header(story, styles, assessment)
    _add_disclaimer(story, styles)
    _add_patient_snapshot(story, styles, assessment)
    _add_model_output(story, styles, prediction)
    _add_safety_rules(story, styles, prediction)
    _add_narrative_sections(story, styles, prediction)
    _add_clinician_review(story, styles, prediction, clinician_review)
    if include_audit:
        _add_audit_trail(story, styles, assessment, prediction, clinician_review, audit_logs)
    _add_footer(story, styles)

    document.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return output_path


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0E1F35"),
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#526070"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0E1F35"),
            spaceBefore=9,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E3A52"),
            spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "TableLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#526070"),
        ),
        "value": ParagraphStyle(
            "TableValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0E1F35"),
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#7A4B00"),
            backColor=colors.HexColor("#FFF7DB"),
            borderColor=colors.HexColor("#E5B84F"),
            borderWidth=0.5,
            borderPadding=6,
            spaceAfter=7,
        ),
        "footer": ParagraphStyle(
            "FooterNote",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#526070"),
            alignment=TA_CENTER,
        ),
    }


def _add_header(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph("TriageAI / SympDirect", styles["title"]))
    story.append(
        Paragraph(
            "ESI Clinical Intake & Care Routing Assistant<br/>"
            "Report type: Assessment Decision-Support Summary",
            styles["subtitle"],
        )
    )
    story.append(
        _key_value_table(
            styles,
            [
                ("Generated", timestamp),
                ("Assessment ID", assessment.id),
                ("Patient ID", assessment.patient_id),
                ("Assessment status", assessment.status),
            ],
        )
    )


def _add_disclaimer(story: list[Any], styles: dict[str, ParagraphStyle]) -> None:
    story.append(Spacer(1, 5))
    story.append(Paragraph(_safe(REPORT_DISCLAIMER), styles["disclaimer"]))


def _add_patient_snapshot(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
) -> None:
    story.append(Paragraph("Patient / Intake Snapshot", styles["section"]))
    story.append(
        _key_value_table(
            styles,
            [
                ("Age", getattr(assessment.patient, "age", None)),
                ("Gender/Sex", getattr(assessment.patient, "sex", None)),
                ("Chief complaint", assessment.chief_complaint),
                ("Symptom duration", assessment.symptom_duration),
                ("Arrival mode", assessment.arrival_mode),
                ("Consciousness level", assessment.consciousness_level),
                ("Pregnancy", _bool_label(assessment.pregnancy)),
                ("Additional context", assessment.additional_context),
            ],
        )
    )
    story.append(
        _key_value_table(
            styles,
            [
                ("Temperature", _unit(assessment.temperature_c, "C")),
                ("Heart rate", _unit(assessment.heart_rate, "bpm")),
                ("Respiratory rate", _unit(assessment.respiratory_rate, "/min")),
                ("Blood pressure", _blood_pressure(assessment)),
                ("Oxygen saturation", _unit(assessment.oxygen_saturation, "%")),
                ("Pain score", _unit(assessment.pain_score, "/10")),
            ],
        )
    )


def _add_model_output(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
) -> None:
    story.append(Paragraph("Model Output", styles["section"]))
    if prediction is None:
        story.append(Paragraph("No model prediction is stored for this assessment.", styles["body"]))
        return

    story.append(
        _key_value_table(
            styles,
            [
                ("Model version", prediction.model_version),
                ("Model loaded", _bool_label(prediction.model_loaded)),
                ("Predicted ESI", _esi(prediction.predicted_esi)),
                ("Model final ESI", _esi(prediction.final_esi)),
                ("Confidence", _percent(prediction.confidence_score)),
                ("Final source", prediction.final_source),
                ("Prediction timestamp", prediction.created_at),
            ],
        )
    )

    probabilities = _json_or_default(prediction.probabilities_json, {})
    rows = [("ESI 3 probability", _percent(probabilities.get("ESI_3")))]
    rows.append(("ESI 4 probability", _percent(probabilities.get("ESI_4"))))
    rows.append(("ESI 5 probability", _percent(probabilities.get("ESI_5"))))
    story.append(_key_value_table(styles, rows))


def _add_safety_rules(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
) -> None:
    story.append(Paragraph("Safety Rules", styles["section"]))
    if prediction is None:
        story.append(Paragraph("No model prediction is stored for this assessment.", styles["body"]))
        return

    rules = _json_or_default(prediction.safety_rules_json, [])
    triggered = [rule for rule in rules if isinstance(rule, dict) and rule.get("triggered")]
    if not triggered:
        story.append(Paragraph("No safety-rule escalation triggered.", styles["body"]))
        return

    rows = [
        (
            rule.get("rule_id", "safety_rule"),
            rule.get("message", "Safety-rule escalation triggered."),
        )
        for rule in triggered
    ]
    story.append(_key_value_table(styles, rows))


def _add_narrative_sections(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
) -> None:
    story.append(Paragraph("Recommendation And Explanation", styles["section"]))
    if prediction is None:
        story.append(Paragraph("No recommendation is stored for this assessment.", styles["body"]))
        return

    story.append(_paragraph_block(styles, "Recommendation", prediction.recommendation))
    story.append(_paragraph_block(styles, "Clinical explanation", prediction.explanation))
    story.append(_paragraph_block(styles, "Clinician summary", prediction.clinician_summary))


def _add_clinician_review(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
) -> None:
    story.append(Paragraph("Clinician Review", styles["section"]))
    if clinician_review is None:
        story.append(Paragraph("Pending clinician review.", styles["body"]))
        return

    story.append(
        _key_value_table(
            styles,
            [
                ("Clinician decision", clinician_review.action),
                ("Clinician final ESI", _esi(clinician_review.final_esi)),
                ("Override reason", clinician_review.override_reason),
                ("Review note", clinician_review.notes),
                ("Review timestamp", clinician_review.created_at),
                ("Review ID", clinician_review.id),
                ("Clinician ID", clinician_review.clinician_id),
            ],
        )
    )
    if (
        prediction is not None
        and clinician_review.final_esi is not None
        and clinician_review.final_esi != prediction.final_esi
    ):
        story.append(Paragraph(_safe(MODEL_VS_CLINICIAN_NOTE), styles["disclaimer"]))


def _add_audit_trail(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    audit_logs: list[AuditLog],
) -> None:
    story.append(Paragraph("Audit Trail", styles["section"]))
    events: list[tuple[Any, Any, Any, Any]] = [
        (
            assessment.created_at,
            "assessment_created",
            "System",
            {"status": assessment.status},
        )
    ]
    if prediction is not None:
        events.append(
            (
                prediction.created_at,
                "prediction_generated",
                "System",
                {
                    "predicted_esi": prediction.predicted_esi,
                    "final_esi": prediction.final_esi,
                    "final_source": prediction.final_source,
                },
            )
        )
    if clinician_review is not None and not audit_logs:
        events.append(
            (
                clinician_review.created_at,
                f"clinician_review_{clinician_review.action}",
                clinician_review.clinician_id,
                {
                    "clinician_final_esi": clinician_review.final_esi,
                    "override_reason": clinician_review.override_reason,
                },
            )
        )
    for audit_log in audit_logs:
        events.append(
            (
                audit_log.created_at,
                audit_log.action,
                audit_log.actor_id,
                _json_or_default(audit_log.details_json, None),
            )
        )

    table_rows = [
        [
            Paragraph("Timestamp", styles["label"]),
            Paragraph("Action", styles["label"]),
            Paragraph("Actor", styles["label"]),
            Paragraph("Details", styles["label"]),
        ]
    ]
    for timestamp, action, actor, details in events:
        table_rows.append(
            [
                Paragraph(_safe(_display(timestamp)), styles["value"]),
                Paragraph(_safe(_display(action)), styles["value"]),
                Paragraph(_safe(_display(actor)), styles["value"]),
                Paragraph(_safe(_details_text(details)), styles["value"]),
            ]
        )
    table = Table(table_rows, colWidths=[1.35 * inch, 1.45 * inch, 1.15 * inch, 3.0 * inch])
    table.setStyle(_table_style())
    story.append(table)


def _add_footer(story: list[Any], styles: dict[str, ParagraphStyle]) -> None:
    story.append(Spacer(1, 10))
    story.append(Paragraph(_safe(REPORT_DISCLAIMER), styles["footer"]))
    story.append(
        Paragraph(
            "Generated by TriageAI for ESI decision-support workflow review.",
            styles["footer"],
        )
    )


def _key_value_table(
    styles: dict[str, ParagraphStyle],
    rows: list[tuple[Any, Any]],
) -> Table:
    table_rows = []
    for label, value in rows:
        table_rows.append(
            [
                Paragraph(_safe(_display(label)), styles["label"]),
                Paragraph(_safe(_display(value)), styles["value"]),
            ]
        )
    table = Table(table_rows, colWidths=[1.65 * inch, 5.25 * inch])
    table.setStyle(_table_style())
    return table


def _paragraph_block(
    styles: dict[str, ParagraphStyle],
    label: str,
    value: Any,
) -> Table:
    return _key_value_table(styles, [(label, value)])


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F7FA")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFCFD")]),
            ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E2EA")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7E2EA")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _page_number(canvas: Any, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#526070"))
    canvas.drawRightString(7.95 * inch, 0.35 * inch, f"Page {document.page}")
    canvas.restoreState()


def _json_or_default(raw_value: str | None, default: Any) -> Any:
    if not raw_value:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def _details_text(details: Any) -> str:
    if details is None:
        return "Not documented"
    if isinstance(details, dict):
        payload = details.get("payload") if isinstance(details.get("payload"), dict) else details
        return json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return _display(details)


def _safe(value: Any) -> str:
    text = _display(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return escape(text).replace("\n", "<br/>")


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Not documented"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M UTC")
    if isinstance(value, bool):
        return _bool_label(value)
    return str(value)


def _bool_label(value: bool | None) -> str:
    if value is None:
        return "Not documented"
    return "True" if value else "False"


def _esi(value: int | None) -> str:
    return "Not documented" if value is None else f"ESI {value}"


def _percent(value: Any) -> str:
    if value is None:
        return "Not documented"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "Not documented"


def _unit(value: Any, unit: str) -> str:
    if value is None or value == "":
        return "Not documented"
    return f"{value} {unit}"


def _blood_pressure(assessment: Assessment) -> str:
    if assessment.systolic_bp is None and assessment.diastolic_bp is None:
        return "Not documented"
    return f"{_display(assessment.systolic_bp)}/{_display(assessment.diastolic_bp)} mmHg"
