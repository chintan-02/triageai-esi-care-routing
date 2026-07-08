"""Human-readable text formatting helpers."""

import re


_MISSING_SPACE_REPLACEMENTS = {
    "ESIis": "ESI is",
    "modelprobability": "model probability",
    "Currentfinal": "Current final",
}


def clean_human_readable_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value
    for cramped, spaced in _MISSING_SPACE_REPLACEMENTS.items():
        cleaned = cleaned.replace(cramped, spaced)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;:])", r"\1", cleaned)
    return cleaned.strip()
