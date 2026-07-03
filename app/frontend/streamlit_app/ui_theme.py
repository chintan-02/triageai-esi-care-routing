"""Shared Streamlit theme and page helpers for the TriageAI frontend."""

from __future__ import annotations

from html import escape

import streamlit as st


DEFAULT_DISCLAIMER = (
    "This project supports clinical decision-support workflow testing only and "
    "does not replace clinician judgment."
)


def apply_theme() -> None:
    """Apply the shared healthcare workflow visual system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --ta-bg: #eef6fb;
            --ta-panel: #ffffff;
            --ta-panel-soft: #f8fbff;
            --ta-text: #0f172a;
            --ta-muted: #52677a;
            --ta-border: #d9e8f2;
            --ta-border-strong: #bae6fd;
            --ta-primary: #0284c7;
            --ta-primary-dark: #0369a1;
            --ta-primary-soft: #e0f2fe;
            --ta-success: #047857;
            --ta-warning: #92400e;
            --ta-danger: #b91c1c;
            --ta-shadow: 0 14px 34px rgba(15, 80, 120, 0.08);
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--ta-text);
        }

        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        .stDeployButton {
            visibility: hidden;
            height: 0;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 8%, rgba(14, 165, 233, 0.10), transparent 24%),
                radial-gradient(circle at 82% 0%, rgba(16, 185, 129, 0.08), transparent 23%),
                var(--ta-bg);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8fbff 0%, #edf5fb 100%);
            border-right: 1px solid var(--ta-border);
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #334155;
        }

        section[data-testid="stSidebar"] .stAlert {
            border-radius: 12px;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 1.6rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--ta-text);
            letter-spacing: 0;
        }

        .ta-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.94);
            border: 1px solid var(--ta-border);
            border-top: 4px solid var(--ta-primary);
            border-radius: 18px;
            padding: 15px 18px;
            box-shadow: var(--ta-shadow);
            margin-bottom: 18px;
        }

        .ta-brand {
            display: flex;
            align-items: center;
            gap: 13px;
        }

        .ta-logo {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--ta-primary-dark), #0ea5e9);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 21px;
            box-shadow: 0 10px 22px rgba(14, 165, 233, 0.25);
            flex: 0 0 auto;
        }

        .ta-brand-title {
            font-size: 20px;
            font-weight: 800;
            color: #0f2742;
            margin: 0;
            line-height: 1.1;
        }

        .ta-brand-subtitle {
            font-size: 12px;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 4px;
        }

        .ta-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 13px;
            border-radius: 999px;
            background: #e6fbf3;
            color: var(--ta-success);
            font-size: 13px;
            font-weight: 800;
            border: 1px solid #b8ecd8;
            white-space: nowrap;
        }

        .ta-hero {
            background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(245, 252, 255, 0.96));
            border: 1px solid #d5e7f2;
            border-radius: 24px;
            padding: 34px 38px;
            box-shadow: 0 20px 50px rgba(15, 80, 120, 0.11);
            margin-bottom: 18px;
            position: relative;
            overflow: hidden;
        }

        .ta-hero:after {
            content: "";
            position: absolute;
            right: -82px;
            top: -92px;
            width: 210px;
            height: 210px;
            border-radius: 999px;
            background: rgba(14, 165, 233, 0.11);
        }

        .ta-eyebrow,
        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--ta-primary-dark);
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .ta-eyebrow {
            padding: 7px 12px;
            background: var(--ta-primary-soft);
            border: 1px solid var(--ta-border-strong);
            border-radius: 999px;
            margin-bottom: 16px;
        }

        .ta-hero h1 {
            font-size: 46px;
            line-height: 1.04;
            margin: 0 0 12px 0;
            color: var(--ta-text);
            font-weight: 850;
        }

        .ta-hero h1 span {
            color: var(--ta-primary);
        }

        .ta-hero p {
            font-size: 17px;
            line-height: 1.62;
            color: #475569;
            max-width: 820px;
            margin: 0;
        }

        .ta-page-header,
        .clinical-header {
            background: rgba(255,255,255,0.94);
            border: 1px solid var(--ta-border);
            border-left: 5px solid var(--ta-primary);
            border-radius: 18px;
            padding: 20px 22px;
            box-shadow: var(--ta-shadow);
            margin: 0 0 18px 0;
        }

        .ta-page-header h1,
        .clinical-header h1 {
            margin: 4px 0 4px 0;
            color: var(--ta-text);
            font-size: 32px;
            line-height: 1.18;
            font-weight: 850;
        }

        .ta-page-header p,
        .clinical-header div:last-child {
            color: var(--ta-muted);
            font-size: 15px;
            line-height: 1.55;
            margin: 0;
        }

        .ta-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
        }

        .ta-badge,
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 8px 13px;
            font-size: 13px;
            font-weight: 800;
            border: 1px solid var(--ta-border-strong);
            background: #f0f9ff;
            color: #075985;
            margin: 0 6px 6px 0;
        }

        .badge-ok {
            background: #ecfdf5;
            border-color: #a7f3d0;
            color: var(--ta-success);
        }

        .badge-warn {
            background: #fff7ed;
            border-color: #fed7aa;
            color: #b45309;
        }

        .ta-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin: 16px 0;
        }

        .ta-card,
        .clinical-card,
        .hero-card {
            background: rgba(255,255,255,0.95);
            border: 1px solid var(--ta-border);
            border-radius: 18px;
            padding: 20px;
            box-shadow: var(--ta-shadow);
            margin-bottom: 16px;
        }

        .ta-card h3 {
            color: #0f2742;
            font-size: 18px;
            margin: 0 0 8px 0;
            font-weight: 800;
        }

        .ta-card p {
            color: #58708a;
            font-size: 14px;
            line-height: 1.55;
            margin: 0;
        }

        .ta-auth-shell {
            max-width: 760px;
            margin: 0 auto;
        }

        .ta-auth-card {
            background: rgba(255,255,255,0.96);
            border: 1px solid var(--ta-border);
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 22px 54px rgba(15, 80, 120, 0.13);
            text-align: center;
            margin-bottom: 18px;
        }

        .ta-auth-card .ta-logo {
            margin: 0 auto 14px auto;
        }

        .ta-auth-card h1 {
            font-size: 34px;
            line-height: 1.15;
            margin: 0 0 8px 0;
            font-weight: 850;
        }

        .ta-auth-card p {
            color: var(--ta-muted);
            margin: 0;
            line-height: 1.55;
            font-weight: 600;
        }

        .ta-workflow {
            background: #ffffff;
            border: 1px solid var(--ta-border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--ta-shadow);
            margin: 16px 0;
        }

        .ta-section-label,
        .section-title {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--ta-primary-dark);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-weight: 900;
            margin: 16px 0 12px 0;
        }

        .ta-section-label:after,
        .section-title:after {
            content: "";
            height: 1px;
            background: #cfe3f0;
            flex: 1;
        }

        .ta-steps {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 9px;
        }

        .ta-step {
            background: var(--ta-panel-soft);
            border: 1px solid var(--ta-border);
            border-radius: 14px;
            padding: 12px 10px;
            text-align: center;
            min-height: 78px;
        }

        .ta-step-num {
            width: 26px;
            height: 26px;
            border-radius: 999px;
            margin: 0 auto 7px auto;
            background: linear-gradient(135deg, var(--ta-primary), #0ea5e9);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 900;
        }

        .ta-step-title {
            color: #0f2742;
            font-size: 12px;
            font-weight: 850;
            line-height: 1.25;
        }

        .ta-disclaimer,
        .disclaimer {
            background: #fff7dc;
            border: 1px solid #f6d365;
            color: #854d0e;
            border-radius: 16px;
            padding: 15px 16px;
            font-weight: 700;
            line-height: 1.55;
            margin: 16px 0;
        }

        .ta-empty-state {
            background: rgba(255,255,255,0.95);
            border: 1px solid var(--ta-border);
            border-radius: 20px;
            padding: 28px;
            box-shadow: var(--ta-shadow);
            text-align: center;
            margin: 20px 0;
        }

        .ta-empty-icon {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: var(--ta-primary-soft);
            border: 1px solid var(--ta-border-strong);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--ta-primary-dark);
            font-size: 22px;
            font-weight: 900;
            margin: 0 auto 12px auto;
        }

        .ta-empty-state h3 {
            margin: 0 0 8px 0;
            color: var(--ta-text);
            font-size: 22px;
        }

        .ta-empty-state p {
            color: var(--ta-muted);
            margin: 0 auto;
            max-width: 560px;
            line-height: 1.6;
        }

        .ta-empty-action {
            display: inline-flex;
            margin-top: 16px;
            border-radius: 999px;
            border: 1px solid var(--ta-border-strong);
            color: var(--ta-primary-dark);
            background: #f0f9ff;
            padding: 8px 13px;
            font-weight: 800;
            font-size: 13px;
        }

        .ta-status-grid,
        .metric-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 16px 0;
        }

        .ta-status-card,
        .mini-metric,
        div[data-testid="stMetric"] {
            border: 1px solid var(--ta-border);
            border-radius: 14px;
            padding: 13px 14px;
            background: rgba(255,255,255,0.96);
            box-shadow: 0 8px 22px rgba(15, 80, 120, 0.055);
        }

        .ta-status-title,
        .metric-label {
            color: #6b8294;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        .ta-status-value,
        .metric-value {
            color: var(--ta-text);
            font-size: 24px;
            font-weight: 850;
            margin-top: 4px;
        }

        .ta-status-helper {
            color: var(--ta-muted);
            font-size: 13px;
            line-height: 1.45;
            margin-top: 4px;
        }

        .note-box,
        .warning-box,
        .safety-ok,
        .safety-warn {
            border-radius: 14px;
            padding: 14px 15px;
            line-height: 1.6;
            margin-bottom: 14px;
        }

        .note-box {
            border: 1px solid var(--ta-border);
            border-left: 4px solid var(--ta-primary);
            background: #fbfdff;
            white-space: pre-wrap;
            color: #1e3a52;
        }

        .safety-ok {
            border: 1px solid #a7f3d0;
            background: #ecfdf5;
            color: #065f46;
            font-weight: 700;
        }

        .safety-warn,
        .warning-box {
            border: 1px solid #fbbf24;
            background: #fffbeb;
            color: var(--ta-warning);
        }

        .final-esi {
            font-size: 3.4rem;
            font-weight: 900;
            color: var(--ta-primary-dark);
            line-height: 1;
            letter-spacing: 0;
        }

        .ta-dev {
            background: #0f172a;
            color: #e2e8f0;
            padding: 16px;
            border-radius: 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
        }

        div[data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--ta-border);
            border-radius: 18px;
            background: rgba(255,255,255,0.72);
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] > div,
        div[data-testid="stDateInput"] input {
            border-radius: 12px;
            border-color: #cfe3f0;
            background: #ffffff;
            color: var(--ta-text);
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: var(--ta-primary);
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.16);
        }

        div[data-testid="stSlider"] [role="slider"] {
            background: var(--ta-primary);
            border-color: var(--ta-primary);
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        div[data-testid="stDownloadButton"] > button,
        a[data-testid="stPageLink"] {
            border-radius: 14px;
            border: 1px solid var(--ta-border-strong);
            background: #ffffff;
            color: var(--ta-primary-dark);
            font-weight: 800;
            min-height: 42px;
            box-shadow: 0 8px 18px rgba(15, 80, 120, 0.06);
        }

        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        div[data-testid="stDownloadButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, var(--ta-primary), #0ea5e9);
            border-color: var(--ta-primary);
            color: #ffffff;
            box-shadow: 0 12px 24px rgba(14, 165, 233, 0.22);
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover,
        a[data-testid="stPageLink"]:hover {
            border-color: var(--ta-primary);
            color: var(--ta-primary-dark);
            transform: translateY(-1px);
        }

        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
            color: #ffffff;
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border: 1px solid var(--ta-border);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: var(--ta-shadow);
            background: #ffffff;
        }

        .stAlert {
            border-radius: 14px;
        }

        @media (max-width: 900px) {
            .ta-grid, .ta-steps, .ta-status-grid, .metric-row {
                grid-template-columns: 1fr;
            }
            .ta-hero {
                padding: 28px 24px;
            }
            .ta-hero h1 {
                font-size: 36px;
            }
            .ta-page-header h1,
            .clinical-header h1,
            .ta-auth-card h1 {
                font-size: 28px;
            }
            .ta-topbar {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
            }
            .final-esi {
                font-size: 2.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_header(status_label: str = "System Active") -> None:
    st.markdown(
        f"""
        <div class="ta-topbar">
            <div class="ta-brand">
                <div class="ta-logo">+</div>
                <div>
                    <div class="ta-brand-title">TriageAI / SympDirect</div>
                    <div class="ta-brand-subtitle">ESI Clinical Intake & Care Routing</div>
                </div>
            </div>
            <div class="ta-status-pill">{escape(status_label)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(
    title: str,
    subtitle: str | None = None,
    eyebrow: str | None = None,
) -> None:
    eyebrow_html = f'<div class="ta-eyebrow">{escape(eyebrow)}</div>' if eyebrow else ""
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="ta-page-header">
            {eyebrow_html}
            <h1>{escape(title)}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_badges(labels: list[str]) -> None:
    badges = "".join(
        [f'<span class="ta-badge">{escape(label)}</span>' for label in labels]
    )
    st.markdown(f'<div class="ta-badges">{badges}</div>', unsafe_allow_html=True)


def render_disclaimer(text: str | None = None) -> None:
    st.markdown(
        f'<div class="ta-disclaimer">{escape(text or DEFAULT_DISCLAIMER)}</div>',
        unsafe_allow_html=True,
    )


def render_empty_state(
    title: str,
    body: str,
    action_label: str | None = None,
) -> None:
    action_html = (
        f'<div class="ta-empty-action">{escape(action_label)}</div>'
        if action_label
        else ""
    )
    st.markdown(
        f"""
        <div class="ta-empty-state">
            <div class="ta-empty-icon">+</div>
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
            {action_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(title: str, value: str | int, helper: str | None = None) -> None:
    helper_html = (
        f'<div class="ta-status-helper">{escape(helper)}</div>' if helper else ""
    )
    st.markdown(
        f"""
        <div class="ta-status-card">
            <div class="ta-status-title">{escape(title)}</div>
            <div class="ta-status-value">{escape(str(value))}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_label(label: str) -> None:
    st.markdown(
        f'<div class="ta-section-label">{escape(label)}</div>',
        unsafe_allow_html=True,
    )


def render_action_grid(actions: list[tuple[str, str]]) -> None:
    cards = "".join(
        f"""
        <div class="ta-card">
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
        </div>
        """
        for title, body in actions
    )
    st.markdown(f'<div class="ta-grid">{cards}</div>', unsafe_allow_html=True)


def render_workflow_card() -> None:
    steps = [
        "New Assessment",
        "Model Prediction",
        "Safety Rules",
        "Clinician Review",
        "Audit Trail",
        "PDF Summary",
    ]
    step_html = ""
    for index, title in enumerate(steps, start=1):
        step_html += f"""
        <div class="ta-step">
            <div class="ta-step-num">{index}</div>
            <div class="ta-step-title">{escape(title)}</div>
        </div>
        """
    st.markdown(
        f"""
        <div class="ta-workflow">
            <div class="ta-section-label">Workflow Overview</div>
            <div class="ta-steps">{step_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_hero() -> None:
    st.markdown(
        """
        <div class="ta-hero">
            <div class="ta-eyebrow">Clinical Decision-Support Workflow Prototype</div>
            <h1>Welcome to <span>TriageAI</span></h1>
            <p>
                Structured emergency intake, LightGBM ESI 3/4/5 model output,
                safety-rule escalation, clinician review, audit visibility, and
                PDF decision-support summaries in one workflow.
            </p>
            <div class="ta-badges">
                <span class="ta-badge">Structured Intake</span>
                <span class="ta-badge">ESI 3/4/5 Model</span>
                <span class="ta-badge">Safety Escalation</span>
                <span class="ta-badge">Clinician Review</span>
                <span class="ta-badge">PDF Summary</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_cards() -> None:
    render_action_grid(
        [
            (
                "Start New Assessment",
                "Enter structured intake data and submit it to the ESI prediction workflow.",
            ),
            (
                "Review Dashboard",
                "Track reviewed, pending, override, and final ESI workflow status.",
            ),
            (
                "Generate Summary",
                "Create a PDF decision-support summary with model, rules, review, and audit context.",
            ),
        ]
    )
