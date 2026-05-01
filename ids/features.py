"""Shared feature extraction for speed IDS — used by both training and inference."""

import numpy as np


def extract_features(window: list[float]) -> list[float]:
    """Extract 5 statistical features from a speed reading window.

    Args:
        window: List of PWM values (e.g., 10 readings = 1 window)

    Returns:
        [mean_pwm, std_pwm, max_delta_pwm, accel_rate, window_range]
    """
    w = np.array(window, dtype=float)
    deltas = np.abs(np.diff(w))
    return [
        float(np.mean(w)),
        float(np.std(w)),
        float(np.max(deltas)) if len(deltas) > 0 else 0.0,
        float(np.mean(deltas)) if len(deltas) > 0 else 0.0,
        float(np.max(w) - np.min(w)),
    ]
