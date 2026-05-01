# Intrusion Detection System — Automated Car (AI + IoT)

**Date:** 2026-04-27  
**Timeline:** 3 days  
**Status:** Approved

---

## 1. Problem Statement

An automated car (ESP32-based prototype) must defend against three classes of network intrusion:
1. A hacker manipulating the traffic signal response
2. A hacker injecting abnormal speed commands
3. A hacker spoofing GPS coordinates to alter the car's route

The system must detect each attack in real time, correct the car's behavior, and surface alerts on a monitoring dashboard — while remaining buildable in 3 days with available hardware.

---

## 2. System Entities

| Entity | Role | Hardware |
|---|---|---|
| User Car | Autonomous/manual prototype | ESP32 + sensors |
| Hacker | Attacker injecting malicious MQTT payloads | Python script on laptop |
| Monitoring Platform | Broker + IDS + dashboard | Laptop (Mosquitto + Python + Flask) |

---

## 3. Architecture

### Communication Stack
- **Protocol:** MQTT over WiFi (Mosquitto broker on laptop, port 1883)
- **Car → Platform:** publishes sensor data
- **Platform → Car:** publishes corrections via `car/command`
- **Hacker → Broker:** publishes malicious payloads to `hacker/*` topics

### MQTT Topic Map

| Topic | Publisher | Subscriber | Purpose |
|---|---|---|---|
| `car/speed` | ESP32 | IDS service | Real-time PWM speed value |
| `car/gps` | ESP32 | IDS service | Simulated lat/lon every 5s |
| `car/ir` | ESP32 | Dashboard | IR + MQTT signal agreement state |
| `car/status` | ESP32 | Dashboard | General health heartbeat |
| `traffic/signal` | Traffic controller ESP32 | ESP32 car, IDS | Authoritative RED/GREEN over MQTT |
| `hacker/speed` | Hacker | IDS (monitored) | Injected speed attack payload |
| `hacker/gps` | Hacker | IDS (monitored) | Injected GPS spoof payload |
| `hacker/ir` | Hacker | IDS (monitored) | Attempted IR signal override (detected via mismatch) |
| `ids/alert` | IDS service | Dashboard | Intrusion events |
| `car/command` | IDS service | ESP32 | Speed correction commands |

---

## 4. Hardware

### Components: Have
- ESP32 (x1 minimum, x2 recommended — one for car, one for traffic signal)
- IR Receiver (TSOP1738 or equivalent)
- DC Motors x2
- L298N Motor Driver
- Buck Converter
- HC-SR04 Ultrasonic Sensor

### Components: Buy
| Component | Purpose | Priority |
|---|---|---|
| IR LED + resistor | Traffic signal emitter | Required |
| Rotary encoder (LM393) | Accurate speed measurement | Recommended |
| 2WD car chassis kit | Physical car frame | Required |
| 7.4V LiPo or 9V battery | Power source | Required |
| 0.96" OLED (SSD1306, I2C) | Show SAFE/INTRUSION on car | Optional (demo impact) |

### ESP32 Pin Map

```
GPIO 13  → IR Receiver OUT
GPIO 14  → HC-SR04 TRIG
GPIO 15  → HC-SR04 ECHO
GPIO 26  → L298N IN1
GPIO 27  → L298N IN2
GPIO 32  → L298N IN3
GPIO 33  → L298N IN4
GPIO 25  → L298N ENA (PWM)
GPIO 18  → L298N ENB (PWM)
GPIO 34  → Encoder A
GPIO 35  → Encoder B
```

### Power Rail
```
Battery (7.4V/9V) → Buck Converter → 5V rail → L298N logic + ESP32
                                   → Motor VCC direct from battery
```

---

## 5. Security Scenarios

### 5.1 Traffic Signal — Dual-Verification Lock

**Attack:** Hacker emits physical IR GREEN signal or publishes `hacker/ir = GREEN` to bypass red light.

**Defense:**
- Traffic controller (second ESP32 **or** Python script on laptop) publishes `traffic/signal = RED` to MQTT (authoritative source)
- Traffic controller also emits IR simultaneously via IR LED circuit
- ESP32 car firmware requires **both** to agree on GREEN before motors run
- Hardware interrupt (`attachInterrupt`) on IR receiver pin — cannot be overridden by software
- If IR says GREEN but `traffic/signal` says RED → mismatch → intrusion alert published to `ids/alert`
- Hacker must compromise both channels simultaneously to succeed

**Why it works:** Physical IR and MQTT are independent channels. A hacker with an IR blaster cannot also forge signed MQTT traffic signal messages without broker credentials.

---

### 5.2 Speed Intrusion — Isolation Forest ML

**Attack:** Hacker publishes `hacker/speed = 255` (full throttle) to accelerate car dangerously.

**Defense:**
- ESP32 publishes current PWM duty cycle to `car/speed` every 100ms
- Python IDS maintains a rolling 10-reading window (1 second)
- Features: `mean_pwm`, `std_pwm`, `max_delta_pwm`, `accel_rate`, `window_range`
- Isolation Forest model (trained offline on 15 min normal drive data) scores each window
- Score below threshold → anomaly → publish alert to `ids/alert` + restore `last_safe_speed` via `car/command`
- ESP32 subscribes to `car/command` and applies correction immediately
- False-positive guard: require 3 consecutive anomaly detections before triggering

**Model training:**
```
Data:       15 min normal drive → ~9000 rows at 100ms intervals
Algorithm:  IsolationForest(n_estimators=100, contamination=0.05)
Threshold:  Determined post-training: THRESHOLD = np.percentile(
              model.decision_function(X_train), 5)  # bottom 5th percentile
Fallback:   Z-score threshold — delta_pwm > 80 in 100ms = intrusion
```

---

### 5.3 GPS Spoofing — Golden Route Integrity Check

**Attack:** Hacker publishes `hacker/gps` with fabricated coordinates to redirect car's route.

**Defense:**
- Golden Route (list of expected waypoints) pre-loaded on IDS server at startup — immutable at runtime
- ESP32 publishes simulated GPS waypoints to `car/gps` every 5 seconds (cycles through route)
- IDS checks `car/gps` against expected waypoint using Haversine distance every 5s
- Deviation > 50m → intrusion alert + `ROUTE_LOCKED = True`
- When locked: all external GPS update requests rejected; car continues on last known good heading
- `hacker/gps` topic is monitored for logging only — never used for routing decisions

```python
# Core check
dist = haversine(car_reported_pos, golden_route[current_index])
if dist > 50:  # meters
    publish("ids/alert", {"type": "gps_spoof", "dist_m": dist})
    ROUTE_LOCKED = True
```

---

## 6. ML Pipeline

### Training (Day 1 evening)
1. Drive car normally for 15 minutes — MQTT subscriber logs `car/speed` to `data/normal_drive.csv`
2. Feature extraction: sliding 10-window aggregation
3. Train `IsolationForest` with `sklearn`, save model + scaler with `joblib`

### Inference (real-time, Day 2+)
```python
speed_window = deque(maxlen=10)

def on_speed_message(msg):
    speed_window.append(extract_features(msg))
    if len(speed_window) == 10:
        X = scaler.transform([aggregate(speed_window)])
        score = model.decision_function(X)[0]
        if score < THRESHOLD:
            anomaly_counter += 1
            if anomaly_counter >= 3:
                alert_and_correct()
        else:
            anomaly_counter = 0
            last_safe_pwm = current_pwm
```

---

## 7. Monitoring Dashboard

**Stack:** Python + Flask + Socket.IO + paho-mqtt + Chart.js

**Data flow:** MQTT → Python IDS → Socket.IO emit → browser DOM update (push-based, <200ms latency)

**UI panels:**
- Car status badge (SAFE / INTRUSION)
- Speed gauge (current PWM)
- Traffic signal state (RED / GREEN + dual-verify status)
- Route integrity state (OK / LOCKED + deviation meters)
- Live speed chart (last 60 seconds)
- Intrusion log (timestamped event stream)

---

## 8. Hacker Simulation

Python CLI script (`hacker.py`) with attack menu:
```
[1] Speed spike attack  → publishes hacker/speed = 255
[2] GPS spoof attack    → publishes hacker/gps = (0.0, 0.0)
[3] IR override attempt → publishes hacker/ir = GREEN (will be detected)
[4] Stop all attacks
```

Run from any machine on same WiFi network. No special hardware required.

---

## 9. 3-Day Build Schedule

### Day 1 — Hardware + ESP32 Firmware
- [ ] Assemble chassis, motors, L298N, buck converter
- [ ] Wire IR receiver, HC-SR04, encoder
- [ ] Flash ESP32: WiFi connect + Mosquitto MQTT
- [ ] Implement: motor control via PWM
- [ ] Implement: hardware interrupt for IR stop
- [ ] Implement: ultrasonic emergency stop (<15cm)
- [ ] Implement: dual-verify traffic signal logic
- [ ] ESP32 publishes: `car/speed`, `car/gps`, `car/ir`, `car/status`
- [ ] ESP32 subscribes: `car/command`, `traffic/signal`
- [ ] Install Mosquitto on laptop, verify data with MQTT Explorer
- [ ] Collect 15 min normal drive data → `data/normal_drive.csv`

### Day 2 — IDS + ML + Dashboard
- [ ] Train Isolation Forest on `normal_drive.csv`
- [ ] IDS service: subscribe all topics, rolling window inference
- [ ] Speed IDS: anomaly detection + correction via `car/command`
- [ ] GPS IDS: haversine check + route lock
- [ ] Traffic IDS: dual-verify mismatch detection
- [ ] Flask app + Socket.IO: push alerts to browser
- [ ] Dashboard: status cards, intrusion log
- [ ] End-to-end test: all 3 attacks detected

### Day 3 — Polish + Demo
- [ ] Live speed chart (Chart.js)
- [ ] OLED on car: SAFE / INTRUSION display
- [ ] IR LED traffic signal demo unit
- [ ] `hacker.py` CLI with clean attack menu
- [ ] Demo run x3 end-to-end
- [ ] Record backup demo video
- [ ] (Bonus) HMAC-SHA256 signing on `car/command` + `traffic/signal`
- [ ] (Bonus) Local Z-score fallback on ESP32

---

## 10. Known Flaws & Limitations

| # | Flaw | Severity | Mitigation |
|---|---|---|---|
| 1 | Mosquitto has no auth — anyone on WiFi can publish | High | Enable ACL + credentials (out of 3-day scope) |
| 2 | `car/command` unsigned — hacker can publish corrections | High | HMAC signing (Day 3 bonus) |
| 3 | GPS fully simulated — real drift not modeled | Medium | Acceptable for demo; state clearly in presentation |
| 4 | Isolation Forest trained once — gradual drift attacks may evade | Medium | Sliding window retraining or LSTM as future work |
| 5 | Physical IR + MQTT dual-verify still defeatable if attacker has broker access | Medium | Broker auth (Flaw 1 fix) closes this |
| 6 | IDS server crash = no cloud-side detection | High | Local Z-score fallback on ESP32 (Day 3 bonus) |

---

## 11. File Structure

```
project/
├── firmware/
│   └── car_esp32/
│       └── car_esp32.ino       # ESP32 Arduino sketch
├── ids/
│   ├── ids_service.py          # MQTT subscriber + IDS logic
│   ├── train_model.py          # Isolation Forest training
│   ├── gps_checker.py          # Haversine route validation
│   └── models/
│       ├── ids_model.pkl
│       └── scaler.pkl
├── dashboard/
│   ├── app.py                  # Flask + Socket.IO server
│   └── templates/
│       └── index.html
├── hacker/
│   └── hacker.py               # Attack simulation CLI
└── data/
    └── normal_drive.csv        # Training data (collected Day 1)
```
