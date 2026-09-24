from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.network.telemetry import FEATURES


def train(dataset: Path | None = None, model_dir: Path | None = None) -> dict:
    dataset = dataset or ROOT / "data" / "network_telemetry.csv"
    model_dir = model_dir or ROOT / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(dataset).dropna(subset=FEATURES + ["failure_type"])
    x = frame[FEATURES].clip(lower=0)
    y = frame["failure_type"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.22, random_state=42, stratify=y
    )

    classifier = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestClassifier(n_estimators=180, max_depth=16, class_weight="balanced", random_state=42, n_jobs=-1)),
    ])
    classifier.fit(x_train, y_train)
    predictions = classifier.predict(x_test)

    normal_train = x_train[y_train == "normal"]
    anomaly = Pipeline([
        ("scaler", StandardScaler()),
        ("model", IsolationForest(n_estimators=160, contamination=0.08, random_state=42, n_jobs=-1)),
    ])
    anomaly.fit(normal_train)

    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    metrics = {
        "accuracy": round(accuracy_score(y_test, predictions), 4),
        "macro_f1": round(f1_score(y_test, predictions, average="macro"), 4),
        "classes": list(classifier.classes_),
        "classification_report": report,
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=classifier.classes_).tolist(),
        "training_samples": int(len(x_train)), "test_samples": int(len(x_test)),
        "features": FEATURES,
    }
    joblib.dump(classifier, model_dir / "failure_classifier.joblib")
    joblib.dump(anomaly, model_dir / "anomaly_detector.joblib")
    (model_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({"accuracy": metrics["accuracy"], "macro_f1": metrics["macro_f1"]}, indent=2))
    return metrics


if __name__ == "__main__":
    train()

