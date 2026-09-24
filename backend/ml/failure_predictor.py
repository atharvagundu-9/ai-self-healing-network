from __future__ import annotations

from collections import defaultdict, deque

import joblib
import numpy as np
import pandas as pd

from backend.config import MODEL_DIR
from backend.network.telemetry import FEATURES


class FailurePredictor:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_DIR / "failure_classifier.joblib")
        self.history: dict[str, deque] = defaultdict(lambda: deque(maxlen=6))

    def predict(self, telemetry: dict) -> dict:
        frame = pd.DataFrame([[telemetry[name] for name in FEATURES]], columns=FEATURES)
        probabilities = self.model.predict_proba(frame)[0]
        best = int(np.argmax(probabilities))
        distribution = {name: round(float(probabilities[index]), 4) for index, name in enumerate(self.model.classes_)}
        return {
            "predicted_failure": str(self.model.classes_[best]),
            "confidence": round(float(probabilities[best]), 4),
            "probabilities": distribution,
        }

    def failure_risk(self, telemetry: dict) -> dict:
        history = self.history[telemetry["device_id"]]
        history.append(telemetry)
        if len(history) < 4:
            return {"level": "LOW", "score": 0.1, "message": "Collecting a longer telemetry window."}
        latency = np.array([row["latency_ms"] for row in history], dtype=float)
        loss = np.array([row["packet_loss_percent"] for row in history], dtype=float)
        utilization = np.array([row["bandwidth_utilization"] for row in history], dtype=float)
        slope = lambda values: float(np.polyfit(np.arange(len(values)), values, 1)[0])
        risk = min(1.0, max(0.0, slope(latency) / 35 + slope(loss) / 8 + slope(utilization) / 24))
        level = "CRITICAL" if risk >= 0.8 else "HIGH" if risk >= 0.55 else "MEDIUM" if risk >= 0.3 else "LOW"
        if risk >= 0.55:
            message = "Metrics are deteriorating; congestion may develop within the next monitoring window."
        elif risk >= 0.3:
            message = "A worsening trend is developing; continue close observation."
        else:
            message = "Recent metrics are stable."
        return {"level": level, "score": round(risk, 3), "message": message}
