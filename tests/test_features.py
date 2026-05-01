from ids.features import extract_features


def test_constant_window_has_zero_variation():
    features = extract_features([80.0, 80.0, 80.0, 80.0, 80.0])
    mean_pwm, std_pwm, max_delta, accel_rate, window_range = features
    assert mean_pwm == 80.0
    assert std_pwm == 0.0
    assert max_delta == 0.0
    assert accel_rate == 0.0
    assert window_range == 0.0


def test_known_input_produces_expected_features():
    features = extract_features([60.0, 80.0, 100.0, 80.0, 60.0])
    mean_pwm, std_pwm, max_delta, accel_rate, window_range = features
    assert mean_pwm == 76.0
    assert max_delta == 20.0
    assert accel_rate == 20.0
    assert window_range == 40.0
    assert std_pwm > 0


def test_single_value_window():
    features = extract_features([100.0])
    mean_pwm, std_pwm, max_delta, accel_rate, window_range = features
    assert mean_pwm == 100.0
    assert std_pwm == 0.0
    assert max_delta == 0.0
    assert accel_rate == 0.0
    assert window_range == 0.0
