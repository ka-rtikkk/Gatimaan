"""Machine-learning endpoints for maintenance delay-risk assessment."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.ml.risk_predictor import model_info, predict_delay_risk

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict-risk")
async def predict_risk(request: Dict[str, Any], current_user: dict = Depends(get_current_user)):
    try:
        task = request.get("task", request)
        prediction = predict_delay_risk(task)
        probability = prediction["risk_probability"]
        prediction["recommendation"] = (
            "Prioritize within the next compatible maintenance window"
            if probability >= 0.45 else
            "Schedule within a suitable maintenance window"
        )
        return prediction
    except Exception as exc:
        logger.exception("ML risk prediction failed")
        raise HTTPException(status_code=503, detail="ML risk prediction is currently unavailable") from exc


@router.get("/model-info")
async def get_model_info(current_user: dict = Depends(get_current_user)):
    try:
        return model_info()
    except Exception as exc:
        logger.exception("ML model info unavailable")
        raise HTTPException(status_code=503, detail="ML model is currently unavailable") from exc
