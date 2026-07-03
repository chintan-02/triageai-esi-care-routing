"""Shared Streamlit theme and page helpers for the TriageAI frontend."""

from __future__ import annotations

from datetime import datetime
from html import escape

import streamlit as st


DEFAULT_DISCLAIMER = (
    "This project supports clinical decision-support workflow testing only and "
    "does not replace clinician judgment."
)


def _render_html(html: str) -> None:
    """Render trusted component HTML through Streamlit's HTML renderer."""
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def _tone_class(tone: str) -> str:
    return tone if tone in {"neutral", "blue", "green", "amber", "red"} else "neutral"


def format_datetime_for_display(value: object) -> str:
    if value is None or value == "":
        return "Not documented"
    if isinstance(value, datetime):
        parsed = value
    else:
        raw_value = str(value)
        try:
            parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            return raw_value

    display = parsed.strftime("%b %d, %Y · %I:%M %p")
    return display.replace("· 0", "· ")


def short_id(value: object, length: int = 8) -> str:
    if value is None or value == "":
        return "Unavailable"
    return str(value)[:length]


def humanize_label(value: object, default: str = "Unavailable") -> str:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return "Yes" if value else "No"

    normalized = str(value).strip()
    label_map = {
        "review_completed": "Review completed",
        "pending_review": "Pending review",
        "safety_rule_override": "Safety-rule escalation",
        "model": "Model",
        "model_tuned": "Tuned model",
        "accept": "Accepted",
        "override": "Override",
        "true": "Yes",
        "false": "No",
    }
    return label_map.get(normalized.lower(), normalized.replace("_", " ").title())


def apply_theme() -> None:
    """Apply the shared healthcare workflow visual system."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --ta-bg: #f1f7fb;
            --ta-panel: #ffffff;
            --ta-panel-soft: #f8fbff;
            --ta-text: #0f172a;
            --ta-emphasis: #13293d;
            --ta-muted: #475569;
            --ta-border: #cfe3f0;
            --ta-border-strong: #9bd8f5;
            --ta-primary: #0284c7;
            --ta-primary-dark: #0369a1;
            --ta-primary-soft: #e0f2fe;
            --ta-success: #059669;
            --ta-success-soft: #ecfdf5;
            --ta-warning: #92400e;
            --ta-warning-soft: #fff7dc;
            --ta-danger: #dc2626;
            --ta-shadow: 0 16px 36px rgba(15, 80, 120, 0.11);
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: var(--ta-text);
        }

        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        .stDeployButton,
        [data-testid="stSidebarCollapseButton"],
        button[kind="header"] {
            display: none !important;
            visibility: hidden;
            height: 0 !important;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarUserContent"] {
            display: none !important;
            visibility: hidden !important;
        }

        .stApp {
            background:
                radial-gradient(circle at 18% 8%, rgba(14, 165, 233, 0.07), transparent 24%),
                radial-gradient(circle at 82% 0%, rgba(16, 185, 129, 0.055), transparent 23%),
                var(--ta-bg);
        }

        [data-testid="stAppViewContainer"] {
            margin-left: 0 !important;
            padding-left: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }

        section[data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            flex: 0 0 0 !important;
        }

        [data-testid="stMain"] {
            margin-left: 0 !important;
            padding-left: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }

        [data-testid="stMain"] > div {
            width: 100% !important;
            max-width: 100% !important;
        }

        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
            color: #334155;
        }

        section[data-testid="stSidebar"] .stAlert {
            border-radius: 12px;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            display: none;
        }

        section[data-testid="stSidebar"] > div {
            padding: 1rem .85rem 1.25rem .85rem;
        }

        section[data-testid="stSidebar"] a[data-testid="stPageLink"] {
            border-radius: 12px;
            border: 1px solid transparent;
            background: transparent;
            box-shadow: none;
            min-height: 40px;
            color: #12324a;
            margin: 3px 0;
            padding: 6px 8px;
        }

        section[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover {
            background: #e0f2fe;
            border-color: #bae6fd;
            color: #0369a1;
        }

        section.main > div.block-container,
        section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
        [data-testid="stMainBlockContainer"],
        .block-container {
            box-sizing: border-box;
            width: 100% !important;
            max-width: 1260px !important;
            padding-top: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-bottom: 3rem !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        .ta-shell,
        .ta-section {
            width: 100%;
            max-width: 1260px;
            margin-left: auto;
            margin-right: auto;
            box-sizing: border-box;
        }

        .ta-shell-wide {
            width: 100%;
            max-width: 1260px;
            margin-left: auto;
            margin-right: auto;
            box-sizing: border-box;
        }

        h1, h2, h3 {
            color: var(--ta-text);
            letter-spacing: 0;
        }

        .ta-navbar,
        .ta-appbar,
        .ta-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.97);
            border: 1px solid #b9d9ea;
            border-top: 4px solid var(--ta-primary);
            border-radius: 14px;
            padding: 12px 16px;
            box-shadow: 0 12px 28px rgba(15, 80, 120, 0.11);
            margin-bottom: 18px;
            position: sticky;
            top: 0.35rem;
            z-index: 40;
            backdrop-filter: blur(10px);
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
            color: var(--ta-text);
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

        .ta-status-pill,
        .ta-page-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 13px;
            border-radius: 999px;
            background: #ecfdf5;
            color: var(--ta-success);
            font-size: 13px;
            font-weight: 800;
            border: 1px solid #a7f3d0;
            white-space: nowrap;
        }

        .ta-appbar-right {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 10px;
            flex-wrap: wrap;
        }

        .ta-product-nav-label {
            color: var(--ta-primary-dark);
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin: -5px auto 7px auto;
            max-width: 860px;
        }

        .ta-product-nav-active {
            min-height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 14px;
            border: 1px solid #9bd8f5;
            background: #e0f2fe;
            color: var(--ta-primary-dark);
            font-size: 14px;
            font-weight: 850;
            box-shadow: 0 8px 18px rgba(14, 165, 233, 0.10);
            text-align: center;
            padding: 0 10px;
            margin-bottom: 0;
        }

        .ta-workflow-nav-spacer {
            margin-bottom: 16px;
        }

        .ta-current-page {
            color: #12324a;
            font-size: 13px;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .ta-sidebar-brand {
            background: #f8fbff;
            border: 1px solid var(--ta-border);
            border-radius: 14px;
            padding: 11px 12px;
            margin-bottom: 12px;
        }

        .ta-sidebar-title {
            color: var(--ta-primary-dark);
            font-size: 12px;
            font-weight: 850;
            letter-spacing: 0.1em;
            line-height: 1.2;
            text-transform: uppercase;
            margin: 0;
        }

        .ta-sidebar-subtitle {
            color: #475569;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: none;
            margin-top: 5px;
        }

        .ta-sidebar-section {
            color: var(--ta-primary-dark);
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin: 14px 0 8px 0;
        }

        .ta-sidebar-active {
            background: #e0f2fe;
            border: 1px solid #bae6fd;
            border-left: 4px solid var(--ta-primary);
            border-radius: 12px;
            color: var(--ta-primary-dark);
            font-weight: 850;
            padding: 9px 10px;
            margin: 3px 0;
            font-size: 13px;
            box-shadow: 0 8px 18px rgba(14, 165, 233, 0.10);
        }

        .ta-sidebar-nav-icon {
            display: inline-flex;
            width: 20px;
            justify-content: center;
            margin-right: 7px;
        }

        .ta-sidebar-status {
            background: #ffffff;
            border: 1px solid var(--ta-border);
            border-radius: 14px;
            padding: 12px;
            box-shadow: 0 8px 20px rgba(15, 80, 120, 0.06);
            margin-top: 12px;
        }

        .ta-sidebar-status.ok {
            border-left: 4px solid var(--ta-success);
        }

        .ta-sidebar-status.warn {
            border-left: 4px solid #f59e0b;
        }

        .ta-sidebar-status-title {
            color: var(--ta-text);
            font-size: 13px;
            font-weight: 850;
            margin-bottom: 5px;
        }

        .ta-sidebar-status-body {
            color: var(--ta-muted);
            font-size: 12px;
            line-height: 1.45;
        }

        .ta-hero {
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            background: linear-gradient(135deg, #ffffff 0%, #f6fbff 100%);
            border: 1px solid #b9d9ea;
            border-left: 6px solid var(--ta-primary);
            border-radius: 22px;
            padding: 28px 32px;
            box-shadow: 0 18px 44px rgba(15, 80, 120, 0.13);
            margin-bottom: 15px;
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
            font-size: 42px;
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
            background: #ffffff;
            border: 1px solid #b9d9ea;
            border-left: 5px solid var(--ta-primary);
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: var(--ta-shadow);
            margin: 0 0 16px 0;
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
            color: #475569;
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
            margin: 14px 0;
            align-items: stretch;
        }

        .ta-grid .ta-card {
            height: 100%;
        }

        .ta-card,
        .clinical-card,
        .hero-card {
            background: #ffffff;
            border: 1px solid #bddbed;
            border-radius: 16px;
            padding: 18px;
            box-shadow: var(--ta-shadow);
            margin-bottom: 14px;
        }

        .hero-card {
            border-top: 4px solid var(--ta-primary);
        }

        .hero-card.escalated {
            border-color: #f59e0b;
            border-top-color: var(--ta-danger);
            background: linear-gradient(180deg, #fffafa 0%, #ffffff 58%);
        }

        .ta-safety-banner {
            border: 1px solid #f59e0b;
            border-left: 5px solid var(--ta-danger);
            background: #fffbeb;
            color: #7c2d12;
            border-radius: 16px;
            padding: 14px 16px;
            margin: 10px 0 14px 0;
            box-shadow: 0 10px 24px rgba(180, 83, 9, 0.08);
            line-height: 1.55;
        }

        .ta-safety-banner strong {
            display: block;
            color: #991b1b;
            font-size: 14px;
            margin-bottom: 3px;
        }

        .ta-card h3 {
            color: #0f2742;
            font-size: 18px;
            margin: 0 0 8px 0;
            font-weight: 800;
        }

        .ta-card p {
            color: #475569;
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
            max-width: 760px;
            margin: 0 auto 18px auto;
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
            border: 1px solid #bddbed;
            border-radius: 18px;
            padding: 16px;
            box-shadow: var(--ta-shadow);
            margin: 14px 0;
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
            background: #f8fbff;
            border: 1px solid #c4e1f1;
            border-radius: 14px;
            padding: 11px 10px;
            text-align: center;
            min-height: 72px;
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
            max-width: 760px;
            margin: 20px auto;
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
        .ta-kpi-grid,
        .metric-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 16px 0;
        }

        .ta-kpi-grid.six {
            grid-template-columns: repeat(6, minmax(0, 1fr));
        }

        .ta-kpi-grid.five {
            grid-template-columns: repeat(5, minmax(0, 1fr));
        }

        .ta-status-card,
        .ta-kpi-card,
        .mini-metric,
        div[data-testid="stMetric"] {
            border: 1px solid #c4e1f1;
            border-radius: 14px;
            padding: 13px 14px;
            background: #ffffff;
            box-shadow: 0 8px 22px rgba(15, 80, 120, 0.055);
            min-width: 0;
        }

        .ta-kpi-card {
            border-top: 4px solid #94a3b8;
            min-height: 96px;
            overflow: hidden;
        }

        .ta-kpi-card.neutral { border-top-color: #94a3b8; }
        .ta-kpi-card.blue { border-top-color: var(--ta-primary); background: #f8fcff; }
        .ta-kpi-card.green { border-top-color: var(--ta-success); background: #f8fffc; }
        .ta-kpi-card.amber { border-top-color: #f59e0b; background: #fffdf5; }
        .ta-kpi-card.red { border-top-color: var(--ta-danger); background: #fffafa; }

        .ta-status-title,
        .ta-kpi-label,
        .metric-label {
            color: var(--ta-primary-dark);
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            line-height: 1.3;
        }

        .ta-status-value,
        .ta-kpi-value,
        .metric-value {
            color: var(--ta-text);
            font-size: clamp(15px, 1.35vw, 22px);
            font-weight: 850;
            margin-top: 4px;
            line-height: 1.18;
            white-space: normal;
            overflow-wrap: break-word;
            word-break: break-word;
        }

        .ta-status-helper,
        .ta-kpi-helper {
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
            color: #047857;
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

        .ta-dev-sidebar {
            font-size: 11px;
            line-height: 1.5;
            overflow-wrap: anywhere;
        }

        .ta-vitals-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 14px;
            margin-top: 8px;
        }

        .ta-vital-card {
            background: #ffffff;
            border: 1px solid #bddbed;
            border-top: 4px solid var(--ta-primary);
            border-radius: 14px;
            padding: 12px;
            box-shadow: 0 10px 24px rgba(15, 80, 120, 0.07);
            margin-bottom: 4px;
        }

        .ta-vital-card.green {
            border-top-color: var(--ta-success);
            background: #f8fffc;
        }

        .ta-vital-card.amber {
            border-top-color: #f59e0b;
            background: #fffdf5;
        }

        .ta-vital-card.red {
            border-top-color: var(--ta-danger);
            background: #fffafa;
        }

        .ta-vital-card.neutral {
            border-top-color: #94a3b8;
            background: #f8fafc;
        }

        .ta-vital-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 6px;
        }

        .ta-vital-label {
            color: var(--ta-primary-dark);
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .ta-vital-status {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 900;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            color: #475569;
            white-space: nowrap;
        }

        .ta-vital-card.green .ta-vital-status {
            border-color: #a7f3d0;
            background: #ecfdf5;
            color: #047857;
        }

        .ta-vital-card.amber .ta-vital-status {
            border-color: #fed7aa;
            background: #fff7ed;
            color: #b45309;
        }

        .ta-vital-card.red .ta-vital-status {
            border-color: #fecaca;
            background: #fef2f2;
            color: #b91c1c;
        }

        .ta-vital-value {
            color: var(--ta-text);
            font-size: 24px;
            font-weight: 850;
            line-height: 1.05;
            margin: 4px 0;
        }

        .ta-vital-unit {
            color: #64748b;
            font-size: 13px;
            font-weight: 800;
            margin-left: 4px;
        }

        .ta-vital-helper {
            color: var(--ta-muted);
            font-size: 12px;
            line-height: 1.4;
            margin-bottom: 8px;
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
            section.main > div.block-container,
            section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
            [data-testid="stMainBlockContainer"],
            .block-container,
            .ta-shell,
            .ta-shell-wide {
                width: 100%;
                max-width: 100% !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            .ta-grid, .ta-steps, .ta-status-grid, .ta-kpi-grid, .ta-kpi-grid.six, .ta-kpi-grid.five, .metric-row, .ta-vitals-grid {
                grid-template-columns: 1fr;
            }
            .ta-hero {
                padding: 24px 22px;
            }
            .ta-hero h1 {
                font-size: 34px;
            }
            .ta-page-header h1,
            .clinical-header h1,
            .ta-auth-card h1 {
                font-size: 28px;
            }
            .ta-appbar,
            .ta-topbar {
                flex-direction: column;
                align-items: flex-start;
                gap: 12px;
                position: relative;
                top: 0;
            }
            .final-esi {
                font-size: 2.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_bar(current_page: str, status_label: str = "System Active") -> None:
    _render_html(
        f"""
        <div class="ta-appbar">
            <div class="ta-brand">
                <div class="ta-logo">+</div>
                <div>
                    <div class="ta-brand-title">TriageAI / SympDirect</div>
                    <div class="ta-brand-subtitle">ESI Clinical Intake & Care Routing</div>
                </div>
            </div>
            <div class="ta-appbar-right">
                <div class="ta-current-page">{escape(current_page)}</div>
                <div class="ta-status-pill">{escape(status_label)}</div>
            </div>
        </div>
        """
    )


def render_product_nav(current_page: str) -> None:
    nav_items = [
        ("Home", "Home.py", "Home"),
        ("New Assessment", "pages/02_New_Assessment.py", "New Assessment"),
        ("Dashboard", "pages/05_Dashboard.py", "Dashboard"),
        ("Review", "pages/04_Clinician_Review.py", "Clinician Review"),
        ("Assessment Detail", "pages/06_Assessment_Detail.py", "Assessment Detail"),
    ]

    _render_html('<div class="ta-product-nav-label">Workflow Navigation</div>')
    nav_cols = st.columns([1, 1.35, 1, 1, 1.35], gap="small")
    for column, (label, page, page_name) in zip(nav_cols, nav_items):
        with column:
            if current_page == page_name:
                _render_html(
                    f'<div class="ta-product-nav-active">{escape(label)}</div>'
                )
            elif st.button(
                label,
                key=f"workflow_nav_{current_page}_{label}",
                width="stretch",
            ):
                st.switch_page(page)
    _render_html('<div class="ta-workflow-nav-spacer"></div>')


def render_fixed_app_nav(
    current_page: str, status_label: str = "System Active"
) -> None:
    render_app_bar(current_page, status_label)
    render_product_nav(current_page)


def render_top_header(status_label: str = "System Active") -> None:
    render_app_bar("TriageAI", status_label)


def render_sidebar_navigation(current_page: str) -> dict:
    from app.frontend.streamlit_app.services.api_client import get_ready_status

    status = get_ready_status()
    return status


def render_sidebar_shell(current_page: str) -> dict:
    return render_sidebar_navigation(current_page)


def render_page_header(
    title: str,
    subtitle: str | None = None,
    eyebrow: str | None = None,
) -> None:
    render_page_hero(eyebrow or "", title, subtitle or "")


def render_page_hero(
    eyebrow: str,
    title: str,
    subtitle: str,
    status_label: str | None = None,
) -> None:
    eyebrow_html = f'<div class="ta-eyebrow">{escape(eyebrow)}</div>' if eyebrow else ""
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    status_html = (
        f'<div class="ta-page-pill">{escape(status_label)}</div>'
        if status_label
        else ""
    )
    _render_html(
        f"""
        <div class="ta-page-header">
            {eyebrow_html}
            <h1>{escape(title)}</h1>
            {subtitle_html}
            {status_html}
        </div>
        """
    )


def render_badges(labels: list[str]) -> None:
    badges = "".join(
        [f'<span class="ta-badge">{escape(label)}</span>' for label in labels]
    )
    _render_html(f'<div class="ta-badges">{badges}</div>')


def render_disclaimer(text: str | None = None) -> None:
    _render_html(
        f'<div class="ta-disclaimer">{escape(text or DEFAULT_DISCLAIMER)}</div>'
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
    _render_html(
        f"""
        <div class="ta-empty-state">
            <div class="ta-empty-icon">+</div>
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
            {action_html}
        </div>
        """
    )


def render_status_card(title: str, value: str | int, helper: str | None = None) -> None:
    helper_html = (
        f'<div class="ta-status-helper">{escape(helper)}</div>' if helper else ""
    )
    _render_html(
        f"""
        <div class="ta-status-card">
            <div class="ta-status-title">{escape(title)}</div>
            <div class="ta-status-value">{escape(str(value))}</div>
            {helper_html}
        </div>
        """
    )


def _kpi_card_html(
    label: str,
    value: str | int,
    helper: str | None = None,
    tone: str = "neutral",
) -> str:
    safe_tone = _tone_class(tone)
    helper_html = f'<div class="ta-kpi-helper">{escape(helper)}</div>' if helper else ""
    return f"""
    <div class="ta-kpi-card {safe_tone}">
        <div class="ta-kpi-label">{escape(label)}</div>
        <div class="ta-kpi-value">{escape(str(value))}</div>
        {helper_html}
    </div>
    """


def render_kpi_card(
    label: str,
    value: str | int,
    helper: str | None = None,
    tone: str = "neutral",
) -> None:
    _render_html(_kpi_card_html(label, value, helper, tone))


def render_kpi_grid(cards: list[tuple[str, str | int, str | None, str]]) -> None:
    count_class = "six" if len(cards) >= 6 else "five" if len(cards) == 5 else ""
    card_html = "".join(
        _kpi_card_html(label, value, helper, tone)
        for label, value, helper, tone in cards
    )
    _render_html(f'<div class="ta-kpi-grid {count_class}">{card_html}</div>')


def render_info_card(title: str, body: str, tone: str = "neutral") -> None:
    safe_tone = _tone_class(tone)
    _render_html(
        f"""
        <div class="ta-kpi-card {safe_tone}">
            <div class="ta-kpi-label">{escape(title)}</div>
            <div class="ta-kpi-helper">{escape(body)}</div>
        </div>
        """
    )


def _action_card_html(title: str, body: str) -> str:
    return f"""
    <div class="ta-card">
        <h3>{escape(title)}</h3>
        <p>{escape(body)}</p>
    </div>
    """


def render_action_card(title: str, body: str) -> None:
    _render_html(_action_card_html(title, body))


def render_section_label(label: str) -> None:
    _render_html(f'<div class="ta-section-label">{escape(label)}</div>')


def render_action_grid(actions: list[tuple[str, str]]) -> None:
    cards = "".join(_action_card_html(title, body) for title, body in actions)
    _render_html(f'<div class="ta-grid">{cards}</div>')


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
    _render_html(
        f"""
        <div class="ta-workflow">
            <div class="ta-section-label">Workflow Overview</div>
            <div class="ta-steps">{step_html}</div>
        </div>
        """
    )


def render_home_hero() -> None:
    _render_html(
        """
        <div class="ta-hero">
            <div class="ta-eyebrow">Clinical Decision-Support Workflow</div>
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
                <span class="ta-badge">PDF Decision-Support Summary</span>
            </div>
        </div>
        """
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
