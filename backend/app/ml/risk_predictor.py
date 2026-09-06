"""Maintenance delay-risk prediction using a persisted Random Forest pipeline."""

from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import joblib
    import pandas as pd
except ImportError as exc:  # pragma: no cover - exercised in dependency failure environments
    joblib = None
    pd = None
    _dependency_error = str(exc)
else:
    _dependency_error = None

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).with_name("model.joblib")
MODEL_TYPE = "RandomForestClassifier"
FEATURES = [
    "criticality", "urgency", "safety_risk", "asset_importance", "overdue",
    "duration_hours", "days_until_due", "department", "asset_type", "task_type", "corridor_id",
]
RISK_THRESHOLDS = {"HIGH": 0.75, "MEDIUM": 0.45}
_model: Any = None
_load_error: Optional[str] = None


def _days_until_due(task: Dict[str, Any]) -> int:
    due_date = task.get("due_date")
    if not due_date:
        return 30
    try:
        if isinstance(due_date, datetime):
            due = due_date.date()
        elif isinstance(due_date, date):
            due = due_date
        else:
            due = datetime.fromisoformat(str(due_date).replace("Z", "+00:00")).date()
        return max(-30, min(180, (due - date.today()).days))
    except (TypeError, ValueError, AttributeError):
        return 30


def task_features(task: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only fields present in the maintenance task contract."""
    return {
        "criticality": int(task.get("criticality", 3) or 3),
        "urgency": int(task.get("urgency", 3) or 3),
        "safety_risk": int(task.get("safety_risk", 3) or 3),
        "asset_importance": int(task.get("asset_importance", 3) or 3),
        "overdue": bool(task.get("overdue", False)),
        "duration_hours": float(task.get("duration_hours", 1.0) or 1.0),
        "days_until_due": _days_until_due(task),
        "department": str(task.get("department", "Unknown") or "Unknown"),
        "asset_type": str(task.get("asset_type", "Unknown") or "Unknown"),
        "task_type": str(task.get("task_type", "Unknown") or "Unknown"),
        "corridor_id": str(task.get("corridor_id", "Unknown") or "Unknown"),
    }


def load_model() -> Any:
    """Load the trained artifact once, raising a useful error when unavailable."""
    global _model, _load_error
    if _model is not None:
        return _model
    if _load_error:
        raise RuntimeError(_load_error)
    if _dependency_error:
        _load_error = f"ML dependencies unavailable: {_dependency_error}"
        logger.error(_load_error)
        raise RuntimeError(_load_error)
    try:
        _model = joblib.load(MODEL_PATH)
        return _model
    except Exception as exc:
        _load_error = f"ML model unavailable: {exc}"
        logger.exception("Unable to load delay-risk model from %s", MODEL_PATH)
        raise RuntimeError(_load_error) from exc


def risk_category(probability: float) -> str:
    if probability >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    if probability >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


def predict_delay_risk(task: Dict[str, Any]) -> Dict[str, Any]:
    """Return a real model probability; failures are intentionally not masked."""
    features = task_features(task)
    model = load_model()
    if pd is None:  # pragma: no cover - guarded by load_model
        raise RuntimeError("pandas is unavailable")
    probability = float(model.predict_proba(pd.DataFrame([features]))[0][1])
    category = risk_category(probability)
    return {
        "risk_probability": round(max(0.0, min(1.0, probability)), 4),
        "risk_category": category,
        "risk_explanation": (
            f"{category} predicted delay risk from the task's operational and "
            "maintenance-risk characteristics."
        ),
        "model_available": True,
    }


def model_info() -> Dict[str, Any]:
    model = load_model()
    metadata = getattr(model, "gatimaan_metadata", {})
    return {
        "model_type": MODEL_TYPE,
        "training_samples": metadata.get("training_samples", 0),
        "features": FEATURES,
        "evaluation_metrics": metadata.get("evaluation_metrics", {}),
        "synthetic_data_disclaimer": (
            "Training data is synthetic and used only for prototype demonstration. "
            "Production deployment would require historical Indian Railways maintenance, "
            "asset, failure and operational-impact data."
        ),
    }
