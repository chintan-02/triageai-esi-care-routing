import type jsPDFType from 'jspdf';
// Legacy browser-side PDF helper retained for mock-mode experiments only.
// Official clinical report generation uses the backend endpoint:
// GET /assessments/{assessment_id}/report/pdf.
import type { AssessmentRecord, AuditEvent, ClinicianReview, EsiLevel } from '@/types/clinical';
import { formatDateTime, formatPercent } from '@/lib/formatters';
import { vitalFlag, vitalStatusLabel, type VitalKey } from '@/lib/vitals';

const ACUITY_RGB: Record<number, [number, number, number]> = {
  1: [127, 29, 29],
  2: [220, 38, 38],
  3: [217, 119, 6],
  4: [37, 99, 235],
  5: [22, 163, 74]
};

const NAVY: [number, number, number] = [11, 27, 51];
const TEAL: [number, number, number] = [13, 148, 136];
const SLATE_LINE: [number, number, number] = [220, 228, 238];
const SLATE_TEXT: [number, number, number] = [51, 65, 85];
const SLATE_MUTED: [number, number, number] = [100, 116, 139];
const SLATE_SOFT: [number, number, number] = [248, 250, 252];
const PAGE_FOOTER_SPACE = 58;

type SafetyGateSummary = {
  triggered: boolean;
  changedFinalEsi: boolean;
  highRisk: boolean;
  result: string;
  rulesFired: string;
  explanation: string;
  recommendation: string;
};

type NormalizedReviewState = {
  status: ClinicianReview['status'];
  modelPredictedEsi: EsiLevel;
  safetyFinalEsi: EsiLevel;
  clinicianFinalEsi?: EsiLevel;
  displayedFinalEsi: EsiLevel;
  reviewer: string;
  reviewedAt?: string;
  note: string;
  headline: string;
  isOverride: boolean;
};

function lastAutoTableY(doc: jsPDFType) {
  return (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY;
}

function ensureSpace(doc: jsPDFType, y: number, needed: number, margin: number) {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (y + needed > pageHeight - PAGE_FOOTER_SPACE) {
    doc.addPage();
    return margin;
  }
  return y;
}

function sectionTitle(doc: jsPDFType, title: string, x: number, y: number) {
  doc.setTextColor(...NAVY);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(12.5);
  doc.text(title, x, y);
}

function drawWrappedText(doc: jsPDFType, text: string, x: number, y: number, maxWidth: number, lineHeight = 11) {
  const lines = doc.splitTextToSize(text, maxWidth) as string[];
  doc.text(lines, x, y);
  return y + Math.max(1, lines.length) * lineHeight;
}

function cleanList(values: string[], fallback = 'None selected') {
  const cleaned = values.filter((value) => value !== 'None reported');
  if (cleaned.length) return cleaned.join(', ');
  if (values.includes('None reported')) return 'None reported';
  return fallback;
}

function pendingReviewNote(note: string) {
  return note.trim().toLowerCase().startsWith('awaiting clinician review');
}

function entered(value: number | undefined) {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatBp(vitals: AssessmentRecord['intake']['vitals']) {
  if (!entered(vitals.systolicBp) || !entered(vitals.diastolicBp)) return 'Not entered';
  return `${vitals.systolicBp}/${vitals.diastolicBp}`;
}

function visibleSafetySignals(record: AssessmentRecord) {
  const { intake } = record;
  const riskFlags = intake.riskFlags.map((flag) => flag.toLowerCase());
  const riskText = `${intake.chiefComplaint} ${intake.symptomText} ${riskFlags.join(' ')}`.toLowerCase();
  const hasAbnormalVitalsFlag = riskFlags.includes('abnormal vital signs');

  const vitalSignals: Array<{ key: VitalKey; label: string; value: number | string }> = [
    { key: 'heartRate', label: 'HR', value: `${intake.vitals.heartRate} bpm` },
    { key: 'respiratoryRate', label: 'RR', value: `${intake.vitals.respiratoryRate}/min` },
    { key: 'systolicBp', label: 'BP', value: formatBp(intake.vitals) },
    { key: 'temperatureC', label: 'Temp', value: `${intake.vitals.temperatureC.toFixed(1)}°C` },
    { key: 'spo2', label: 'SpO2', value: `${intake.vitals.spo2}%` },
    { key: 'painScore', label: 'Pain', value: `${intake.vitals.painScore}/10` }
  ];

  const abnormalVitals = vitalSignals.filter((signal) => vitalFlag(signal.key, Number(intake.vitals[signal.key]), intake.patient.age) !== 'normal');
  const criticalVitals = vitalSignals.filter((signal) => vitalFlag(signal.key, Number(intake.vitals[signal.key]), intake.patient.age) === 'critical');
  const signals = criticalVitals.map((signal) => `Critical ${signal.label} (${signal.value})`);

  if (hasAbnormalVitalsFlag && abnormalVitals.length) signals.push('Abnormal vital signs risk flag');
  if (riskText.includes('altered mental status')) signals.push('Altered mental status');
  if ((riskText.includes('shortness of breath') || riskText.includes('breath')) && abnormalVitals.length) signals.push('Shortness of breath with abnormal vitals');
  if (riskText.includes('chest pain') && abnormalVitals.length) signals.push('Chest pain with abnormal vitals');
  if ((riskText.includes('severe pain') || intake.vitals.painScore >= 8) && abnormalVitals.length) signals.push('Severe pain with abnormal vitals');
  if (riskText.includes('recent trauma') && abnormalVitals.length) signals.push('Recent trauma with abnormal vitals');

  return Array.from(new Set(signals));
}

function safetyGateSummary(record: AssessmentRecord): SafetyGateSummary {
  const { prediction } = record;
  const visibleSignals = visibleSafetySignals(record);
  const ruleLabels = prediction.ruleHits.map((rule) => rule.label);
  const triggered = ruleLabels.length > 0 || visibleSignals.length > 0;
  const changedFinalEsi = prediction.finalEsi < prediction.predictedEsi;
  const highRisk = changedFinalEsi || prediction.finalEsi <= 2 || prediction.ruleHits.some((rule) => rule.severity === 'critical' || rule.severity === 'high') || visibleSignals.length > 0;
  const result = changedFinalEsi
    ? `Escalated from model prediction ESI ${prediction.predictedEsi} to final ESI ${prediction.finalEsi} by safety rules.`
    : triggered
      ? 'Safety-rule review triggered; final ESI unchanged.'
      : 'No safety-rule escalation triggered.';
  const rulesFired = ruleLabels.length
    ? ruleLabels.join('; ')
    : triggered
      ? visibleSignals.join('; ')
      : 'None';
  const explanation = triggered && /No safety-rule escalation triggered/i.test(prediction.explanation)
    ? visibleSignals.length
      ? `Visible safety signals support clinician review visibility: ${visibleSignals.join('; ')}.`
      : `Safety rules require clinician review visibility: ${ruleLabels.join('; ')}.`
    : prediction.explanation;
  return {
    triggered,
    changedFinalEsi,
    highRisk,
    result,
    rulesFired,
    explanation,
    recommendation: highRisk
      ? 'Immediate clinician assessment recommended. Confirm final acuity before care routing.'
      : 'Clinician review required before final care routing.'
  };
}

function normalizeReviewState(record: AssessmentRecord, safety: SafetyGateSummary): NormalizedReviewState {
  const { prediction, review } = record;
  const safetyFinalEsi = prediction.finalEsi;
  const realOverride = review.status === 'overridden' && review.finalDecision !== safetyFinalEsi;
  const status = realOverride ? 'overridden' : review.status === 'pending' ? 'pending' : 'accepted';
  const clinicianFinalEsi = status === 'pending' ? undefined : status === 'accepted' ? safetyFinalEsi : review.finalDecision;
  const displayedFinalEsi = status === 'overridden' ? review.finalDecision : safetyFinalEsi;
  const reviewer = status === 'pending' && (!review.reviewer || review.reviewer === 'Unassigned') ? 'Unassigned' : `${review.reviewer} (${review.role})`;
  const overrideFallback = `Doctor override changed final routing from ESI ${safetyFinalEsi} to ESI ${review.finalDecision}.`;
  const note = (() => {
    if (status === 'pending') return 'Awaiting clinician review.';
    if (status === 'accepted') return 'Current final routing decision accepted.';
    if (!review.note || pendingReviewNote(review.note) || /accepted|overridden based on clinician judgment/i.test(review.note)) return overrideFallback;
    return review.note;
  })();
  const headline = (() => {
    if (status === 'overridden') return overrideFallback;
    if (prediction.finalEsi < prediction.predictedEsi) {
      return `Escalated from model prediction ESI ${prediction.predictedEsi} to final ESI ${prediction.finalEsi} by safety rules.`;
    }
    if (safety.triggered) return 'Safety-rule review triggered; final ESI unchanged.';
    return 'Model decision confirmed; no safety-rule escalation triggered.';
  })();

  return {
    status,
    modelPredictedEsi: prediction.predictedEsi,
    safetyFinalEsi,
    clinicianFinalEsi,
    displayedFinalEsi,
    reviewer,
    reviewedAt: review.reviewedAt,
    note,
    headline,
    isOverride: status === 'overridden'
  };
}

function reviewRows(normalized: NormalizedReviewState) {
  const rows = [
    ['Status', normalized.status],
    ['Reviewer', normalized.reviewer],
    ['Final Clinician Decision', normalized.status === 'pending' ? 'Not yet reviewed' : `ESI ${normalized.displayedFinalEsi}`],
    ['Reviewed time', normalized.reviewedAt ? formatDateTime(normalized.reviewedAt) : 'Not yet reviewed'],
    [normalized.isOverride ? 'Override reason' : 'Note', normalized.note]
  ];
  if (normalized.isOverride && normalized.clinicianFinalEsi && normalized.clinicianFinalEsi !== normalized.safetyFinalEsi) {
    rows.splice(3, 0, ['Original Final ESI', `ESI ${normalized.safetyFinalEsi}`], ['Overridden Final ESI', `ESI ${normalized.clinicianFinalEsi}`]);
  }
  return rows;
}

function auditEventsForPdf(record: AssessmentRecord, normalized: NormalizedReviewState): AuditEvent[] {
  const nonReviewEvents = record.auditTrail.filter((event) => !/^Decision (accepted|overridden)$/i.test(event.action));
  if (normalized.status === 'pending') return nonReviewEvents;
  return [
    ...nonReviewEvents,
    {
      id: `${record.id}-pdf-review`,
      timestamp: normalized.reviewedAt ?? new Date().toISOString(),
      actor: normalized.reviewer,
      action: normalized.status === 'overridden' ? 'Decision overridden' : 'Decision accepted',
      details: normalized.note,
      severity: normalized.status === 'overridden' ? 'warning' : 'info'
    }
  ];
}

function drawFooter(doc: jsPDFType, pageWidth: number, margin: number) {
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i += 1) {
    doc.setPage(i);
    const footerY = doc.internal.pageSize.getHeight() - 42;
    doc.setDrawColor(...SLATE_LINE);
    doc.line(margin, footerY - 15, pageWidth - margin, footerY - 15);
    doc.setTextColor(100, 116, 139);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.text(
      'This report supports structured triage review and does not replace clinician judgment, diagnosis, or emergency protocols.',
      margin,
      footerY,
      { maxWidth: pageWidth - margin * 2 - 70 }
    );
    doc.text(`Page ${i} of ${pageCount}`, pageWidth - margin, footerY, { align: 'right' });
  }
}

export async function generateAssessmentPdf(record: AssessmentRecord) {
  const [{ default: jsPDF }, { default: autoTable }] = await Promise.all([import('jspdf'), import('jspdf-autotable')]);

  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 44;
  const { intake, prediction } = record;
  const generatedAt = new Date().toISOString();
  const safety = safetyGateSummary(record);
  const normalized = normalizeReviewState(record, safety);
  const reportFinalEsi = normalized.displayedFinalEsi;
  const auditEvents = auditEventsForPdf(record, normalized);
  const acuityColor = ACUITY_RGB[reportFinalEsi] ?? NAVY;

  // ---- Header band -------------------------------------------------------
  doc.setFillColor(...NAVY);
  doc.roundedRect(margin, 34, pageWidth - margin * 2, 88, 12, 12, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.text('Clinical ESI Routing Summary', margin + 20, 62);
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.text('Human-in-the-loop ESI care routing report — not a diagnostic tool', margin + 20, 80);
  doc.text(`Assessment ID: ${record.id}`, margin + 20, 99);
  doc.text(`Generated time: ${formatDateTime(generatedAt)}`, margin + 20, 113);

  // ESI chip, top-right of the header band
  const chipW = 96;
  const chipX = pageWidth - margin - 20 - chipW;
  doc.setFillColor(...acuityColor);
  doc.roundedRect(chipX, 52, chipW, 30, 8, 8, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(13);
  doc.setTextColor(255, 255, 255);
  doc.text(`FINAL ESI ${reportFinalEsi}`, chipX + chipW / 2, 71, { align: 'center' });
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.text(`Assessment time: ${formatDateTime(prediction.createdAt)}`, pageWidth - margin - 20, 101, { align: 'right' });
  if (normalized.reviewedAt) {
    doc.text(`Reviewed time: ${formatDateTime(normalized.reviewedAt)}`, pageWidth - margin - 20, 115, { align: 'right' });
  }

  let y = 148;

  // ---- Final routing decision --------------------------------------------
  sectionTitle(doc, 'Final Routing Decision', margin, y);
  const cardX = margin;
  const cardY = y + 10;
  const cardW = pageWidth - margin * 2;
  const cardH = 120;
  doc.setFillColor(255, 255, 255);
  doc.setDrawColor(...SLATE_LINE);
  doc.roundedRect(cardX, cardY, cardW, cardH, 10, 10, 'FD');
  doc.setFillColor(...acuityColor);
  doc.roundedRect(cardX + 14, cardY + 18, 96, 48, 9, 9, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(17);
  doc.text(`ESI ${reportFinalEsi}`, cardX + 62, cardY + 48, { align: 'center' });
  doc.setFontSize(7.5);
  doc.text('FINAL ROUTING', cardX + 62, cardY + 30, { align: 'center' });

  const summaryX = cardX + 126;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(...NAVY);
  doc.text(normalized.headline, summaryX, cardY + 26, { maxWidth: cardW - 146 });
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(...SLATE_TEXT);
  drawWrappedText(doc, `Safety gate: ${safety.result}`, summaryX, cardY + 45, cardW - 146, 10);

  const metrics = [
    ['Model prediction', `ESI ${prediction.predictedEsi}`],
    ['Confidence', formatPercent(prediction.confidence)],
    ['Latency', prediction.latencyMs === null ? 'Not captured' : `${prediction.latencyMs} ms`],
    ['Safety gate', safety.triggered ? 'Review triggered' : 'No escalation'],
    ['Clinician review', normalized.status],
    ['Assessment time', formatDateTime(prediction.createdAt)]
  ];
  const metricTop = cardY + 70;
  const metricGap = 6;
  const metricW = (cardW - 28 - metricGap * 2) / 3;
  metrics.forEach(([label, value], index) => {
    const col = index % 3;
    const row = Math.floor(index / 3);
    const x = cardX + 14 + col * (metricW + metricGap);
    const yy = metricTop + row * 23;
    doc.setFillColor(...SLATE_SOFT);
    doc.roundedRect(x, yy, metricW, 18, 4, 4, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.7);
    doc.setTextColor(...SLATE_MUTED);
    doc.text(label.toUpperCase(), x + 6, yy + 7);
    doc.setFontSize(8.2);
    doc.setTextColor(...NAVY);
    doc.text(String(value), x + metricW - 6, yy + 12.5, { align: 'right', maxWidth: metricW - 54 });
  });
  y = cardY + cardH + 13;

  autoTable(doc, {
    startY: y,
    body: [
      ['Request ID', prediction.requestId],
      ['Model Version', prediction.modelVersion],
      ['Threshold Profile', prediction.thresholdProfile],
      ['Model Scope', 'Classifier predicts ESI 3/4/5; safety gate and clinician review handle ESI 1/2 escalation']
    ],
    theme: 'plain',
    styles: { fontSize: 8.4, cellPadding: 4.5, lineColor: SLATE_LINE, lineWidth: 0.4, overflow: 'linebreak', valign: 'top' },
    columnStyles: {
      0: { fontStyle: 'bold', textColor: SLATE_TEXT, fillColor: SLATE_SOFT, cellWidth: 112 },
      1: { textColor: [15, 23, 42], cellWidth: pageWidth - margin * 2 - 112 }
    },
    margin: { left: margin, right: margin }
  });
  y = lastAutoTableY(doc) + 14;

  // ---- Patient & intake summary ------------------------------------------
  y = ensureSpace(doc, y, 126, margin);
  sectionTitle(doc, 'Patient & Intake Summary', margin, y);
  autoTable(doc, {
    startY: y + 10,
    body: [
      ['Patient', `${intake.patient.name} (${intake.patient.age}, ${intake.patient.sex || 'Unknown'})`],
      ['MRN', intake.patient.mrn],
      ['Arrival Mode', intake.patient.arrivalMode],
      ['Chief Complaint', intake.chiefComplaint],
      ['Symptom Narrative', intake.symptomText],
      ['Duration', intake.duration],
      ['Selected risk flags', cleanList(intake.riskFlags)],
      ['Comorbidities', cleanList(intake.comorbidities)]
    ],
    theme: 'striped',
    styles: { fontSize: 9, cellPadding: 5, valign: 'top', overflow: 'linebreak' },
    columnStyles: { 0: { fontStyle: 'bold', cellWidth: 120 }, 1: { cellWidth: pageWidth - margin * 2 - 120 } },
    margin: { left: margin, right: margin }
  });
  y = lastAutoTableY(doc) + 16;

  // ---- Vitals (abnormal values highlighted) ------------------------------
  y = ensureSpace(doc, y, 90, margin);
  sectionTitle(doc, 'Vitals', margin, y);

  type VitalCell = { key: keyof typeof intake.vitals; text: string };
  const vitalCells: VitalCell[] = [
    { key: 'heartRate', text: `${intake.vitals.heartRate} bpm` },
    { key: 'respiratoryRate', text: `${intake.vitals.respiratoryRate}/min` },
    { key: 'systolicBp', text: formatBp(intake.vitals) },
    { key: 'temperatureC', text: `${intake.vitals.temperatureC.toFixed(1)}°C` },
    { key: 'spo2', text: `${intake.vitals.spo2}%` },
    { key: 'painScore', text: `${intake.vitals.painScore}/10` }
  ];
  autoTable(doc, {
    startY: y + 10,
    head: [['HR', 'RR', 'BP', 'Temp', 'SpO2', 'Pain']],
    body: [
      vitalCells.map((cell) => {
        const flag = vitalFlag(cell.key, intake.vitals[cell.key], intake.patient.age);
        const fill: [number, number, number] = flag === 'critical' ? [254, 226, 226] : flag === 'abnormal' ? [254, 243, 199] : [255, 255, 255];
        const textColor: [number, number, number] = flag === 'critical' ? [153, 27, 27] : flag === 'abnormal' ? [146, 64, 14] : [15, 23, 42];
        return { content: `${cell.text}\n${vitalStatusLabel(flag)}`, styles: { fillColor: fill, textColor, fontStyle: flag === 'normal' ? 'normal' : 'bold' } };
      })
    ],
    styles: { fontSize: 9, cellPadding: 6, halign: 'center' },
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255] },
    margin: { left: margin, right: margin }
  });
  y = lastAutoTableY(doc) + 8;
  doc.setFont('helvetica', 'italic');
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text('Highlighted values support review visibility; backend safety thresholds remain authoritative.', margin, y + 10);
  y += 26;

  // Page 2 is intentional: model transparency, safety routing, review, and audit metadata.
  doc.addPage();
  y = margin;
  const columnGap = 16;
  const columnWidth = (pageWidth - margin * 2 - columnGap) / 2;
  const rightColumnX = margin + columnWidth + columnGap;

  // ---- Model probabilities ------------------------------------------------
  sectionTitle(doc, 'Model Output Probabilities', margin, y);

  const probEntries = Object.entries(prediction.probabilities).sort(([a], [b]) => a.localeCompare(b));
  const topLabel = probEntries.reduce((max, [label, value]) => (value > (prediction.probabilities[max] ?? -1) ? label : max), probEntries[0]?.[0]);
  let barY = y + 16;
  const barLabelWidth = 42;
  const percentWidth = 40;
  const barWidth = columnWidth - barLabelWidth - percentWidth - 12;
  probEntries.forEach(([label, value]) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(51, 65, 85);
    doc.text(label, margin, barY + 8);
    doc.setFillColor(241, 245, 249);
    doc.roundedRect(margin + barLabelWidth, barY, barWidth, 10, 4, 4, 'F');
    const fillW = Math.max(6, barWidth * value);
    const barColor: [number, number, number] = label === topLabel ? TEAL : [148, 163, 184];
    doc.setFillColor(...barColor);
    doc.roundedRect(margin + barLabelWidth, barY, fillW, 10, 4, 4, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.2);
    doc.setTextColor(15, 23, 42);
    doc.text(formatPercent(value), margin + barLabelWidth + barWidth + 8, barY + 8);
    barY += 18;
  });
  doc.setFont('helvetica', 'italic');
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  const probabilityNoteY = drawWrappedText(doc, 'Raw model probabilities are shown for transparency and are not calibrated probabilities.', margin, barY + 4, columnWidth, 9);
  const leftColumnBottom = probabilityNoteY + 2;

  // ---- Safety rules & recommendation -------------------------------------
  sectionTitle(doc, 'Safety Rules & Recommendation', rightColumnX, y);
  autoTable(doc, {
    startY: y + 10,
    head: [['Signal', 'Value']],
    body: [
      ['Rules Fired', safety.rulesFired],
      ['Safety Gate Result', safety.result],
      ['Explanation', safety.explanation],
      ['Recommendation', safety.recommendation]
    ],
    styles: { fontSize: 8.2, cellPadding: 4, valign: 'top', overflow: 'linebreak' },
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255] },
    columnStyles: { 0: { fontStyle: 'bold', cellWidth: 76 }, 1: { cellWidth: columnWidth - 76 } },
    margin: { left: rightColumnX, right: margin },
    tableWidth: columnWidth
  });
  const rightColumnBottom = lastAutoTableY(doc);
  y = Math.max(leftColumnBottom, rightColumnBottom) + 18;

  // ---- Clinician review ---------------------------------------------------
  y = ensureSpace(doc, y, 95, margin);
  sectionTitle(doc, 'Clinician Review', margin, y);
  autoTable(doc, {
    startY: y + 10,
    body: reviewRows(normalized),
    theme: 'striped',
    styles: { fontSize: 8.6, cellPadding: 4, valign: 'top', overflow: 'linebreak' },
    columnStyles: { 0: { fontStyle: 'bold', cellWidth: 120 }, 1: { cellWidth: pageWidth - margin * 2 - 120 } },
    margin: { left: margin, right: margin }
  });
  y = lastAutoTableY(doc) + 14;

  // ---- Compact audit metadata --------------------------------------------
  y = ensureSpace(doc, y, 100, margin);
  sectionTitle(doc, 'Audit Metadata', margin, y);
  autoTable(doc, {
    startY: y + 10,
    body: [
      ['Assessment ID', record.id],
      ['Request ID', prediction.requestId],
      ['Model Version', prediction.modelVersion],
      ['Generated time', formatDateTime(generatedAt)],
      ['Review Status', normalized.status],
      ['Audit Trail Events', auditEvents.map((event) => `${formatDateTime(event.timestamp)} - ${event.action}: ${event.details}`).join('\n') || 'No audit events recorded']
    ],
    theme: 'plain',
    styles: { fontSize: 8.2, cellPadding: 4, lineColor: SLATE_LINE, lineWidth: 0.4, overflow: 'linebreak', valign: 'top' },
    columnStyles: {
      0: { fontStyle: 'bold', fillColor: [248, 250, 252], textColor: SLATE_TEXT, cellWidth: 120 },
      1: { cellWidth: pageWidth - margin * 2 - 120 }
    },
    margin: { left: margin, right: margin }
  });

  // ---- Footer: disclaimer + page numbers on every page -------------------
  drawFooter(doc, pageWidth, margin);

  doc.save(`${record.id}_triageai_report.pdf`);
}
