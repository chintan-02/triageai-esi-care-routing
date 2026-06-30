"""Probability display helpers."""

from __future__ import annotations

import streamlit as st


def render_probability_section(
    probabilities: dict[str, float],
    predicted_esi: int | None = None,
) -> None:
    st.markdown('<div class="section-title">ESI Class Probabilities</div>', unsafe_allow_html=True)
    if not probabilities:
        st.info("No model probabilities were returned.")
        return

    with st.container(border=True):
        for label in ["ESI_3", "ESI_4", "ESI_5"]:
            value = max(0.0, min(1.0, float(probabilities.get(label, 0.0))))
            display_label = label.replace("_", " ")
            selected = predicted_esi is not None and label == f"ESI_{predicted_esi}"
            selected_text = " Selected" if selected else ""

            st.markdown(f"**{display_label}{selected_text}** · {value:.1%}")
            st.progress(value)
