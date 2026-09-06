"""Generate synthetic task history and train the prototype delay-risk model."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.ml.risk_predictor import FEATURES

SEED = 42
RECORD_COUNT = 3000
ROOT = Path(__file__).parent


def build_training_data(count: int = RECORD_COUNT) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    departments = np.array(["Engineering", "S&T", "Traction Distribution"])
    assets = np.array(["Track", "Signal", "OHE", "Point Machine", "Bridge"])
    task_types = np.array(["Inspection", "Repair", "Replacement", "Overhaul", "Testing"])
    corridors = np.array(["DEL-AGR", "MUM-PUN", "HWH-KOL", "BPL-NGP", "MAS-BLR"])
    frame = pd.DataFrame({
        "criticality": rng.integers(1, 6, count),
        "urgency": rng.integers(1, 6, count),
        "safety_risk": rng.integers(1, 6, count),
        "asset_importance": rng.integers(1, 6, count),
        "overdue": rng.random(count) < 0.22,
        "duration_hours": np.round(rng.uniform(0.5, 6.0, count), 2),
        "days_until_due": rng.integers(-14, 61, count),
        "department": rng.choice(departments, count),
        "asset_type": rng.choice(assets, count),
        "task_type": rng.choice(task_types, count),
        "corridor_id": rng.choice(corridors, count),
    })
    latent = (
        0.55 * frame.criticality + 0.42 * frame.safety_risk
        + 0.30 * frame.asset_importance + 0.24 * frame.urgency
        + 0.16 * frame.duration_hours + 1.15 * frame.overdue.astype(float)
        + 0.65 * (frame.days_until_due <= 3)
        + 0.35 * ((frame.criticality >= 4) & (frame.safety_risk >= 4))
        + 0.25 * ((frame.asset_type == "Bridge") | (frame.task_type == "Replacement"))
        + rng.normal(0, 1.8, count)
    )
    threshold = float(np.quantile(latent, 0.58))
    frame["high_delay_risk"] = (latent > threshold).astype(int)
    return frame


def train_and_save() -> dict:
    frame = build_training_data()
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURES], frame["high_delay_risk"], test_size=0.2,
        random_state=SEED, stratify=frame["high_delay_risk"],
    )
    categorical = ["department", "asset_type", "task_type", "corridor_id"]
    numeric = [feature for feature in FEATURES if feature not in categorical]
    pipeline = Pipeline([
        ("features", ColumnTransformer([
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("numeric", "passthrough", numeric),
        ])),
        ("classifier", RandomForestClassifier(
            n_estimators=200, max_depth=8, random_state=SEED, class_weight="balanced", n_jobs=-1,
        )),
    ])
    pipeline.fit(x_train, y_train)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "precision": round(precision_score(y_test, predictions, zero_division=0), 4),
        "recall": round(recall_score(y_test, predictions, zero_division=0), 4),
        "f1": round(f1_score(y_test, predictions, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, probabilities), 4),
    }
    metadata = {"training_samples": len(frame), "evaluation_metrics": metrics, "seed": SEED}
    pipeline.gatimaan_metadata = metadata
    frame.to_csv(ROOT / "training_data.csv", index=False)
    joblib.dump(pipeline, ROOT / "model.joblib")
    (ROOT / "model_metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    print(json.dumps(train_and_save(), indent=2))
