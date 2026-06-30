"""Speech-to-text placeholder service."""

from fastapi import UploadFile

from app.backend.schemas.speech import SpeechTranscriptionResponse


def transcribe_audio_placeholder(audio_file: UploadFile) -> SpeechTranscriptionResponse:
    _ = audio_file
    return SpeechTranscriptionResponse(
        transcript="",
        confidence=None,
        language="en-US",
        is_placeholder=True,
        message=(
            "Speech-to-text contract is ready. Azure Speech integration will be "
            "added in the next implementation phase."
        ),
    )
