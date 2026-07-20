"""Speech-to-text placeholder service."""

from fastapi import UploadFile

from app.backend.schemas.speech import SpeechTranscriptionResponse


def transcribe_audio_placeholder(audio_file: UploadFile) -> SpeechTranscriptionResponse:
    _ = audio_file
    return SpeechTranscriptionResponse(
        transcript_text="",
        transcript="",
        confidence=None,
        language="en-US",
        source="speech_transcript",
        requires_clinician_review=True,
        is_placeholder=True,
        message=(
            "Speech-to-text placeholder returned an empty transcript. Clinician "
            "review is required before using transcript text."
        ),
    )
