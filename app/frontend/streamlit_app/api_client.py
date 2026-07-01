"""Compatibility wrapper for the Streamlit backend API client."""

from app.frontend.streamlit_app.services.api_client import (  # noqa: F401
    BACKEND_URL,
    START_BACKEND_COMMAND,
    get_assessment_detail,
    get_dashboard_summary,
    get_ready_status,
    submit_clinician_review,
    submit_prediction,
)
