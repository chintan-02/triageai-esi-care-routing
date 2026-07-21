from fastapi import APIRouter, File, UploadFile

from app.backend.schemas.speech import SpeechTranscriptionResponse
from app.backend.services.speech_service import transcribe_audio

router = APIRouter(prefix="/speech", tags=["speech"])


@router.post("/transcribe", response_model=SpeechTranscriptionResponse)
def transcribe_speech(
    audio_file: UploadFile = File(...),
) -> SpeechTranscriptionResponse:
    return transcribe_audio(audio_file)
