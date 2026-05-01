"""Flask dashboard — real-time car IDS monitoring via Socket.IO."""

import threading
import json
import paho.mqtt.client as mqtt
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ids.ids_service import IDSService

app      = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

BROKER = "localhost"

state = {
    "car_status": "SAFE",
    "speed_pwm":  0,
    "traffic":    "GREEN",
    "route_ok":   True,
    "alerts":     [],
}


def on_dashboard_message(client, userdata, msg):
    topic   = msg.topic
    payload = msg.payload.decode()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return

    if topic == "car/speed":
        state["speed_pwm"] = data.get("pwm", 0)
        socketio.emit("speed_update", {"pwm": state["speed_pwm"]})

    elif topic == "car/ir":
        signal = "RED" if (data.get("ir_red") or data.get("mqtt_red")) else "GREEN"
        state["traffic"] = signal
        socketio.emit("traffic_update", {
            "signal": signal,
            "mismatch": data.get("mismatch", False),
        })

    elif topic == "car/gps":
        socketio.emit("gps_update", data)

    elif topic == "ids/alert":
        state["alerts"].insert(0, data)
        state["alerts"] = state["alerts"][:50]
        state["car_status"] = "INTRUSION"
        socketio.emit("alert", data)

    elif topic == "car/status":
        socketio.emit("status_update", data)


def start_mqtt_listener():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="dashboard_listener")
    client.on_message = on_dashboard_message
    client.connect(BROKER)
    client.subscribe([
        ("car/speed", 0), ("car/ir", 0), ("car/gps", 0),
        ("car/status", 0), ("ids/alert", 0),
    ])
    client.loop_forever()


@app.route("/")
def index():
    return render_template("index.html", state=state)


@app.route("/reset", methods=["POST"])
def reset():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return "Forbidden", 403
    state["car_status"] = "SAFE"
    state["alerts"] = []
    state["route_ok"] = True
    socketio.emit("reset", {})
    return "OK"


def start_ids_service():
    service = IDSService(broker=BROKER)
    service.run()


if __name__ == "__main__":
    threading.Thread(target=start_mqtt_listener, daemon=True).start()
    threading.Thread(target=start_ids_service, daemon=True).start()

    print("=" * 50)
    print("  Car IDS Dashboard")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 50)

    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
