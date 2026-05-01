# Car IDS — Resume Session

## Status
Design + implementation plan complete. Ready to build.

## Next Step
Invoke `superpowers:subagent-driven-development` skill with the plan below.

Tell Claude:
> "Resume the Car IDS project. Use superpowers:subagent-driven-development to execute the plan at `docs/superpowers/plans/2026-04-27-car-ids.md` task by task, starting from Task 1."

---

## Key Files

| File | Purpose |
|---|---|
| `docs/superpowers/specs/2026-04-27-car-ids-design.md` | Full system design spec |
| `2026-04-27-car-ids-design.md` | Same spec (copy at project root) |
| `docs/superpowers/plans/2026-04-27-car-ids.md` | Implementation plan (16 tasks) |

---

## Before Starting — Do These First

1. **Find laptop WiFi IP** — `ipconfig getifaddr en0` (mac) or `hostname -I` (linux)
2. **Replace `192.168.1.X`** in both firmware sketches with that IP
3. **Replace `YOUR_SSID` / `YOUR_PASSWORD`** in both firmware sketches
4. **Install Arduino libraries** via Library Manager:
   - `PubSubClient` by Nick O'Leary
   - `NewPing` by Tim Eckel
   - `IRremote` by Armin Joachimsmeyer (v4.x)
5. **Board setting**: ESP32 Dev Module, upload speed 115200

---

## System Summary

**3 entities:** ESP32 Car + Python Hacker CLI + Laptop (Mosquitto + IDS + Flask dashboard)

**3 attack scenarios:**
1. Traffic signal — dual-verify IR + MQTT, hardware interrupt defense
2. Speed injection — Isolation Forest ML on rolling 1s window
3. GPS spoofing — Haversine distance check vs golden route every 5s

**Communication:** WiFi + MQTT (Mosquitto on laptop, port 1883)

**ML:** Isolation Forest trained on 15 min normal drive data (Day 1 collection → Day 2 train)

---

## Hardware Available
- ESP32, IR sensor, DC motors x2, L298N motor driver, buck converter, HC-SR04

## Hardware to Buy
- IR LED + resistor (traffic signal emitter)
- Rotary encoder LM393 (speed sensing)
- 2WD chassis kit
- 7.4V LiPo / 9V battery
- OLED SSD1306 I2C (optional, great for demo)

---

## 3-Day Target
- Day 1: Hardware + firmware + data collection
- Day 2: IDS + ML + dashboard
- Day 3: Polish + hacker CLI + demo rehearsal
