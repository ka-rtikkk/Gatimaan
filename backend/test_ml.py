"""Focused tests for the synthetic Random Forest delay-risk prototype."""

import asyncio
import sys

sys.path.insert(0, ".")

from app.api.ml import get_model_info, predict_risk
from app.ml.risk_predictor import model_info, predict_delay_risk, risk_category, task_features
from app.services import priority_engine
from app.services.compatibility_engine import find_compatible_groups
from app.services.optimizer import run_ortools_optimizer


TASK = {
    "task_id": "ML-0001", "department": "Engineering", "asset_type": "Track",
    "asset_name": "Rail Section", "task_type": "Repair", "corridor_id": "DEL-AGR",
    "duration_hours": 2.0, "criticality": 5, "urgency": 5, "safety_risk": 5,
    "asset_importance": 5, "overdue": True, "due_date": None,
    "compatible_departments": ["S&T"],
}


def test_model_training_and_loading():
    info = model_info()
    assert info["model_type"] == "RandomForestClassifier"
    assert info["training_samples"] == 3000
    assert set(info["evaluation_metrics"]) >= {"accuracy", "precision", "recall", "f1", "roc_auc"}


def test_prediction_probability_category_and_invalid_input():
    prediction = predict_delay_risk(TASK)
    assert 0 <= prediction["risk_probability"] <= 1
    assert prediction["risk_category"] == risk_category(prediction["risk_probability"])
    assert task_features({})["duration_hours"] == 1.0


def test_ml_api_contract():
    prediction = asyncio.run(predict_risk(TASK, {}))
    info = asyncio.run(get_model_info({}))
    assert "recommendation" in prediction
    assert info["training_samples"] == 3000


def test_priority_ml_integration_and_optimizer():
    scored = priority_engine.calculate_priority_score(TASK)
    assert scored["existing_priority_score"] == scored["priority_score"]
    assert scored["ml_risk_probability"] is not None
    assert scored["final_planning_score"] == round(
        0.60 * scored["existing_priority_score"] + 0.40 * scored["ml_risk_probability"], 4
    )
    groups = find_compatible_groups([scored])
    assert groups[0]["max_planning_score"] == scored["final_planning_score"]
    from datetime import date
    windows = [{"corridor_id": "DEL-AGR", "date": date.today().isoformat(), "start_time": "12:00:00", "end_time": "15:00:00", "available": True, "maximum_duration": 3.0}]
    blocks, _ = run_ortools_optimizer(groups, windows, [], "today")
    assert blocks and blocks[0]["optimization_score"] >= scored["final_planning_score"] * 100 - 0.1


def test_ml_fallback_keeps_existing_priority(monkeypatch):
    monkeypatch.setattr(priority_engine, "predict_delay_risk", lambda task: (_ for _ in ()).throw(RuntimeError("missing model")))
    scored = priority_engine.calculate_priority_score(TASK)
    assert scored["ml_risk_probability"] is None
    assert scored["final_planning_score"] == scored["priority_score"]
    assert scored["ml_model_available"] is False


if __name__ == "__main__":
    test_model_training_and_loading()
    test_prediction_probability_category_and_invalid_input()
    test_ml_api_contract()
    test_priority_ml_integration_and_optimizer()
    class Patch:
        def setattr(self, target, name, value):
            original = getattr(target, name)
            setattr(target, name, value)
            self.original = (target, name, original)
        def undo(self):
            target, name, original = self.original
            setattr(target, name, original)
    patch = Patch()
    original_predictor = priority_engine.predict_delay_risk
    priority_engine.predict_delay_risk = lambda task: (_ for _ in ()).throw(RuntimeError("missing model"))
    test_ml_fallback_keeps_existing_priority(patch)
    priority_engine.predict_delay_risk = original_predictor
    print("ML tests passed")