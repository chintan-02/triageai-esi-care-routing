from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.assets.styles import apply_app_styles
from app.frontend.streamlit_app.components.intake_form import render_intake_form
from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.services.api_client import submit_prediction


st.set_page_config(page_title="New Assessment | TriageAI", layout="wide")
apply_app_styles()

st.title("New Assessment")
st.caption("Submit structured intake to the FastAPI ESI prediction endpoint.")

render_backend_status()

submitted, payload = render_intake_form()

if submitted:
    if not payload["chief_complaint"] or len(payload["chief_complaint"]) < 3:
        st.error("Chief complaint must be at least 3 characters.")
    else:
        with st.spinner("Running backend ESI assessment..."):
            api_result = submit_prediction(payload)

        if api_result.get("ok"):
            st.session_state["last_intake_payload"] = payload
            st.session_state["last_prediction_result"] = api_result["data"]
            if api_result.get("message"):
                st.warning(api_result["message"])
            st.success("Assessment complete.")
            try:
                st.switch_page("pages/03_Result.py")
            except Exception:
                st.info("Open the Assessment Result page from the sidebar to view details.")
        else:
            st.error(api_result.get("message") or "Prediction request failed.")
            if api_result.get("error_type") == "connection":
                st.code(api_result.get("start_command", ""), language="bash")
            details = api_result.get("data")
            if details:
                st.json(details)
