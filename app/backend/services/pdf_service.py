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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Flowable,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.backend.db.models import Assessment, AuditLog, ClinicianReview, Prediction


REPORT_DISCLAIMER = (
    "This report supports structured triage review and ESI care routing. It is "
    "decision-support only and does not replace clinician judgment, emergency "
    "protocols, or required clinician review."
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
    "nlp_extraction_reviewed": "Clinical NLP extraction reviewed",
    "pending_review": "Pending review",
    "needs_review": "Needs review",
    "review_completed": "Review completed",
}

NAVY = colors.HexColor("#0B1B33")
TEAL = colors.HexColor("#0D9488")
SLATE_TEXT = colors.HexColor("#334155")
SLATE_MUTED = colors.HexColor("#64748B")
SLATE_LINE = colors.HexColor("#DCE5EF")
SLATE_SOFT = colors.HexColor("#F8FAFC")
AMBER_SOFT = colors.HexColor("#FFF7ED")
RED_SOFT = colors.HexColor("#FEF2F2")
GREEN_SOFT = colors.HexColor("#ECFDF5")
GREEN = colors.HexColor("#047857")

NLP_EVIDENCE_FIELDS = {
    "age",
    "gender",
    "chief_complaint",
    "symptom",
    "symptoms",
    "triage_vital_hr",
    "triage_vital_sbp",
    "triage_vital_dbp",
    "triage_vital_rr",
    "triage_vital_o2",
    "triage_vital_temp",
}

ESI_COLORS = {
    1: colors.HexColor("#7F1D1D"),
    2: colors.HexColor("#DC2626"),
    3: colors.HexColor("#D97706"),
    4: colors.HexColor("#2563EB"),
    5: colors.HexColor("#16A34A"),
}


class HeaderBand(Flowable):
    """Rounded navy report header modeled after the legacy frontend PDF."""

    def __init__(
        self,
        *,
        width: float,
        assessment: Assessment,
        prediction: Prediction | None,
        clinician_review: ClinicianReview | None,
        generated_at: datetime,
    ) -> None:
        super().__init__()
        self.width = width
        self.height = 92
        self.assessment = assessment
        self.prediction = prediction
        self.clinician_review = clinician_review
        self.generated_at = generated_at

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv
        final_esi = _report_final_esi(self.prediction, self.clinician_review)
        badge_color = ESI_COLORS.get(final_esi, TEAL)
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.roundRect(0, 0, self.width, self.height, 12, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(18, 63, "Clinical ESI Routing Summary")
        canvas.setFillColor(colors.HexColor("#D9E7F5"))
        canvas.setFont("Helvetica", 9.5)
        canvas.drawString(18, 45, "Human-in-the-loop ESI care routing report - decision-support only")
        canvas.setFillColor(colors.HexColor("#BED0E3"))
        canvas.setFont("Helvetica", 8.1)
        canvas.drawString(18, 25, f"Assessment ID: {_display(self.assessment.id)}")
        canvas.drawString(18, 12, f"Generated time: {_display(self.generated_at)}")

        badge_width = 98
        badge_x = self.width - badge_width - 18
        canvas.setFillColor(badge_color)
        canvas.roundRect(badge_x, 47, badge_width, 30, 8, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawCentredString(badge_x + badge_width / 2, 58, f"FINAL {_esi_badge(final_esi)}")
        canvas.setFillColor(colors.HexColor("#D9E7F5"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(self.width - 18, 29, f"Assessment time: {_display(getattr(self.prediction, 'created_at', None) or self.assessment.created_at)}")
        if self.clinician_review is not None:
            canvas.drawRightString(self.width - 18, 15, f"Reviewed time: {_display(self.clinician_review.created_at)}")
        else:
            canvas.drawRightString(self.width - 18, 15, "Reviewed time: Pending review")
        canvas.restoreState()


class FinalDecisionCard(Flowable):
    """Large first-page routing card with ESI badge and compact metrics."""

    def __init__(
        self,
        *,
        width: float,
        styles: dict[str, ParagraphStyle],
        assessment: Assessment,
        prediction: Prediction | None,
        clinician_review: ClinicianReview | None,
    ) -> None:
        super().__init__()
        self.width = width
        self.height = 132
        self.styles = styles
        self.assessment = assessment
        self.prediction = prediction
        self.clinician_review = clinician_review

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv
        final_esi = _report_final_esi(self.prediction, self.clinician_review)
        predicted_esi = self.prediction.predicted_esi if self.prediction is not None else None
        badge_color = ESI_COLORS.get(final_esi, TEAL)
        canvas.saveState()
        canvas.setStrokeColor(SLATE_LINE)
        canvas.setFillColor(colors.white)
        canvas.roundRect(0, 0, self.width, self.height, 10, stroke=1, fill=1)

        canvas.setFillColor(badge_color)
        canvas.roundRect(14, self.height - 66, 96, 48, 9, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawCentredString(62, self.height - 31, "FINAL ROUTING")
        canvas.setFont("Helvetica-Bold", 17)
        canvas.drawCentredString(62, self.height - 49, _esi_badge(final_esi))

        summary = Paragraph(_safe(_final_decision_summary(self.prediction, self.clinician_review)), self.styles["value_bold"])
        summary.wrapOn(canvas, self.width - 142, 35)
        summary.drawOn(canvas, 126, self.height - 38)
        safety = Paragraph(_safe(f"Safety gate: {_safety_gate_result_text(self.prediction)}"), self.styles["body"])
        safety.wrapOn(canvas, self.width - 142, 22)
        safety.drawOn(canvas, 126, self.height - 62)

        metrics = [
            ("Model prediction", _esi(predicted_esi)),
            ("Confidence", _percent(self.prediction.confidence_score if self.prediction else None)),
            ("Latency", _latency_ms(self.prediction)),
            ("Safety gate", _safety_gate_status(self.prediction)),
            ("Clinician review", _review_status(self.clinician_review)),
            ("Assessment time", _display(getattr(self.prediction, "created_at", None) or self.assessment.created_at)),
        ]
        metric_gap = 6
        metric_width = (self.width - 28 - metric_gap * 2) / 3
        metric_height = 24
        for index, (label, value) in enumerate(metrics):
            col = index % 3
            row = index // 3
            x = 14 + col * (metric_width + metric_gap)
            y = 12 + (1 - row) * 28
            canvas.setFillColor(SLATE_SOFT)
            canvas.roundRect(x, y, metric_width, metric_height, 4, stroke=0, fill=1)
            canvas.setFillColor(SLATE_MUTED)
            canvas.setFont("Helvetica-Bold", 6.3)
            canvas.drawString(x + 6, y + metric_height - 8, label.upper())
            value_paragraph = Paragraph(
                _safe(_display(value)),
                self.styles["metric_chip_value"],
            )
            value_paragraph.wrapOn(canvas, metric_width - 12, 11)
            value_paragraph.drawOn(canvas, x + 6, y + 4)
        canvas.restoreState()


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
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.55 * inch,
        title=f"TriageAI Assessment Report {assessment.id}",
    )
    styles = _styles()
    content_width = document.width
    generated_at = datetime.now(timezone.utc)
    story: list[Any] = []

    _add_header(story, styles, assessment, prediction, clinician_review, content_width, generated_at)
    _add_final_decision(story, styles, assessment, prediction, clinician_review, content_width)
    _add_model_metadata(story, styles, assessment, prediction, content_width)
    _add_patient_snapshot(
        story,
        styles,
        assessment,
        prediction,
        content_width,
        include_symptom_narrative=_nlp_review_details(audit_logs) is None,
    )
    _add_vitals_table(story, styles, assessment, content_width)
    story.append(PageBreak())
    _add_model_and_safety_columns(story, styles, prediction, content_width)
    _add_clinician_review(story, styles, prediction, clinician_review, content_width)
    _add_clinical_nlp_review_evidence(
        story,
        styles,
        audit_logs,
        content_width,
    )
    if include_audit:
        _add_audit_trail(
            story,
            styles,
            assessment,
            prediction,
            clinician_review,
            audit_logs,
            content_width,
            generated_at,
        )

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output_path


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "header_title": ParagraphStyle(
            "HeaderTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "header_subtitle": ParagraphStyle(
            "HeaderSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#D9E7F5"),
            alignment=TA_LEFT,
        ),
        "header_meta": ParagraphStyle(
            "HeaderMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=11,
            textColor=colors.HexColor("#BED0E3"),
            alignment=TA_LEFT,
        ),
        "esi_badge": ParagraphStyle(
            "EsiBadge",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "esi_badge_label": ParagraphStyle(
            "EsiBadgeLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#F8FAFC"),
            alignment=TA_CENTER,
        ),
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
            fontSize=12,
            leading=15,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "ReportBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=11.5,
            textColor=SLATE_TEXT,
            spaceAfter=4,
        ),
        "label": ParagraphStyle(
            "TableLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.6,
            leading=9.5,
            textColor=SLATE_MUTED,
        ),
        "value": ParagraphStyle(
            "TableValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=10.5,
            textColor=NAVY,
        ),
        "value_bold": ParagraphStyle(
            "TableValueBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=10.8,
            textColor=NAVY,
        ),
        "metric_label": ParagraphStyle(
            "MetricLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.5,
            textColor=SLATE_MUTED,
            alignment=TA_CENTER,
        ),
        "metric_value": ParagraphStyle(
            "MetricValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "metric_chip_value": ParagraphStyle(
            "MetricChipValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.2,
            leading=8,
            textColor=NAVY,
            alignment=TA_RIGHT,
        ),
        "right_value": ParagraphStyle(
            "RightValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=10.5,
            textColor=NAVY,
            alignment=TA_RIGHT,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.6,
            leading=9.5,
            textColor=colors.white,
        ),
        "vital_header": ParagraphStyle(
            "VitalHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.6,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "vital_value": ParagraphStyle(
            "VitalValue",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=10.5,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "vital_abnormal": ParagraphStyle(
            "VitalAbnormal",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=10.5,
            textColor=colors.HexColor("#92400E"),
            alignment=TA_CENTER,
        ),
        "vital_critical": ParagraphStyle(
            "VitalCritical",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=10.5,
            textColor=colors.HexColor("#991B1B"),
            alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#7C2D12"),
            backColor=AMBER_SOFT,
            borderColor=colors.HexColor("#FDBA74"),
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
            textColor=colors.HexColor("#7C2D12"),
        ),
    }


def _add_header(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    content_width: float,
    generated_at: datetime,
) -> None:
    story.append(
        HeaderBand(
            width=content_width,
            assessment=assessment,
            prediction=prediction,
            clinician_review=clinician_review,
            generated_at=generated_at,
        )
    )
    story.append(Spacer(1, 6))


def _add_final_decision(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    content_width: float,
) -> None:
    story.append(Paragraph("Final Routing Decision", styles["section"]))
    story.append(
        FinalDecisionCard(
            width=content_width,
            styles=styles,
            assessment=assessment,
            prediction=prediction,
            clinician_review=clinician_review,
        )
    )
    story.append(Spacer(1, 5))


def _add_model_metadata(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    prediction: Prediction | None,
    content_width: float,
) -> None:
    story.append(
        _key_value_table(
            styles,
            content_width,
            [
                ("Request ID", prediction.id if prediction is not None else "Not captured"),
                ("Model Version", prediction.model_version if prediction is not None else "Not captured"),
                ("Threshold Profile", _threshold_profile_text(prediction)),
                ("Model Scope", "Clinical decision-support classifier predicts ESI 3/4/5; safety gate and clinician review handle ESI 1/2 escalation"),
                ("Assessment ID", assessment.id),
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
    prediction: Prediction | None,
    content_width: float,
    include_symptom_narrative: bool = True,
) -> None:
    intake_rows = [
        ("Patient", _patient_summary(assessment)),
        ("MRN", _patient_mrn(assessment)),
        ("Arrival Mode", assessment.arrival_mode),
        ("Chief Complaint", assessment.chief_complaint),
    ]
    if include_symptom_narrative:
        intake_rows.append(("Symptom Narrative", assessment.additional_context))
    intake_rows.extend(
        [
            ("Duration", assessment.symptom_duration),
            ("Selected risk flags", _risk_flags_text(prediction)),
            ("Comorbidities", "None selected"),
            ("Consciousness level", assessment.consciousness_level),
        ]
    )
    story.append(
        KeepTogether(
            [
                Paragraph("Patient & Intake Summary", styles["section"]),
                _key_value_table(
                    styles,
                    content_width,
                    intake_rows,
                ),
            ]
        )
    )


def _add_vitals_table(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    content_width: float,
) -> None:
    rows = _vital_cells(assessment)
    table_rows = [
        [Paragraph(_safe(label), styles["vital_header"]) for label, _, _ in rows],
        [
            Paragraph(_safe(f"{value}\n{status}"), _vital_style(styles, status))
            for _, value, status in rows
        ],
    ]
    table = Table(table_rows, colWidths=[content_width / 6] * 6)
    commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.4, SLATE_LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, SLATE_LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for index, (_, _, status) in enumerate(rows):
        if status != "Documented":
            commands.append(("BACKGROUND", (index, 1), (index, 1), RED_SOFT if status == "Critical display range" else AMBER_SOFT))
    table.setStyle(TableStyle(commands))
    story.append(KeepTogether([Paragraph("Vitals", styles["section"]), table, Spacer(1, 4), Paragraph("Highlighted values support review visibility; backend safety thresholds remain authoritative.", styles["body"])]))


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
    probability_rows = [
        [
            Paragraph("Class", styles["label"]),
            Paragraph("Probability", styles["label"]),
            Paragraph("Visual weight", styles["label"]),
        ],
        *[
            [
                Paragraph(_safe(label.replace("_", " ")), styles["value_bold"]),
                Paragraph(_safe(_percent(probabilities.get(label))), styles["right_value"]),
                _probability_bar(styles, probabilities.get(label)),
            ]
            for label in ("ESI_3", "ESI_4", "ESI_5")
        ],
    ]
    probability_table = _standard_table(
        probability_rows,
        [content_width * 0.22, content_width * 0.20, content_width * 0.58],
    )
    metadata = _key_value_table(
        styles,
        content_width,
        [
            ("Model version", prediction.model_version),
            ("Model loaded", _bool_label(prediction.model_loaded)),
            ("Predicted ESI", _esi(prediction.predicted_esi)),
            ("Model final ESI", _esi(prediction.final_esi)),
            ("Confidence", _percent(prediction.confidence_score)),
            ("Final source", _readable_value(prediction.final_source)),
            ("Prediction timestamp", prediction.created_at),
        ],
    )
    story.append(
        KeepTogether(
            [
                Paragraph("Model Output Probabilities", styles["section"]),
                probability_table,
                Spacer(1, 6),
                metadata,
            ]
        )
    )


def _add_model_and_safety_columns(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
    content_width: float,
) -> None:
    column_gap = 0.18 * inch
    column_width = (content_width - column_gap) / 2
    left: list[Any] = [Paragraph("Model Output Probabilities", styles["section"])]
    right: list[Any] = [Paragraph("Safety Rules & Recommendation", styles["section"])]

    if prediction is None:
        left.append(Paragraph("No model prediction is stored for this assessment.", styles["body"]))
        right.append(Paragraph("No safety-rule output is stored for this assessment.", styles["body"]))
    else:
        probabilities = _json_or_default(prediction.probabilities_json, {})
        probability_rows = [
            [
                Paragraph("Class", styles["table_header"]),
                Paragraph("Probability", styles["table_header"]),
                Paragraph("Visual weight", styles["table_header"]),
            ],
            *[
                [
                    Paragraph(_safe(label.replace("_", " ")), styles["value_bold"]),
                    Paragraph(_safe(_percent(probabilities.get(label))), styles["right_value"]),
                    _probability_bar(
                        styles,
                        probabilities.get(label),
                        width=column_width * 0.42,
                        accent=label == _top_probability_label(probabilities),
                    ),
                ]
                for label in ("ESI_3", "ESI_4", "ESI_5")
            ],
        ]
        left.append(
            _standard_table(
                probability_rows,
                [column_width * 0.25, column_width * 0.25, column_width * 0.50],
            )
        )
        left.append(Spacer(1, 5))
        left.append(Paragraph("Raw model probabilities are shown for transparency and are not calibrated probabilities.", styles["body"]))

        right.append(
            _standard_table(
                [
                    [Paragraph("Signal", styles["table_header"]), Paragraph("Value", styles["table_header"])],
                    [Paragraph("Rules Fired", styles["value_bold"]), Paragraph(_safe(_rules_fired_text(prediction)), styles["value"])],
                    [Paragraph("Safety Gate Result", styles["value_bold"]), Paragraph(_safe(_safety_gate_result_text(prediction)), styles["value"])],
                    [Paragraph("Explanation", styles["value_bold"]), Paragraph(_safe(_short_text(_pdf_explanation_text(prediction.explanation), 360)), styles["value"])],
                    [Paragraph("Recommendation", styles["value_bold"]), Paragraph(_safe(_short_text(prediction.recommendation, 220)), styles["value"])],
                ],
                [column_width * 0.30, column_width * 0.70],
            )
        )

    grid = Table([[left, "", right]], colWidths=[column_width, column_gap, column_width])
    grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(grid)
    story.append(Spacer(1, 8))


def _add_safety_rules_and_recommendation(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    prediction: Prediction | None,
    content_width: float,
) -> None:
    if prediction is None:
        story.append(
            KeepTogether(
                [
                    Paragraph("Safety Rules & Recommendation", styles["section"]),
                    Paragraph("No model prediction is stored for this assessment.", styles["body"]),
                ]
            )
        )
        return

    rules = _json_or_default(prediction.safety_rules_json, [])
    triggered = [rule for rule in rules if isinstance(rule, dict) and rule.get("triggered")]
    section: list[Any] = [Paragraph("Safety Rules & Recommendation", styles["section"])]
    if not triggered:
        section.append(_status_box(styles, content_width, "No safety-rule escalation triggered.", GREEN_SOFT, GREEN))
    else:
        table_rows = [
            [
                Paragraph("Safety flag", styles["table_header"]),
                Paragraph("Clinical meaning", styles["table_header"]),
            ]
        ]
        for rule in triggered:
            table_rows.append(
                [
                    Paragraph(_safe(_safety_rule_label(rule.get("rule_id"))), styles["value_bold"]),
                    Paragraph(
                        _safe(rule.get("message") or "Safety-rule escalation triggered."),
                        styles["value"],
                    ),
                ]
            )
        section.append(
            _standard_table(table_rows, [content_width * 0.33, content_width * 0.67])
        )
    section.extend(
        [
            Spacer(1, 6),
            _note_box(styles, content_width, "Recommendation", prediction.recommendation),
            Spacer(1, 5),
            _note_box(styles, content_width, "Clinical explanation", _pdf_explanation_text(prediction.explanation)),
            Spacer(1, 5),
            _note_box(styles, content_width, "Clinician summary", prediction.clinician_summary),
        ]
    )
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
                    _key_value_table(
                        styles,
                        content_width,
                        [
                            ("Status", "Pending review"),
                            ("Reviewer", "Unassigned"),
                            ("Final clinician decision", "Not yet reviewed"),
                            ("Reviewed time", "Not yet reviewed"),
                            ("Note", "Awaiting human-in-the-loop clinician review."),
                        ],
                    ),
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
                ("Status", _readable_value(clinician_review.action)),
                ("Reviewer", clinician_review.clinician_id),
                ("Final clinician decision", _esi(clinician_review.final_esi)),
                ("Reviewed time", clinician_review.created_at),
                ("Note", clinician_review.notes or clinician_review.override_reason),
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


def _nlp_review_details(audit_logs: list[AuditLog]) -> dict[str, Any] | None:
    for audit_log in reversed(audit_logs):
        if audit_log.action != "nlp_extraction_reviewed":
            continue
        details = _json_or_default(audit_log.details_json, None)
        if not isinstance(details, dict):
            return {}
        payload = details.get("payload")
        if isinstance(payload, dict):
            return {**details, **payload}
        return details
    return None


def _nlp_text(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _nlp_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _nlp_text(item)) is not None]


def _nlp_vitals_text(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None

    systolic = _nlp_text(value.get("sbp"))
    diastolic = _nlp_text(value.get("dbp"))
    blood_pressure = (
        f"{systolic or '-'}/{diastolic or '-'}"
        if systolic is not None or diastolic is not None
        else None
    )
    vital_values = [
        ("HR", _nlp_text(value.get("hr"))),
        ("BP", blood_pressure),
        ("RR", _nlp_text(value.get("rr"))),
        ("O2", _nlp_text(value.get("o2"))),
        ("Temp", _nlp_text(value.get("temp"))),
    ]
    rendered = [f"{label}: {reading}" for label, reading in vital_values if reading]
    return "; ".join(rendered) or None


def _nlp_extracted_field_rows(details: dict[str, Any]) -> list[tuple[str, str]]:
    extracted_fields = details.get("extracted_fields")
    if not isinstance(extracted_fields, dict):
        return []

    symptoms = _nlp_text_list(extracted_fields.get("symptoms"))
    candidates = [
        ("Age", _nlp_text(extracted_fields.get("age"))),
        ("Gender", _nlp_text(extracted_fields.get("gender"))),
        ("Chief complaint", _nlp_text(extracted_fields.get("chief_complaint"))),
        ("Symptoms", "; ".join(symptoms) or None),
        ("Vitals", _nlp_vitals_text(extracted_fields.get("vitals"))),
    ]
    return [(label, value) for label, value in candidates if value]


def _nlp_evidence_rows(details: dict[str, Any]) -> list[tuple[str, str, str]]:
    evidence = details.get("evidence")
    if not isinstance(evidence, list):
        return []

    rows: list[tuple[str, str, str]] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        field = _nlp_text(item.get("field"))
        value = _nlp_text(item.get("value"))
        if value is None and isinstance(item.get("value"), list):
            value = "; ".join(_nlp_text_list(item.get("value"))) or None
        snippet = _nlp_text(item.get("text"))
        if not field or field not in NLP_EVIDENCE_FIELDS or not value or not snippet:
            continue
        rows.append(
            (
                _nlp_evidence_field_label(field),
                _short_text(value, 100),
                _short_text(snippet, 240),
            )
        )
    return rows


def _nlp_evidence_field_label(field: str) -> str:
    labels = {
        "age": "Age",
        "gender": "Gender",
        "chief_complaint": "Chief complaint",
        "symptom": "Symptom",
        "symptoms": "Symptoms",
        "triage_vital_hr": "HR",
        "triage_vital_sbp": "Systolic BP",
        "triage_vital_dbp": "Diastolic BP",
        "triage_vital_rr": "RR",
        "triage_vital_o2": "O2",
        "triage_vital_temp": "Temperature",
    }
    return labels[field]


def _add_clinical_nlp_review_evidence(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    audit_logs: list[AuditLog],
    content_width: float,
) -> None:
    details = _nlp_review_details(audit_logs)
    if details is None:
        return

    story.append(Paragraph("Clinical NLP Review Evidence", styles["section"]))
    story.append(
        _status_box(
            styles,
            content_width,
            "Reviewed before prediction",
            GREEN_SOFT,
            GREEN,
        )
    )

    message = _nlp_text(details.get("message"))
    if message:
        story.extend(
            [
                Spacer(1, 5),
                Paragraph(_safe(_short_text(message, 320)), styles["body"]),
            ]
        )

    context_rows: list[tuple[str, str]] = []
    safety_cues = _nlp_text_list(details.get("safety_cues"))
    missing_fields = _nlp_text_list(details.get("missing_fields"))
    if safety_cues:
        context_rows.append(("Safety cues", "; ".join(safety_cues)))
    if missing_fields:
        context_rows.append(("Missing fields", "; ".join(missing_fields)))
    if context_rows:
        story.extend(
            [
                Spacer(1, 5),
                _key_value_table(styles, content_width, context_rows),
            ]
        )

    extracted_rows = _nlp_extracted_field_rows(details)
    if extracted_rows:
        story.extend(
            [
                Spacer(1, 6),
                Paragraph("Extracted fields", styles["value_bold"]),
                Spacer(1, 3),
                _key_value_table(styles, content_width, extracted_rows),
            ]
        )

    evidence_rows = _nlp_evidence_rows(details)
    if evidence_rows:
        table_rows = [
            [
                Paragraph("Field", styles["table_header"]),
                Paragraph("Value", styles["table_header"]),
                Paragraph("Text snippet", styles["table_header"]),
            ],
            *[
                [
                    Paragraph(_safe(field), styles["value_bold"]),
                    Paragraph(_safe(value), styles["value"]),
                    Paragraph(_safe(snippet), styles["value"]),
                ]
                for field, value, snippet in evidence_rows
            ],
        ]
        story.extend(
            [
                Spacer(1, 6),
                Paragraph("Evidence snippets", styles["value_bold"]),
                Spacer(1, 3),
                _standard_table(
                    table_rows,
                    [content_width * 0.22, content_width * 0.20, content_width * 0.58],
                    long=True,
                ),
            ]
        )

    disclaimer = _nlp_text(details.get("disclaimer"))
    if disclaimer:
        story.extend(
            [
                Spacer(1, 6),
                Paragraph(_safe(_short_text(disclaimer, 420)), styles["disclaimer"]),
            ]
        )
    story.extend(
        [
            Paragraph(
                "Decision-support audit context only. Clinician review remains required.",
                styles["body"],
            ),
            Spacer(1, 6),
        ]
    )


def _add_audit_trail(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    assessment: Assessment,
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
    audit_logs: list[AuditLog],
    content_width: float,
    generated_at: datetime,
) -> None:
    story.append(Paragraph("Audit Metadata / Audit Trail", styles["section"]))
    story.append(
        _key_value_table(
            styles,
            content_width,
            [
                ("Assessment ID", assessment.id),
                ("Request ID", prediction.id if prediction is not None else "Not captured"),
                ("Model Version", prediction.model_version if prediction is not None else "Not captured"),
                ("Generated time", generated_at),
                ("Review Status", _review_status(clinician_review)),
            ],
        )
    )
    story.append(Spacer(1, 6))
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
        details = _json_or_default(audit_log.details_json, None)
        if audit_log.action == "nlp_extraction_reviewed":
            details = {"status": "Reviewed before prediction"}
        events.append(
            (
                audit_log.created_at,
                _readable_value(audit_log.action),
                audit_log.actor_id,
                details,
            )
        )

    total_events = len(events)
    if total_events > 4:
        events = [
            *events[:2],
            (
                generated_at,
                "Audit trail condensed",
                "System",
                {"status": f"Showing first 2 and latest event of {total_events} events."},
            ),
            events[-1],
        ]

    table_rows = [
        [
            Paragraph("Timestamp", styles["table_header"]),
            Paragraph("Action", styles["table_header"]),
            Paragraph("Actor", styles["table_header"]),
            Paragraph("Details", styles["table_header"]),
        ]
    ]
    for timestamp, action, actor, details in events:
        table_rows.append(
            [
                Paragraph(_safe(_display(timestamp)), styles["value"]),
                Paragraph(_safe(_display(action)), styles["value"]),
                Paragraph(_safe(_display(actor)), styles["value"]),
                Paragraph(_safe(_short_text(_details_text(details), 150)), styles["value"]),
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


def _report_final_esi(
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
) -> int | None:
    if clinician_review is not None and clinician_review.final_esi is not None:
        return clinician_review.final_esi
    return prediction.final_esi if prediction is not None else None


def _patient_summary(assessment: Assessment) -> str:
    patient = getattr(assessment, "patient", None)
    name = getattr(patient, "name", None)
    display_name = name.strip() if isinstance(name, str) and name.strip() else "Not captured"
    age = _display(getattr(patient, "age", None))
    sex = _display(getattr(patient, "sex", None))
    return f"{display_name} ({age}, {sex})"


def _patient_mrn(assessment: Assessment) -> str:
    mrn = getattr(getattr(assessment, "patient", None), "mrn", None)
    return mrn.strip() if isinstance(mrn, str) and mrn.strip() else "Not captured"


def _vital_cells(assessment: Assessment) -> list[tuple[str, str, str]]:
    return [
        ("HR", _unit(assessment.heart_rate, "bpm"), _vital_status("heart_rate", assessment.heart_rate)),
        ("RR", _unit(assessment.respiratory_rate, "/min"), _vital_status("respiratory_rate", assessment.respiratory_rate)),
        ("BP", _blood_pressure(assessment), _blood_pressure_status(assessment)),
        ("Temp", _unit(assessment.temperature_c, "C"), _vital_status("temperature_c", assessment.temperature_c)),
        ("SpO2", _unit(assessment.oxygen_saturation, "%"), _vital_status("oxygen_saturation", assessment.oxygen_saturation)),
        ("Pain", _unit(assessment.pain_score, "/10"), _vital_status("pain_score", assessment.pain_score)),
    ]


def _vital_style(
    styles: dict[str, ParagraphStyle],
    status: str,
) -> ParagraphStyle:
    if status == "Critical display range":
        return styles["vital_critical"]
    if status == "Outside display range":
        return styles["vital_abnormal"]
    return styles["vital_value"]


def _threshold_profile_text(prediction: Prediction | None) -> str:
    if prediction is None:
        return "Not captured"
    return f"Backend safety gate / {_readable_value(prediction.final_source)}"


def _risk_flags_text(prediction: Prediction | None) -> str:
    triggered = _triggered_safety_rules(prediction)
    if not triggered:
        return "None selected"
    return "; ".join(_safety_rule_label(rule.get("rule_id")) for rule in triggered)


def _safety_gate_status(prediction: Prediction | None) -> str:
    if prediction is None:
        return "Not documented"
    triggered = [
        rule
        for rule in _json_or_default(prediction.safety_rules_json, [])
        if isinstance(rule, dict) and rule.get("triggered")
    ]
    if triggered and prediction.predicted_esi is not None and prediction.final_esi is not None:
        if prediction.final_esi < prediction.predicted_esi:
            return "Escalated by safety rules"
    return "Review triggered" if triggered else "No escalation"


def _triggered_safety_rules(prediction: Prediction | None) -> list[dict[str, Any]]:
    if prediction is None:
        return []
    return [
        rule
        for rule in _json_or_default(prediction.safety_rules_json, [])
        if isinstance(rule, dict) and rule.get("triggered")
    ]


def _rules_fired_text(prediction: Prediction | None) -> str:
    triggered = _triggered_safety_rules(prediction)
    if not triggered:
        return "None"
    return "; ".join(
        _safety_rule_label(rule.get("rule_id")) for rule in triggered
    )


def _top_probability_label(probabilities: dict[str, Any]) -> str | None:
    parsed: list[tuple[str, float]] = []
    for label, value in probabilities.items():
        try:
            parsed.append((label, float(value)))
        except (TypeError, ValueError):
            continue
    if not parsed:
        return None
    return max(parsed, key=lambda item: item[1])[0]


def _safety_gate_result_text(prediction: Prediction | None) -> str:
    if prediction is None:
        return "Not documented"
    if _triggered_safety_rules(prediction):
        if prediction.predicted_esi is not None and prediction.final_esi is not None and prediction.final_esi < prediction.predicted_esi:
            return f"Escalated from model prediction ESI {prediction.predicted_esi} to final ESI {prediction.final_esi} by safety rules."
        return "Safety-rule review triggered; final ESI unchanged."
    return "No safety-rule escalation triggered."


def _review_status(clinician_review: ClinicianReview | None) -> str:
    if clinician_review is None:
        return "Pending clinician review"
    return _readable_value(clinician_review.action)


def _final_decision_summary(
    prediction: Prediction | None,
    clinician_review: ClinicianReview | None,
) -> str:
    if prediction is None:
        return (
            "No stored model prediction is available. Clinician review is required "
            "before ESI care routing decisions are used."
        )
    if clinician_review is not None and clinician_review.final_esi != prediction.final_esi:
        return (
            f"Clinician review changed final routing from ESI {prediction.final_esi} "
            f"to ESI {clinician_review.final_esi}."
        )
    if (
        prediction.predicted_esi is not None
        and prediction.final_esi is not None
        and prediction.final_esi < prediction.predicted_esi
    ):
        return (
            f"Escalated from model prediction ESI {prediction.predicted_esi} "
            f"to final ESI {prediction.final_esi} by safety rules."
        )
    if _triggered_safety_rules(prediction):
        return "Safety-rule review triggered; final ESI unchanged."
    return "Model decision confirmed; no safety-rule escalation triggered."


def _probability_bar(
    styles: dict[str, ParagraphStyle],
    value: Any,
    width: float = 2.55 * inch,
    accent: bool = True,
) -> Table:
    try:
        probability = max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        probability = 0.0
    filled = max(0.01, min(0.99, probability))
    table = Table(
        [["", ""]],
        colWidths=[width * filled, width * (1 - filled)],
        rowHeights=[0.12 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), TEAL if accent and probability else colors.HexColor("#94A3B8")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#E2E8F0")),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def _status_box(
    styles: dict[str, ParagraphStyle],
    content_width: float,
    text: str,
    background: colors.Color,
    border: colors.Color,
) -> Table:
    table = Table([[Paragraph(_safe(text), styles["value_bold"])]], colWidths=[content_width])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, border),
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def _vital_status(vital_name: str, value: Any) -> str:
    if value is None:
        return "Not documented"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "Not documented"
    if vital_name == "temperature_c":
        if numeric < 35 or numeric >= 40:
            return "Critical display range"
        if numeric < 36 or numeric >= 38:
            return "Outside display range"
    if vital_name == "heart_rate":
        if numeric < 40 or numeric >= 130:
            return "Critical display range"
        if numeric < 60 or numeric >= 110:
            return "Outside display range"
    if vital_name == "respiratory_rate":
        if numeric < 8 or numeric >= 30:
            return "Critical display range"
        if numeric < 12 or numeric >= 22:
            return "Outside display range"
    if vital_name == "oxygen_saturation":
        if numeric < 92:
            return "Critical display range"
        if numeric < 95:
            return "Outside display range"
    if vital_name == "pain_score":
        if numeric >= 8:
            return "Outside display range"
    return "Documented"


def _blood_pressure_status(assessment: Assessment) -> str:
    if assessment.systolic_bp is None and assessment.diastolic_bp is None:
        return "Not documented"
    if assessment.systolic_bp is not None:
        if assessment.systolic_bp < 90 or assessment.systolic_bp >= 180:
            return "Critical display range"
        if assessment.systolic_bp < 100 or assessment.systolic_bp >= 140:
            return "Outside display range"
    if assessment.diastolic_bp is not None and assessment.diastolic_bp >= 110:
        return "Critical display range"
    if assessment.diastolic_bp is not None and assessment.diastolic_bp >= 90:
        return "Outside display range"
    return "Documented"


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
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E2EA")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D7E2EA")),
                ("BACKGROUND", (0, 0), (0, -1), SLATE_SOFT),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
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
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFCFD")]),
            ]
        )
    else:
        commands.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#FAFCFD")]))
    return TableStyle(commands)


def _footer(canvas: Any, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    footer_y = 0.44 * inch
    page_width = document.pagesize[0]
    canvas.setStrokeColor(SLATE_LINE)
    canvas.setLineWidth(0.4)
    canvas.line(document.leftMargin, footer_y + 0.18 * inch, page_width - document.rightMargin, footer_y + 0.18 * inch)
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(SLATE_MUTED)
    canvas.drawString(
        document.leftMargin,
        footer_y,
        "This report supports structured triage review and does not replace clinician judgment or emergency protocols.",
    )
    canvas.drawRightString(page_width - document.rightMargin, footer_y, f"Page {document.page}")
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


def _short_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 1].rstrip()}..."


def _pdf_explanation_text(value: str) -> str:
    return value.replace(
        "is not a diagnosis or a substitute for clinician judgment",
        "does not replace clinician judgment",
    )


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


def _esi_badge(value: int | None) -> str:
    return "Not captured" if value is None else f"ESI {value}"


def _percent(value: Any) -> str:
    if value is None:
        return "Not documented"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "Not documented"


def _latency_ms(prediction: Prediction | None) -> str:
    latency = getattr(prediction, "latency_ms", None)
    if latency is None:
        return "Not captured"
    try:
        return f"{int(latency)} ms"
    except (TypeError, ValueError):
        return "Not captured"


def _unit(value: Any, unit: str) -> str:
    if value is None or value == "":
        return "Not documented"
    return f"{value} {unit}"


def _blood_pressure(assessment: Assessment) -> str:
    if assessment.systolic_bp is None and assessment.diastolic_bp is None:
        return "Not documented"
    return f"{_display(assessment.systolic_bp)}/{_display(assessment.diastolic_bp)} mmHg"
