from fastapi import APIRouter, Depends

from app.backend.core.security import get_authenticated_db

from app.backend.schemas.nlp import (
    ClinicalIntakeExtractionRequest,
    ClinicalIntakeExtractionResponse,
)
from app.backend.services.clinical_nlp.extractor import extract_clinical_intake


router = APIRouter(prefix="/nlp", tags=["Clinical Intake NLP"], dependencies=[Depends(get_authenticated_db)])


@router.post("/extract-intake", response_model=ClinicalIntakeExtractionResponse)
def extract_intake(
    request: ClinicalIntakeExtractionRequest,
) -> ClinicalIntakeExtractionResponse:
    return extract_clinical_intake(request.note_text)