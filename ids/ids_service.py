"""Main IDS service — wires GPS, speed, and traffic detection modules."""

import json
import time
import threading
import paho.mqtt.client as mqtt
from ids.gps_checker import GpsChecker
from ids.speed_ids import SpeedIDS
from ids.traffic_ids import TrafficIDS

GOLDEN_ROUTE = [
    (12.9716, 77.5946),
    (12.9720, 77.5950),
    (12.9724, 77.5954),
    (12.9728, 77.5958),
    (12.9732, 77.5962),
]


class IDSService:
    def __init__(self, broker: str = "localhost", port: int = 1883,
                 model_path: str = "models/ids_model.pkl",
                 scaler_path: str = "models/scaler.pkl",
                 threshold_path: str = "models/threshold.txt"):
        self.broker = broker
        self.port   = port

        self.gps_checker = GpsChecker(GOLDEN_ROUTE, threshold_m=50)
        self.traffic_ids = TrafficIDS()

        threshold = self._load_threshold(threshold_path)
        self.speed_ids = SpeedIDS(model_path, scaler_path, threshold=threshold)

        self.ir_state = {"ir_red": False, "mqtt_red": False}
        self.alert_cb = None
        self.client   = None

    def _load_threshold(self, path: str) -> float:
        try:
            with open(path) as f:
                return float(f.read().strip())
        except (FileNotFoundError, ValueError):
            return -0.1

    def set_alert_callback(self, cb):
        self.alert_cb = cb

    def _publish_alert(self, alert: dict):
        alert["timestamp"] = time.time()
        if self.client:
            self.client.publish("ids/alert", json.dumps(alert))
        if self.alert_cb:
            self.alert_cb(alert)
        print(f"[IDS ALERT] {alert}")

    def _publish_heartbeat(self):
        if self.client:
            self.client.publish("ids/heartbeat", json.dumps({"ts": time.time()}))

    def _publish_route(self):
        if self.client:
            waypoints = [{"lat": lat, "lon": lon} for lat, lon in GOLDEN_ROUTE]
            self.client.publish("car/route", json.dumps({"waypoints": waypoints}))
            print("[IDS] Published golden route to car/route")

    def on_message(self, client, userdata, msg):
        topic   = msg.topic
        payload = msg.payload.decode()

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        if topic == "car/speed":
            pwm    = data.get("pwm", 0)
            result = self.speed_ids.update(pwm)
            if result["status"] == "intrusion":
                self._publish_alert({
                    "type":    "speed_intrusion",
                    "pwm":     pwm,
                    "correct": result["correction_pwm"],
                })
                correction = json.dumps({
                    "action": "set_speed",
                    "value":  result["correction_pwm"],
                })
                client.publish("car/command", correction)

        elif topic == "car/gps":
            lat = data.get("lat", 0)
            lon = data.get("lon", 0)
            result = self.gps_checker.check(lat, lon)
            if result["status"] in ("intrusion", "locked"):
                self._publish_alert({
                    "type":        "gps_spoof",
                    "lat":         lat,
                    "lon":         lon,
                    "deviation_m": result["deviation_m"],
                })

        elif topic == "car/ir":
            self.ir_state = {
                "ir_red":   data.get("ir_red", False),
                "mqtt_red": data.get("mqtt_red", False),
            }
            result = self.traffic_ids.check(
                ir_red=self.ir_state["ir_red"],
                mqtt_red=self.ir_state["mqtt_red"],
            )
            if result["status"] == "intrusion":
                self._publish_alert({
                    "type":        "traffic_intrusion",
                    "attack_type": result["attack_type"],
                })

        elif topic in ("hacker/speed", "hacker/gps", "hacker/ir"):
            print(f"[HACKER DETECTED] {topic}: {payload}")
            self._publish_alert({
                "type":    "hacker_activity",
                "topic":   topic,
                "payload": payload,
            })

    def _heartbeat_loop(self):
        while True:
            self._publish_heartbeat()
            time.sleep(2)

    def run(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="ids_service")
        self.client.on_message = self.on_message
        self.client.connect(self.broker, self.port)
        self.client.subscribe([
            ("car/speed", 0), ("car/gps", 0), ("car/ir", 0),
            ("hacker/speed", 0), ("hacker/gps", 0), ("hacker/ir", 0),
        ])

        self._publish_route()

        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()

        print("[IDS] Service running...")
        self.client.loop_forever()


def run():
    service = IDSService()
    service.run()


if __name__ == "__main__":
    run()
