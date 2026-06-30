"""Clinician handoff summary card."""

from __future__ import annotations

import streamlit as st


def render_clinician_summary_card(summary: str | None) -> None:
    st.markdown('<div class="section-title">Clinician Handoff Summary</div>', unsafe_allow_html=True)
    summary_text = summary or "No clinician summary returned."
    st.text_area(
        "Copy-friendly summary",
        value=summary_text,
        height=150,
        label_visibility="collapsed",
    )
