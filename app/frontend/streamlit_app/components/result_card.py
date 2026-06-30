"""ESI result display helpers."""

from __future__ import annotations

import streamlit as st


def render_main_result_card(result: dict) -> None:
    confidence = result.get("confidence_score")
    confidence_text = f"{float(confidence):.1%}" if confidence is not None else "Unavailable"

    st.markdown('<div class="result-band">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Final ESI", result.get("final_esi") or "Pending")
    col2.metric("Predicted ESI", result.get("predicted_esi") or "Pending")
    col3.metric("Confidence", confidence_text)
    col4.metric("Final Source", result.get("final_source") or "fallback")
    st.markdown("</div>", unsafe_allow_html=True)
