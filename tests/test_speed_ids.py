import pytest
import numpy as np
from ids.speed_ids import SpeedIDS


def make_normal_window(base=80, n=10):
    return [base + np.random.uniform(-3, 3) for _ in range(n)]


def test_normal_speed_returns_ok():
    ids = SpeedIDS(model_path=None, scaler_path=None, threshold=-999)
    for _ in range(3):
        for pwm in make_normal_window():
            result = ids.update(pwm)
    assert result["status"] == "ok"


def test_speed_spike_returns_intrusion():
    ids = SpeedIDS(model_path=None, scaler_path=None, threshold=-999)
    for pwm in make_normal_window():
        ids.update(pwm)
    for _ in range(3):
        result = ids.update(255)
    assert result["status"] == "intrusion"


def test_correction_value_is_last_safe_pwm():
    ids = SpeedIDS(model_path=None, scaler_path=None, threshold=-999)
    for pwm in make_normal_window(base=80):
        ids.update(pwm)
    for _ in range(3):
        result = ids.update(255)
    assert result["correction_pwm"] == pytest.approx(80, abs=5)


def test_anomaly_counter_resets_on_normal():
    ids = SpeedIDS(model_path=None, scaler_path=None, threshold=-999)
    for pwm in make_normal_window():
        ids.update(pwm)
    ids.update(255)
    for pwm in make_normal_window(base=80):
        ids.update(pwm)
    assert ids.anomaly_counter == 0


def test_suspicious_state_below_threshold():
    ids = SpeedIDS(model_path=None, scaler_path=None, threshold=-999)
    for pwm in make_normal_window():
        ids.update(pwm)
    result = ids.update(255)
    assert result["status"] == "suspicious"
    assert result["correction_pwm"] is None
