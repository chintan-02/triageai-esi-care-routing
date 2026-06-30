"""Shared Streamlit layout helpers."""

from __future__ import annotations

import streamlit as st

from app.frontend.streamlit_app.services.api_client import (
    START_BACKEND_COMMAND,
    get_ready_status,
)


def render_backend_status() -> dict:
    """Render backend readiness in the sidebar and return the normalized status."""
    status = get_ready_status()
    data = status.get("data") or {}

    with st.sidebar:
        st.markdown("### System Status")
        if status.get("ok"):
            st.success("Backend connected", icon="✅")
            st.caption(
                f"Model loaded: `{data.get('model_loaded')}`  \n"
                f"Database: `{data.get('database')}`"
            )
            if data.get("model_version"):
                st.caption(f"Model version: `{data.get('model_version')}`")
            if data.get("model_error"):
                st.warning(str(data.get("model_error")))
        else:
            st.error(status.get("message") or "Backend unavailable")
            st.code(START_BACKEND_COMMAND, language="bash")

    return status
