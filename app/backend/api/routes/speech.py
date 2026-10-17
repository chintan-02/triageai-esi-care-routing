from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.backend.core.config import settings
from app.backend.core.security import get_authenticated_db

from app.backend.schemas.speech import SpeechTranscriptionResponse
from app.backend.services.speech_service import transcribe_audio

router = APIRouter(prefix="/speech", tags=["speech"], dependencies=[Depends(get_authenticated_db)])


@router.post("/transcribe", response_model=SpeechTranscriptionResponse)
def transcribe_speech(
    audio_file: UploadFile = File(...),
) -> SpeechTranscriptionResponse:
    if audio_file.size is None or audio_file.size > settings.MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio upload exceeds the allowed size")
    return transcribe_audio(audio_file)
