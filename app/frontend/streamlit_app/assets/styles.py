"""Compatibility wrapper for the shared Streamlit theme."""

from app.frontend.streamlit_app.ui_theme import apply_theme


def apply_app_styles() -> None:
    """Apply the single shared frontend theme.

    Older pages still import this function; keeping it as a wrapper prevents
    competing CSS systems while those imports are migrated.
    """
    apply_theme()
