"""Speech-to-text response schemas."""

from pydantic import BaseModel


class SpeechTranscriptionResponse(BaseModel):
    transcript: str
    confidence: float | None = None
    language: str = "en-US"
    is_placeholder: bool
    message: str
