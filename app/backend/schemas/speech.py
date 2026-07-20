"""Speech-to-text response schemas."""

from pydantic import BaseModel


class SpeechTranscriptionResponse(BaseModel):
    transcript_text: str
    transcript: str
    confidence: float | None = None
    language: str = "en-US"
    source: str = "speech_transcript"
    requires_clinician_review: bool = True
    is_placeholder: bool
    message: str
    disclaimer: str = (
        "Decision support only. Transcript requires clinician review before NLP "
        "extraction or prediction."
    )
