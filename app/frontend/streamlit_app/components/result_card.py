"""ESI result hero display helpers."""

from __future__ import annotations

from html import escape

import streamlit as st

from app.frontend.streamlit_app.ui_theme import humanize_label


ESI_INTERPRETATION = {
    1: "Immediate clinician review and care-routing escalation required.",
    2: "Safety-rule escalation: high-priority clinician review recommended.",
    3: "Urgent evaluation; patient may require multiple resources.",
    4: "Lower-acuity evaluation pathway; likely one resource after review.",
    5: "Non-urgent care pathway; minimal resources may be appropriate after review.",
}


def _confidence_text(value: object) -> str:
    if value is None:
        return "Unavailable"
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "Unavailable"


def _esi_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def render_main_result_card(result: dict) -> None:
    final_esi = result.get("final_esi") or "Pending"
    predicted_esi = result.get("predicted_esi") or "Pending"
    confidence = _confidence_text(result.get("confidence_score"))
    final_source = result.get("final_source") or "fallback"
    model_loaded = bool(result.get("model_loaded"))
    is_placeholder = bool(result.get("is_placeholder"))
    source_label = humanize_label(final_source)
    final_esi_int = _esi_int(result.get("final_esi"))
    high_risk = final_esi_int in {1, 2} or final_source == "safety_rule_override"
    hero_class = "hero-card escalated" if high_risk else "hero-card"

    interpretation = ESI_INTERPRETATION.get(
        final_esi_int,
        "Model estimates ESI 3/4/5; safety rules may escalate final ESI to 2.",
    )
    model_badge_class = "badge-ok" if model_loaded else "badge-warn"
    placeholder_badge_class = "badge-warn" if is_placeholder else "badge-ok"
    placeholder_text = "Fallback response" if is_placeholder else "Real model output"
    escalation_banner = (
        """
        <div class="ta-safety-banner">
          <strong>Safety-rule escalation applied.</strong>
          Final ESI was escalated for clinician review. Decision-support only; clinician judgment is required.
        </div>
        """
        if high_risk
        else ""
    )

    st.markdown(
        f"""
        {escalation_banner}
        <div class="{hero_class}">
          <div class="hero-grid">
            <div>
              <div class="eyebrow">Final ESI</div>
              <div class="final-esi">{escape(str(final_esi))}</div>
              <div style="color:#31566f;font-weight:700;margin-top:.35rem;">
                {escape(interpretation)}
              </div>
              <div style="margin-top:.8rem;">
                <span class="badge {model_badge_class}">Model loaded: {escape(humanize_label(model_loaded))}</span>
                <span class="badge {placeholder_badge_class}">{escape(placeholder_text)}</span>
              </div>
            </div>
            <div>
              <div class="metric-row">
                <div class="mini-metric">
                  <div class="metric-label">Predicted ESI</div>
                  <div class="metric-value">{escape(str(predicted_esi))}</div>
                </div>
                <div class="mini-metric">
                  <div class="metric-label">Confidence</div>
                  <div class="metric-value">{escape(confidence)}</div>
                </div>
                <div class="mini-metric">
                  <div class="metric-label">Final Source</div>
                  <div class="metric-value">{escape(source_label)}</div>
                </div>
              </div>
              <div style="margin-top:.85rem;color:#526070;font-size:.9rem;line-height:1.55;">
                ESI 3 indicates urgent evaluation and likely multiple resources.
                ESI 4 suggests lower-acuity evaluation with likely one resource.
                ESI 5 suggests non-urgent/minimal-resource care after clinician review.
                Safety rules may escalate the final recommendation to ESI 2 when
                high-risk criteria are triggered.
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
