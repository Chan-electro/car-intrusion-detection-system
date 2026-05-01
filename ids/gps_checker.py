"""GPS route integrity checker — detects spoofing via Haversine distance."""

from haversine import haversine, Unit


class GpsChecker:
    def __init__(self, golden_route: list[tuple], threshold_m: float = 50.0):
        if not golden_route:
            raise ValueError("golden_route must not be empty")
        self.route        = golden_route
        self.threshold_m  = threshold_m
        self.current_index = 0
        self.locked       = False

    def check(self, lat: float, lon: float) -> dict:
        if self.locked:
            return {"status": "locked", "deviation_m": None}

        expected    = self.route[self.current_index]
        deviation_m = haversine(expected, (lat, lon), unit=Unit.METERS)

        if deviation_m > self.threshold_m:
            self.locked = True
            return {"status": "intrusion", "deviation_m": round(deviation_m, 1)}

        self.current_index = (self.current_index + 1) % len(self.route)
        return {"status": "ok", "deviation_m": round(deviation_m, 1)}
