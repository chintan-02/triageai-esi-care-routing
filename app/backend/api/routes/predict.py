from fastapi import APIRouter

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import ESIPredictionResponse
from app.backend.services.prediction_service import validate_prediction_contract

router = APIRouter(prefix="/predict", tags=["prediction"])


@router.post("", response_model=ESIPredictionResponse)
def predict_esi(intake: PatientIntakeRequest) -> ESIPredictionResponse:
    return validate_prediction_contract(intake)
