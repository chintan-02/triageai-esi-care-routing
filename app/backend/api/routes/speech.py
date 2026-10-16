from fastapi import APIRouter, Depends, File, UploadFile

from app.backend.core.security import get_authenticated_db

from app.backend.schemas.speech import SpeechTranscriptionResponse
from app.backend.services.speech_service import transcribe_audio

router = APIRouter(prefix="/speech", tags=["speech"], dependencies=[Depends(get_authenticated_db)])


@router.post("/transcribe", response_model=SpeechTranscriptionResponse)
def transcribe_speech(
    audio_file: UploadFile = File(...),
) -> SpeechTranscriptionResponse:
    return transcribe_audio(audio_file)
