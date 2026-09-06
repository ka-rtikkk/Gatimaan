"""
=============================================================================
GATIMAAN PRIORITY ENGINE
=============================================================================
Implements an explainable weighted priority scoring system for maintenance tasks.

Formula:
    priority_score =
        0.30 * criticality_normalized
      + 0.25 * urgency_normalized
      + 0.20 * safety_risk_normalized
      + 0.15 * asset_importance_normalized
      + 0.10 * overdue_factor

Normalized inputs are in [0, 1].
Overdue tasks receive a bonus to push them higher in the schedule.

Classification:
    0.80 - 1.00 → CRITICAL
    0.60 - 0.79 → HIGH
    0.40 - 0.59 → MEDIUM
    below 0.40  → LOW

This module is designed so the scoring function can be replaced by an
ML model (e.g., a trained Random Forest or XGBoost regressor) in the future.
The interface remains the same: input task dict → output scored task dict.
=============================================================================
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
import math
import logging

from app.ml.risk_predictor import predict_delay_risk

logger = logging.getLogger(__name__)


# Scoring weights (must sum to 1.0)
WEIGHTS = {
    "criticality": 0.30,
    "urgency": 0.25,
    "safety_risk": 0.20,
    "asset_importance": 0.15,
    "overdue_factor": 0.10,
}

ML_PRIORITY_WEIGHT = 0.60
ML_RISK_WEIGHT = 0.40

# Classification thresholds
PRIORITY_THRESHOLDS = {
    "CRITICAL": 0.80,
    "HIGH": 0.60,
    "MEDIUM": 0.40,
    "LOW": 0.0,
}

# Max values for normalization (all fields 1-5)
FIELD_MAX = 5.0
FIELD_MIN = 1.0


def normalize_field(value: int, min_val: float = FIELD_MIN, max_val: float = FIELD_MAX) -> float:
    """Normalize a 1-5 integer field to [0, 1]"""
    return (value - min_val) / (max_val - min_val)


def compute_overdue_factor(due_date_str: Optional[str], overdue: bool) -> float:
    """
    Compute overdue factor in [0, 1].
    - Overdue tasks get 1.0
    - Due in 1 day: 0.9
    - Due in 3 days: 0.7
    - Due in 7 days: 0.5
    - Due in > 14 days: 0.1
    """
    if overdue:
        return 1.0

    if not due_date_str:
        return 0.2

    try:
        if isinstance(due_date_str, str):
            due = datetime.fromisoformat(due_date_str).date()
        elif isinstance(due_date_str, date):
            due = due_date_str
        else:
            return 0.2

        today = date.today()
        days_until_due = (due - today).days

        if days_until_due < 0:
            return 1.0  # Overdue
        elif days_until_due == 0:
            return 0.95  # Due today
        elif days_until_due <= 1:
            return 0.90
        elif days_until_due <= 3:
            return 0.75
        elif days_until_due <= 7:
            return 0.55
        elif days_until_due <= 14:
            return 0.35
        else:
            return 0.15

    except (ValueError, AttributeError):
        return 0.2


def calculate_priority_score(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate priority score and category for a single maintenance task.

    Args:
        task: Dictionary with keys: criticality, urgency, safety_risk,
              asset_importance, due_date, overdue

    Returns:
        Dict with added fields:
            priority_score: float [0, 1]
            priority_category: str (CRITICAL/HIGH/MEDIUM/LOW)
            score_breakdown: dict of individual factor contributions
            explanation: str human-readable explanation
    """
    # Normalize each component
    crit_norm = normalize_field(task.get("criticality", 3))
    urg_norm = normalize_field(task.get("urgency", 3))
    safety_norm = normalize_field(task.get("safety_risk", 3))
    asset_norm = normalize_field(task.get("asset_importance", 3))
    overdue_factor = compute_overdue_factor(
        task.get("due_date"), task.get("overdue", False)
    )

    # Weighted sum
    score = (
        WEIGHTS["criticality"] * crit_norm
        + WEIGHTS["urgency"] * urg_norm
        + WEIGHTS["safety_risk"] * safety_norm
        + WEIGHTS["asset_importance"] * asset_norm
        + WEIGHTS["overdue_factor"] * overdue_factor
    )

    score = round(min(1.0, max(0.0, score)), 4)

    # Classify
    if score >= PRIORITY_THRESHOLDS["CRITICAL"]:
        category = "CRITICAL"
    elif score >= PRIORITY_THRESHOLDS["HIGH"]:
        category = "HIGH"
    elif score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        category = "MEDIUM"
    else:
        category = "LOW"

    # Score breakdown (contribution of each factor)
    breakdown = {
        "criticality_contribution": round(WEIGHTS["criticality"] * crit_norm, 4),
        "urgency_contribution": round(WEIGHTS["urgency"] * urg_norm, 4),
        "safety_risk_contribution": round(WEIGHTS["safety_risk"] * safety_norm, 4),
        "asset_importance_contribution": round(WEIGHTS["asset_importance"] * asset_norm, 4),
        "overdue_contribution": round(WEIGHTS["overdue_factor"] * overdue_factor, 4),
        "criticality_normalized": round(crit_norm, 4),
        "urgency_normalized": round(urg_norm, 4),
        "safety_risk_normalized": round(safety_norm, 4),
        "asset_importance_normalized": round(asset_norm, 4),
        "overdue_factor": round(overdue_factor, 4),
    }

    # Generate human-readable explanation
    explanation = _generate_priority_explanation(task, score, category, breakdown)

    ml_fields = {
        "existing_priority_score": score,
        "ml_risk_probability": None,
        "ml_risk_category": None,
        "ml_risk_explanation": None,
        "ml_model_available": False,
        "final_planning_score": score,
    }
    try:
        prediction = predict_delay_risk(task)
        ml_probability = prediction["risk_probability"]
        ml_fields.update({
            "ml_risk_probability": ml_probability,
            "ml_risk_category": prediction["risk_category"],
            "ml_risk_explanation": prediction["risk_explanation"],
            "ml_model_available": True,
            "final_planning_score": round(
                ML_PRIORITY_WEIGHT * score + ML_RISK_WEIGHT * ml_probability, 4
            ),
        })
    except Exception as exc:
        logger.warning("ML risk unavailable for task %s; using weighted priority only: %s", task.get("task_id"), exc)

    return {
        **task,
        "priority_score": score,
        "priority_category": category,
        "score_breakdown": breakdown,
        "priority_explanation": explanation,
        **ml_fields,
    }


def _generate_priority_explanation(
    task: Dict, score: float, category: str, breakdown: Dict
) -> str:
    """Generate a human-readable explanation for the priority score"""
    reasons = []

    # Criticality
    crit = task.get("criticality", 3)
    if crit == 5:
        reasons.append("maximum criticality (asset failure imminent)")
    elif crit >= 4:
        reasons.append("high criticality asset condition")

    # Safety risk
    safety = task.get("safety_risk", 3)
    if safety == 5:
        reasons.append("severe safety risk to train operations")
    elif safety >= 4:
        reasons.append("high safety risk")

    # Urgency
    urgency = task.get("urgency", 3)
    if urgency >= 4:
        reasons.append("urgent attention required")

    # Overdue
    if task.get("overdue"):
        reasons.append("task is OVERDUE and past due date")
    elif breakdown.get("overdue_factor", 0) >= 0.7:
        reasons.append("due date is imminent")

    # Asset importance
    ai = task.get("asset_importance", 3)
    if ai >= 4:
        reasons.append("critical asset importance to railway operations")

    if not reasons:
        reasons.append("standard maintenance requirements")

    reason_text = "; ".join(reasons[:3])
    return f"{category} priority (score: {score:.2f}) — {reason_text.capitalize()}."


def calculate_priorities_bulk(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate priority scores for a list of tasks.
    Returns tasks sorted by priority score (highest first).

    This function provides a stable interface for future ML model replacement.
    To use an ML model:
        1. Train a model on historical task/priority data
        2. Replace the score calculation in calculate_priority_score()
           with model.predict(feature_vector)
        3. Keep the same input/output interface
    """
    scored = [calculate_priority_score(task) for task in tasks]
    scored.sort(key=lambda t: t.get("final_planning_score", t["priority_score"]), reverse=True)
    return scored


def get_priority_distribution(tasks: List[Dict]) -> Dict[str, int]:
    """Get count of tasks in each priority category"""
    dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for task in tasks:
        cat = task.get("priority_category", "LOW")
        if cat in dist:
            dist[cat] += 1
    return dist
