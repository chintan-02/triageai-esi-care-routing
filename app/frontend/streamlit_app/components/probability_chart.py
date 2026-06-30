"""Probability display helpers."""

from __future__ import annotations

import streamlit as st


def render_probability_section(probabilities: dict[str, float]) -> None:
    st.subheader("ESI Class Probabilities")
    if not probabilities:
        st.info("No model probabilities were returned.")
        return

    for label in ["ESI_3", "ESI_4", "ESI_5"]:
        value = float(probabilities.get(label, 0.0))
        st.write(f"{label.replace('_', ' ')}: **{value:.1%}**")
        st.progress(max(0.0, min(1.0, value)))
