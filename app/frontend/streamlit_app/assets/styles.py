"""Shared Streamlit CSS for the TriageAI frontend."""

import streamlit as st


def apply_app_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.7rem;
            padding-bottom: 3rem;
            max-width: 1100px;
        }
        .clinical-header {
            border-bottom: 1px solid #d0e4f1;
            padding-bottom: 0.75rem;
            margin-bottom: 1rem;
        }
        .eyebrow {
            color: #0369a1;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }
        .section-title {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin: 1.05rem 0 0.55rem 0;
            color: #0e1f35;
            font-weight: 800;
            font-size: 1rem;
        }
        .section-title:after {
            content: "";
            flex: 1;
            height: 1px;
            background: #d0e4f1;
        }
        .clinical-card {
            border: 1px solid #d7e5ee;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            background: #ffffff;
            box-shadow: 0 1px 5px rgba(14, 90, 140, 0.05);
            margin-bottom: 1rem;
        }
        .hero-card {
            border: 1.5px solid #bae6fd;
            border-left: 6px solid #0369a1;
            border-radius: 8px;
            padding: 1.25rem 1.35rem;
            background: linear-gradient(135deg, #f7fbff 0%, #ffffff 55%);
            box-shadow: 0 4px 18px rgba(14, 90, 140, 0.08);
            margin: 0.6rem 0 1rem 0;
        }
        .hero-grid {
            display: grid;
            grid-template-columns: 1.15fr 1.6fr;
            gap: 1.2rem;
            align-items: center;
        }
        .final-esi {
            font-size: 3.5rem;
            font-weight: 900;
            color: #0369a1;
            line-height: 1;
            letter-spacing: 0;
        }
        .metric-row {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 0.8rem;
        }
        .mini-metric {
            border: 1px solid #d7e5ee;
            border-radius: 8px;
            padding: 0.72rem 0.8rem;
            background: #ffffff;
        }
        .metric-label {
            color: #6b8294;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .metric-value {
            color: #0e1f35;
            font-size: 1.05rem;
            font-weight: 800;
            margin-top: 0.15rem;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 99px;
            padding: 0.18rem 0.62rem;
            font-size: 0.74rem;
            font-weight: 800;
            margin-right: 0.35rem;
            border: 1px solid #d7e5ee;
            background: #f7fbff;
            color: #31566f;
        }
        .badge-ok {
            background: #ecfdf5;
            border-color: #a7f3d0;
            color: #047857;
        }
        .badge-warn {
            background: #fff7ed;
            border-color: #fed7aa;
            color: #b45309;
        }
        .note-box {
            border: 1px solid #d7e5ee;
            border-left: 4px solid #0369a1;
            border-radius: 8px;
            padding: 1rem;
            background: #fbfdff;
            white-space: pre-wrap;
            color: #1e3a52;
            line-height: 1.6;
        }
        .safety-ok {
            border: 1px solid #a7f3d0;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #ecfdf5;
            color: #065f46;
            font-weight: 700;
        }
        .safety-warn {
            border: 1px solid #fbbf24;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #fffbeb;
            color: #92400e;
        }
        .warning-box {
            border: 1px solid #e2c15c;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #fff9e8;
            color: #7c5a00;
            margin: 0.75rem 0 1rem 0;
        }
        .disclaimer {
            border: 1px solid #fed7aa;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            background: #fff7ed;
            color: #92400e;
            font-weight: 700;
            margin-top: 1rem;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #d7e5ee;
            border-radius: 8px;
            padding: 0.8rem;
            background: #ffffff;
        }
        @media (max-width: 760px) {
            .hero-grid,
            .metric-row {
                grid-template-columns: 1fr;
            }
            .final-esi {
                font-size: 2.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
