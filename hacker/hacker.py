"""Hacker simulation CLI — demonstrates all 3 attack scenarios."""

import paho.mqtt.client as mqtt
import json
import time

BROKER = "localhost"
PORT   = 1883


def attack_speed(client, pwm: int = 255, count: int = 15):
    print(f"\n[ATTACK] Speed spike PWM={pwm} x{count}")
    for i in range(count):
        client.publish("hacker/speed", json.dumps({"pwm": pwm}))
        client.publish("car/speed", json.dumps({"pwm": pwm}))
        time.sleep(0.2)
        print(f"  Injected {i+1}/{count}", end="\r")
    print(f"\n[ATTACK] Speed attack complete")


def attack_gps(client, lat: float = 0.0, lon: float = 0.0):
    print(f"\n[ATTACK] GPS spoof -> ({lat}, {lon})")
    for i in range(3):
        client.publish("hacker/gps", json.dumps({"lat": lat, "lon": lon}))
        client.publish("car/gps", json.dumps({"lat": lat, "lon": lon, "idx": 0}))
        time.sleep(1)
        print(f"  Sent {i+1}/3")
    print("[ATTACK] GPS attack complete")


def attack_ir(client):
    print("\n[ATTACK] IR override attempt — publishing hacker/ir GREEN")
    for i in range(5):
        client.publish("hacker/ir", json.dumps({"signal": "GREEN", "override": True}))
        time.sleep(0.5)
        print(f"  Sent {i+1}/5")
    print("[ATTACK] IR attack complete (detected as mismatch if physical IR is RED)")


MENU = """
=============================================
     HACKER SIMULATION CLI
=============================================
  [1] Speed spike attack   (Isolation Forest)
  [2] GPS spoof attack     (Golden Route)
  [3] IR override attempt  (Dual-Verify)
  [4] All attacks (demo mode)
  [q] Quit
=============================================
"""


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="hacker_cli")
    try:
        client.connect(BROKER, PORT)
    except ConnectionRefusedError:
        print("ERROR: Cannot connect to MQTT broker at localhost:1883")
        print("Make sure Mosquitto is running.")
        return

    client.loop_start()
    print(MENU)

    while True:
        choice = input("Select attack > ").strip()
        if choice == "1":
            attack_speed(client)
        elif choice == "2":
            attack_gps(client)
        elif choice == "3":
            attack_ir(client)
        elif choice == "4":
            print("\n[DEMO] Running all attacks with 3s gaps...\n")
            attack_ir(client)
            time.sleep(3)
            attack_speed(client)
            time.sleep(3)
            attack_gps(client)
            print("\n[DEMO] All attacks complete.\n")
        elif choice == "q":
            break
        else:
            print("Invalid choice. Enter 1-4 or q.")

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
