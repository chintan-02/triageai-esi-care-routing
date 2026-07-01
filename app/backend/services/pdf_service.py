"""PDF generation service for persisted assessment reports."""

from __future__ import annotations

import json
import re
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
    KeepTogether,
    LongTable,
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

SAFETY_RULE_LABELS = {
    "oxygen_saturation_below_92": "Oxygen saturation below 92%",
    "oxygen_saturation_below_9_2": "Oxygen saturation below 92%",
    "abnormal_vitals": "Abnormal vital signs",
    "high_risk_chief_complaint": "High-risk chief complaint",
    "altered_mental_status": "Altered mental status",
    "altered_consciousness": "Altered mental status",
    "severe_pain": "Severe pain",
    "active_bleeding": "Active bleeding",
    "bleeding_red_flag": "Active bleeding",
    "pregnancy_high_risk": "Pregnancy-related risk flag",
    "pregnancy_bleeding_red_flag": "Pregnancy-related risk flag",
    "cardiopulmonary_red_flag": "Cardiopulmonary red flag",
}

VALUE_LABELS = {
    "accept": "Accept",
    "override": "Override",
    "needs_review": "Needs review",
    "model": "Model",
    "safety_rule_override": "Safety rule override",
    "assessment_created": "Assessment created",
    "prediction_generated": "Prediction generated",
    "clinician_review_accept": "Clinician review accepted",
    "clinician_review_override": "Clinician review override",
    "clinician_review_needs_review": "Clinician marked needs review",
    "pending_review": "Pending review",
    "needs_review": "Needs review",
    "review_completed": "Review completed",
}


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
    content_width = document.width
    story: list[Any] = []

    _add_header(story, styles, assessment, content_width)
    _add_disclaimer(story, styles)
    _add_patient_snapshot(story, styles, assessment, content_width)
    _add_model_output(story, styles, prediction, content_width)
    _add_safety_rules(story, styles, prediction, content_width)
    _add_narrative_sections(story, styles, prediction, content_width)
    _add_clinician_review(story, styles, prediction, clinician_review, content_width)
    if include_audit:
        _add_audit_trail(
            story,
            styles,
            assessment,
            prediction,
            clinician_review,
            audit_logs,
            content_width,
        )

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
        "callout": ParagraphStyle(
            "Callout",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#7A4B00"),
        ),
    }


def _add_header(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    content_width: float,
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
            content_width,
            [
                ("Generated", timestamp),
                ("Assessment ID", assessment.id),
                ("Patient ID", assessment.patient_id),
                ("Assessment status", _readable_value(assessment.status)),
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
    content_width: float,
) -> None:
    story.append(
        KeepTogether(
            [
                Paragraph("Patient / Intake Snapshot", styles["section"]),
                _key_value_table(
                    styles,
                    content_width,
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
                ),
            ]
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        _key_value_table(
            styles,
            content_width,
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
    content_width: float,
) -> None:
    if prediction is None:
        story.append(
            KeepTogether(
                [
                    Paragraph("Model Output", styles["section"]),
                    Paragraph("No model prediction is stored for this assessment.", styles["body"]),
                ]
            )
        )
        return

    probabilities = _json_or_default(prediction.probabilities_json, {})
    rows = [
        ("Model version", prediction.model_version),
        ("Model loaded", _bool_label(prediction.model_loaded)),
        ("Predicted ESI", _esi(prediction.predicted_esi)),
        ("Model final ESI", _esi(prediction.final_esi)),
        ("Confidence", _percent(prediction.confidence_score)),
        ("Final source", _readable_value(prediction.final_source)),
        ("ESI 3 probability", _percent(probabilities.get("ESI_3"))),
        ("ESI 4 probability", _percent(probabilities.get("ESI_4"))),
        ("ESI 5 probability", _percent(probabilities.get("ESI_5"))),
        ("Prediction timestamp", prediction.created_at),
    ]
    story.append(
        KeepTogether(
            [
                Paragraph("Model Output", styles["section"]),
                _key_value_table(styles, content_width, rows),
            ]
        )
    )


def _add_safety_rules(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
    content_width: float,
) -> None:
    if prediction is None:
        story.append(
            KeepTogether(
                [
                    Paragraph("Safety Rules", styles["section"]),
                    Paragraph("No model prediction is stored for this assessment.", styles["body"]),
                ]
            )
        )
        return

    rules = _json_or_default(prediction.safety_rules_json, [])
    triggered = [rule for rule in rules if isinstance(rule, dict) and rule.get("triggered")]
    if not triggered:
        story.append(
            KeepTogether(
                [
                    Paragraph("Safety Rules", styles["section"]),
                    Paragraph("No safety-rule escalation triggered.", styles["body"]),
                ]
            )
        )
        return

    table_rows = [
        [
            Paragraph("Safety flag", styles["label"]),
            Paragraph("Clinical meaning", styles["label"]),
        ]
    ]
    for rule in triggered:
        table_rows.append(
            [
                Paragraph(_safe(_safety_rule_label(rule.get("rule_id"))), styles["value"]),
                Paragraph(
                    _safe(rule.get("message") or "Safety-rule escalation triggered."),
                    styles["value"],
                ),
            ]
        )
    section = [
        Paragraph("Safety Rules", styles["section"]),
        _standard_table(table_rows, [content_width * 0.33, content_width * 0.67]),
    ]
    if len(triggered) <= 3:
        story.append(KeepTogether(section))
    else:
        story.extend(section)


def _maybe_pain_override_note(
    clinician_review: ClinicianReview | None,
) -> str | None:
    if clinician_review is None or clinician_review.action != "override":
        return None
    note_text = f"{clinician_review.override_reason or ''} {clinician_review.notes or ''}".lower()
    if "pain" not in note_text:
        return None
    return (
        "Pain score is considered with vitals, symptoms, and safety rules. "
        "A moderate pain score alone may not trigger model escalation."
    )


def _add_narrative_sections(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
    content_width: float,
) -> None:
    story.append(Paragraph("Recommendation And Explanation", styles["section"]))
    if prediction is None:
        story.append(Paragraph("No recommendation is stored for this assessment.", styles["body"]))
        return

    story.append(_note_box(styles, content_width, "Recommendation", prediction.recommendation))
    story.append(Spacer(1, 5))
    story.append(_note_box(styles, content_width, "Clinical explanation", prediction.explanation))
    story.append(Spacer(1, 5))
    story.append(_note_box(styles, content_width, "Clinician summary", prediction.clinician_summary))


def _add_clinician_review(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    content_width: float,
) -> None:
    if clinician_review is None:
        story.append(
            KeepTogether(
                [
                    Paragraph("Clinician Review", styles["section"]),
                    Paragraph("Pending clinician review.", styles["body"]),
                ]
            )
        )
        return

    section = [
        Paragraph("Clinician Review", styles["section"]),
        _key_value_table(
            styles,
            content_width,
            [
                ("Clinician decision", _readable_value(clinician_review.action)),
                ("Clinician final ESI", _esi(clinician_review.final_esi)),
                ("Override reason", clinician_review.override_reason),
                ("Review note", clinician_review.notes),
                ("Review timestamp", clinician_review.created_at),
                ("Review ID", clinician_review.id),
                ("Clinician ID", clinician_review.clinician_id),
            ],
        ),
    ]
    pain_note = _maybe_pain_override_note(clinician_review)
    if pain_note:
        section.extend([Spacer(1, 5), _callout_box(styles, content_width, pain_note)])
    if (
        prediction is not None
        and clinician_review.final_esi is not None
        and clinician_review.final_esi != prediction.final_esi
    ):
        section.extend([Spacer(1, 5), _callout_box(styles, content_width, MODEL_VS_CLINICIAN_NOTE)])
    story.append(KeepTogether(section))


def _add_audit_trail(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    audit_logs: list[AuditLog],
    content_width: float,
) -> None:
    story.append(Paragraph("Audit Trail", styles["section"]))
    events: list[tuple[Any, Any, Any, Any]] = [
        (
            assessment.created_at,
            "Assessment created",
            "System",
            {"status": _readable_value(assessment.status)},
        )
    ]
    if prediction is not None:
        events.append(
            (
                prediction.created_at,
                "Prediction generated",
                "System",
                {
                    "predicted_esi": prediction.predicted_esi,
                    "model_final_esi": prediction.final_esi,
                    "final_source": _readable_value(prediction.final_source),
                },
            )
        )
    if clinician_review is not None and not audit_logs:
        events.append(
            (
                clinician_review.created_at,
                _readable_value(f"clinician_review_{clinician_review.action}"),
                clinician_review.clinician_id,
                {
                    "clinician_decision": clinician_review.action,
                    "clinician_final_esi": clinician_review.final_esi,
                    "override_reason": clinician_review.override_reason,
                    "review_note": clinician_review.notes,
                },
            )
        )
    for audit_log in audit_logs:
        events.append(
            (
                audit_log.created_at,
                _readable_value(audit_log.action),
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
    story.append(
        _standard_table(
            table_rows,
            [
                content_width * 0.20,
                content_width * 0.22,
                content_width * 0.17,
                content_width * 0.41,
            ],
            long=True,
        )
    )


def _key_value_table(
    styles: dict[str, ParagraphStyle],
    content_width: float,
    rows: list[tuple[Any, Any]],
) -> Table:
    label_width = min(1.65 * inch, content_width * 0.26)
    table_rows = []
    for label, value in rows:
        table_rows.append(
            [
                Paragraph(_safe(_display(label)), styles["label"]),
                Paragraph(_safe(_display(value)), styles["value"]),
            ]
        )
    table = Table(table_rows, colWidths=[label_width, content_width - label_width])
    table.setStyle(_table_style(has_header=False))
    return table


def _note_box(
    styles: dict[str, ParagraphStyle],
    content_width: float,
    label: str,
    value: Any,
) -> Table:
    table = Table(
        [
            [Paragraph(_safe(label), styles["label"])],
            [Paragraph(_safe(value), styles["value"])],
        ],
        colWidths=[content_width],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F7FA")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#D7E2EA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _callout_box(
    styles: dict[str, ParagraphStyle],
    content_width: float,
    value: Any,
) -> Table:
    table = Table(
        [[Paragraph(_safe(value), styles["callout"])]],
        colWidths=[content_width],
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5B84F")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _standard_table(
    table_rows: list[list[Any]],
    col_widths: list[float],
    long: bool = False,
) -> Table:
    table_class = LongTable if long else Table
    table = table_class(table_rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(_table_style(has_header=True))
    return table


def _table_style(has_header: bool) -> TableStyle:
    commands: list[tuple[Any, ...]] = [
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E2EA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7E2EA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if has_header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF2")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFCFD")]),
            ]
        )
    else:
        commands.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#FAFCFD")]))
    return TableStyle(commands)


def _page_number(canvas: Any, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#526070"))
    canvas.drawCentredString(4.25 * inch, 0.35 * inch, REPORT_DISCLAIMER)
    canvas.drawRightString(7.95 * inch, 0.22 * inch, f"Page {document.page}")
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
        lines = _readable_detail_lines(payload)
        return "\n".join(lines) if lines else "Not documented"
    return _display(details)


def _readable_detail_lines(payload: dict[str, Any]) -> list[str]:
    field_labels = [
        ("action", "Clinician decision"),
        ("clinician_decision", "Clinician decision"),
        ("final_esi", "Clinician final ESI"),
        ("clinician_final_esi", "Clinician final ESI"),
        ("predicted_esi", "Predicted ESI"),
        ("model_final_esi", "Model final ESI"),
        ("final_source", "Final source"),
        ("override_reason", "Override reason"),
        ("review_note", "Review note"),
        ("notes", "Review note"),
        ("status", "Status"),
    ]
    lines = []
    for key, label in field_labels:
        if key in payload:
            lines.append(f"{label}: {_readable_detail_value(payload.get(key))}")
    if lines:
        return lines

    return [
        f"{_label_from_key(key)}: {_readable_detail_value(value)}"
        for key, value in payload.items()
        if key not in {"assessment_id", "clinician_id"}
    ]


def _readable_detail_value(value: Any) -> str:
    if value is None or value == "":
        return "Not documented"
    if isinstance(value, bool):
        return _bool_label(value)
    if isinstance(value, dict):
        nested_lines = _readable_detail_lines(value)
        return "; ".join(nested_lines) if nested_lines else "Not documented"
    return _readable_value(str(value))


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


def _safety_rule_label(rule_id: Any) -> str:
    raw_rule_id = _display(rule_id)
    normalized = raw_rule_id.lower().replace("/", "_").replace(" ", "_")
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    normalized = normalized.replace("oxygen_saturation_below_9_2", "oxygen_saturation_below_92")
    if normalized in SAFETY_RULE_LABELS:
        return SAFETY_RULE_LABELS[normalized]
    return _label_from_key(normalized)


def _label_from_key(value: str) -> str:
    return value.replace("_", " ").strip().title() or "Not documented"


def _readable_value(value: str) -> str:
    normalized = value.lower().replace(" ", "_")
    return VALUE_LABELS.get(normalized, _label_from_key(normalized))


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
