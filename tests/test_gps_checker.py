import pytest
from ids.gps_checker import GpsChecker

GOLDEN_ROUTE = [
    (12.9716, 77.5946),
    (12.9720, 77.5950),
    (12.9724, 77.5954),
    (12.9728, 77.5958),
    (12.9732, 77.5962),
]


def test_on_route_returns_ok():
    checker = GpsChecker(GOLDEN_ROUTE, threshold_m=50)
    result = checker.check(12.9716, 77.5946)
    assert result["status"] == "ok"
    assert result["deviation_m"] < 1


def test_large_deviation_returns_intrusion():
    checker = GpsChecker(GOLDEN_ROUTE, threshold_m=50)
    result = checker.check(0.0, 0.0)
    assert result["status"] == "intrusion"
    assert result["deviation_m"] > 50


def test_route_locks_after_intrusion():
    checker = GpsChecker(GOLDEN_ROUTE, threshold_m=50)
    checker.check(0.0, 0.0)
    assert checker.locked is True


def test_locked_checker_always_returns_locked():
    checker = GpsChecker(GOLDEN_ROUTE, threshold_m=50)
    checker.check(0.0, 0.0)
    result = checker.check(12.9716, 77.5946)
    assert result["status"] == "locked"


def test_waypoint_advances_on_ok_check():
    checker = GpsChecker(GOLDEN_ROUTE, threshold_m=50)
    assert checker.current_index == 0
    checker.check(12.9716, 77.5946)
    assert checker.current_index == 1


def test_empty_route_raises_error():
    with pytest.raises(ValueError, match="must not be empty"):
        GpsChecker([], threshold_m=50)
