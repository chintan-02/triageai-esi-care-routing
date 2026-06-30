"""Shared Streamlit CSS for the TriageAI frontend."""

import streamlit as st


def apply_app_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }
        .triage-section {
            border: 1px solid #d7dee8;
            border-radius: 8px;
            padding: 1.1rem 1.2rem;
            background: #ffffff;
            margin-bottom: 1rem;
        }
        .triage-muted {
            color: #526070;
            font-size: 0.92rem;
        }
        .result-band {
            border-left: 5px solid #2f6f73;
            background: #f7fbfb;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.75rem 0 1rem 0;
        }
        .note-box {
            border: 1px solid #d7dee8;
            border-radius: 8px;
            padding: 1rem;
            background: #fbfcfe;
            white-space: pre-wrap;
        }
        .warning-box {
            border: 1px solid #e2c15c;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            background: #fff9e8;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #d7dee8;
            border-radius: 8px;
            padding: 0.8rem;
            background: #ffffff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
