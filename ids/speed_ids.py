"""Speed anomaly detection using Isolation Forest with Z-score fallback."""

import numpy as np
from collections import deque
import joblib
import os
from ids.features import extract_features

WINDOW_SIZE = 5  # 5 readings at 200ms = 1 second


class SpeedIDS:
    def __init__(self, model_path: str | None, scaler_path: str | None,
                 threshold: float = -0.1):
        self.window          = deque(maxlen=WINDOW_SIZE)
        self.last_safe_pwm   = 80
        self.anomaly_counter = 0
        self.threshold       = threshold

        self.model  = None
        self.scaler = None

        if model_path and os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"[SpeedIDS] Failed to load model: {e} — using Z-score fallback")

        if scaler_path and os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
            except Exception as e:
                print(f"[SpeedIDS] Failed to load scaler: {e} — using Z-score fallback")

    def _is_anomaly(self, features: list[float]) -> bool:
        if self.model is None:
            return features[2] > 80  # max_delta_pwm > 80 = anomaly

        X = np.array([features])
        if self.scaler:
            X = self.scaler.transform(X)
        score = self.model.decision_function(X)[0]
        return score < self.threshold

    def update(self, pwm: float) -> dict:
        self.window.append(pwm)

        if len(self.window) < WINDOW_SIZE:
            return {"status": "collecting", "correction_pwm": None}

        features = extract_features(list(self.window))

        if self._is_anomaly(features):
            self.anomaly_counter += 1
            if self.anomaly_counter >= 3:
                return {"status": "intrusion", "correction_pwm": self.last_safe_pwm}
            return {"status": "suspicious", "correction_pwm": None}
        else:
            self.anomaly_counter = 0
            if 20 < pwm < 240:
                self.last_safe_pwm = int(pwm)
            return {"status": "ok", "correction_pwm": None}
