from __future__ import annotations

import joblib
import pandas as pd

from backend.config import MODEL_DIR
from backend.network.telemetry import FEATURES


class AnomalyDetector:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_DIR / "anomaly_detector.joblib")

    def predict(self, telemetry: dict) -> dict:
        frame = pd.DataFrame([[telemetry[name] for name in FEATURES]], columns=FEATURES)
        raw_score = float(self.model.decision_function(frame)[0])
        anomalous = bool(self.model.predict(frame)[0] == -1)
        # Map the unbounded decision score into a presentation-friendly risk signal.
        score = max(0.0, min(1.0, 0.5 - raw_score * 3.0))
        return {"is_anomaly": anomalous, "anomaly_score": round(score, 4), "raw_score": round(raw_score, 4)}

