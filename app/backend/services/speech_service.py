"""Safe Azure Speech-to-Text integration for uploaded audio."""

import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.backend.core.config import settings
from app.backend.schemas.speech import SpeechTranscriptionResponse

logger = logging.getLogger(__name__)

LANGUAGE = "en-US"
DISCLAIMER = (
    "Decision support only. Transcript requires clinician review before NLP "
    "extraction or prediction."
)
AZURE_UNCONFIGURED_MESSAGE = (
    "Azure Speech is not configured. Add AZURE_SPEECH_KEY and "
    "AZURE_SPEECH_REGION to enable transcription."
)
AZURE_SUCCESS_MESSAGE = (
    "Transcript generated. Clinician review is required before NLP extraction "
    "or prediction."
)
AZURE_ERROR_MESSAGE = (
    "Audio could not be transcribed. Confirm the file contains supported audio "
    "and try again."
)


class SpeechTranscriptionError(RuntimeError):
    """Normalized Azure transcription failure without credential details."""


def _response(
    *,
    transcript_text: str,
    source: str,
    is_placeholder: bool,
    message: str,
) -> SpeechTranscriptionResponse:
    return SpeechTranscriptionResponse(
        transcript_text=transcript_text,
        transcript=transcript_text,
        confidence=None,
        language=LANGUAGE,
        source=source,
        requires_clinician_review=True,
        is_placeholder=is_placeholder,
        message=message,
        disclaimer=DISCLAIMER,
    )


def _transcribe_file_with_azure(
    audio_path: Path,
    *,
    speech_key: str,
    speech_region: str,
) -> str:
    """Transcribe one utterance from a local file using the Azure Speech SDK."""
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as exc:  # pragma: no cover - dependency is present in deployment
        raise SpeechTranscriptionError("Azure Speech SDK is unavailable.") from exc

    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region,
        )
        speech_config.speech_recognition_language = LANGUAGE
        audio_config = speechsdk.audio.AudioConfig(filename=str(audio_path))
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )
        result = recognizer.recognize_once_async().get()
    except Exception as exc:
        raise SpeechTranscriptionError("Azure Speech request failed.") from exc

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        transcript_text = result.text.strip()
        if transcript_text:
            return transcript_text
        raise SpeechTranscriptionError("Azure Speech returned an empty transcript.")

    if result.reason == speechsdk.ResultReason.NoMatch:
        raise SpeechTranscriptionError("Azure Speech did not recognize speech.")

    if result.reason == speechsdk.ResultReason.Canceled:
        raise SpeechTranscriptionError("Azure Speech canceled transcription.")

    raise SpeechTranscriptionError("Azure Speech returned an unsupported result.")


def _temporary_suffix(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix and len(suffix) <= 10 and suffix[1:].isalnum():
        return suffix
    return ".wav"


def transcribe_audio(audio_file: UploadFile) -> SpeechTranscriptionResponse:
    """Transcribe an upload through Azure, or return a safe local placeholder."""
    speech_key = settings.AZURE_SPEECH_KEY.strip()
    speech_region = settings.AZURE_SPEECH_REGION.strip()

    if not speech_key or not speech_region:
        return _response(
            transcript_text="",
            source="azure_speech_unconfigured",
            is_placeholder=True,
            message=AZURE_UNCONFIGURED_MESSAGE,
        )

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=_temporary_suffix(audio_file.filename),
            delete=False,
        ) as temporary_file:
            shutil.copyfileobj(audio_file.file, temporary_file)
            temporary_path = Path(temporary_file.name)

        if temporary_path.stat().st_size == 0:
            return _response(
                transcript_text="",
                source="azure_speech_error",
                is_placeholder=True,
                message=AZURE_ERROR_MESSAGE,
            )

        transcript_text = _transcribe_file_with_azure(
            temporary_path,
            speech_key=speech_key,
            speech_region=speech_region,
        )
        return _response(
            transcript_text=transcript_text,
            source="azure_speech",
            is_placeholder=False,
            message=AZURE_SUCCESS_MESSAGE,
        )
    except Exception as exc:
        logger.warning("Azure Speech transcription failed safely: %s", type(exc).__name__)
        return _response(
            transcript_text="",
            source="azure_speech_error",
            is_placeholder=True,
            message=AZURE_ERROR_MESSAGE,
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def transcribe_audio_placeholder(audio_file: UploadFile) -> SpeechTranscriptionResponse:
    """Backward-compatible service name retained for existing callers."""
    return transcribe_audio(audio_file)
