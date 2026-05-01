"""Trains Isolation Forest on collected normal drive data."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from ids.features import extract_features

DATA_FILE = "data/normal_drive.csv"
MODEL_DIR = "models"
WINDOW    = 5    # 5 readings at 200ms = 1 second window


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        print(f"ERROR: {DATA_FILE} not found.")
        print("Run collect_data.py first to gather training data.")
        sys.exit(1)

    df = pd.read_csv(DATA_FILE)
    pwm = df["pwm"].values
    print(f"Loaded {len(pwm)} readings from {DATA_FILE}")

    if len(pwm) < WINDOW + 1:
        print(f"ERROR: Need at least {WINDOW + 1} readings. Got {len(pwm)}.")
        sys.exit(1)

    X = [extract_features(pwm[i:i + WINDOW].tolist())
         for i in range(len(pwm) - WINDOW)]
    X = np.array(X)
    print(f"Extracted {len(X)} feature windows")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X_scaled)

    scores = model.decision_function(X_scaled)
    threshold = float(np.percentile(scores, 5))
    print(f"Threshold (5th percentile): {threshold:.4f}")

    joblib.dump(model, f"{MODEL_DIR}/ids_model.pkl")
    joblib.dump(scaler, f"{MODEL_DIR}/scaler.pkl")
    with open(f"{MODEL_DIR}/threshold.txt", "w") as f:
        f.write(str(threshold))

    print(f"\nModel saved to {MODEL_DIR}/")
    print(f"  ids_model.pkl  — Isolation Forest ({len(X)} training windows)")
    print(f"  scaler.pkl     — StandardScaler")
    print(f"  threshold.txt  — {threshold:.4f}")


if __name__ == "__main__":
    main()
