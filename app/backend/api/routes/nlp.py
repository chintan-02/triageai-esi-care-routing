from fastapi import APIRouter

from app.backend.schemas.nlp import (
    ClinicalIntakeExtractionRequest,
    ClinicalIntakeExtractionResponse,
)
from app.backend.services.clinical_nlp.extractor import extract_clinical_intake


router = APIRouter(prefix="/nlp", tags=["Clinical Intake NLP"])


@router.post("/extract-intake", response_model=ClinicalIntakeExtractionResponse)
def extract_intake(
    request: ClinicalIntakeExtractionRequest,
) -> ClinicalIntakeExtractionResponse:
    return extract_clinical_intake(request.note_text)