"""Integration tests for IDSService — uses mock MQTT client."""

import json
from unittest.mock import MagicMock, patch
from ids.ids_service import IDSService


def make_msg(topic: str, payload: dict):
    msg = MagicMock()
    msg.topic = topic
    msg.payload = json.dumps(payload).encode()
    return msg


def make_service():
    service = IDSService(
        broker="localhost",
        model_path="nonexistent.pkl",
        scaler_path="nonexistent.pkl",
        threshold_path="nonexistent.txt",
    )
    service.client = MagicMock()
    return service


def test_speed_intrusion_publishes_alert_and_correction():
    service = make_service()
    alerts = []
    service.set_alert_callback(lambda a: alerts.append(a))

    for _ in range(5):
        msg = make_msg("car/speed", {"pwm": 80})
        service.on_message(service.client, None, msg)

    for _ in range(5):
        msg = make_msg("car/speed", {"pwm": 255})
        service.on_message(service.client, None, msg)

    speed_alerts = [a for a in alerts if a["type"] == "speed_intrusion"]
    assert len(speed_alerts) > 0
    assert speed_alerts[0]["correct"] is not None

    service.client.publish.assert_any_call(
        "ids/alert", json.dumps(speed_alerts[0])
    )


def test_gps_spoof_publishes_alert():
    service = make_service()
    alerts = []
    service.set_alert_callback(lambda a: alerts.append(a))

    msg = make_msg("car/gps", {"lat": 0.0, "lon": 0.0, "idx": 0})
    service.on_message(service.client, None, msg)

    gps_alerts = [a for a in alerts if a["type"] == "gps_spoof"]
    assert len(gps_alerts) == 1
    assert gps_alerts[0]["deviation_m"] > 50


def test_traffic_mismatch_publishes_alert():
    service = make_service()
    alerts = []
    service.set_alert_callback(lambda a: alerts.append(a))

    msg = make_msg("car/ir", {"ir_red": False, "mqtt_red": True, "mismatch": True})
    service.on_message(service.client, None, msg)

    traffic_alerts = [a for a in alerts if a["type"] == "traffic_intrusion"]
    assert len(traffic_alerts) == 1
    assert traffic_alerts[0]["attack_type"] == "ir_spoof"


def test_malformed_json_does_not_crash():
    service = make_service()
    msg = MagicMock()
    msg.topic = "car/speed"
    msg.payload = b"not valid json {{"

    service.on_message(service.client, None, msg)
