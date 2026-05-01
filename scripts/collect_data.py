"""Collects car/speed MQTT data to CSV for ML training."""

import paho.mqtt.client as mqtt
import csv
import time
import json
import os

BROKER   = "localhost"
TOPIC    = "car/speed"
OUT_FILE = "data/normal_drive.csv"

rows = []
start = time.time()


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return
    rows.append({
        "timestamp": round(time.time() - start, 3),
        "pwm":       payload.get("pwm", 0),
    })


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_message = on_message
    client.connect(BROKER)
    client.subscribe(TOPIC)
    client.loop_start()

    print(f"Collecting speed data from '{TOPIC}'.")
    print("Drive the car normally for 10-15 minutes. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            elapsed = round(time.time() - start)
            print(f"\r  {len(rows)} samples collected ({elapsed}s)", end="", flush=True)
    except KeyboardInterrupt:
        pass

    client.loop_stop()
    client.disconnect()

    os.makedirs("data", exist_ok=True)
    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "pwm"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n\nSaved {len(rows)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()
