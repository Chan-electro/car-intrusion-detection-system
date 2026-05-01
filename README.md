# Car Intrusion Detection System (IDS)

Real-time intrusion detection for an ESP32-based autonomous RC car. Detects three categories of cyber-physical attacks over MQTT and displays live alerts on a web dashboard.

---

## Architecture

```
  ESP32 Car                  Laptop (Python)               Browser
  ─────────                  ───────────────               ───────
  Sensors → MQTT publish ──► IDS Service (detection)
  MQTT subscribe ◄────────── IDS heartbeat/commands ──► Dashboard (Flask + Socket.IO)
                   Mosquitto Broker (hub, port 1883)
```

---

## Attack Scenarios

| # | Attack | Detection Method |
|---|--------|-----------------|
| 1 | Speed injection | Isolation Forest ML (scikit-learn) |
| 2 | GPS spoofing | Haversine distance from golden route |
| 3 | Traffic signal spoof | MQTT dual-verify |

---

## Hardware

| Component | Role |
|---|---|
| ESP32 Dev Module | Car brain — WiFi, MQTT, motor control |
| L298N Motor Driver | DC motor PWM control |
| HC-SR04 | Ultrasonic obstacle detection |
| IR TX-RX Module | Traffic signal detection |
| SSD1306 OLED (128×64) | Live status display |
| KY-040 Rotary Encoder | Manual speed adjustment |
| Buzzer | Intrusion audio alert |
| Traffic Signal ESP32 | Publishes RED/GREEN over MQTT |

---

## Project Structure

```
car-intrusion-detection-system/
├── firmware/
│   ├── car_esp32/          # ESP32 car firmware (Arduino)
│   └── traffic_signal/     # Traffic light controller firmware
├── ids/
│   ├── ids_service.py      # Main IDS orchestrator
│   ├── speed_ids.py        # Isolation Forest speed anomaly detection
│   ├── gps_checker.py      # Haversine golden-route GPS validation
│   ├── traffic_ids.py      # Traffic signal dual-verify
│   └── features.py         # Shared feature extraction
├── dashboard/
│   ├── app.py              # Flask + Socket.IO backend
│   └── templates/
│       └── index.html      # Modern Tailwind UI dashboard
├── hacker/
│   └── hacker.py           # Attack simulation CLI
├── scripts/
│   ├── collect_data.py     # Record normal drive data to CSV
│   └── train_model.py      # Train Isolation Forest model
└── tests/                  # 24 unit + integration tests
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start MQTT broker (Mosquitto)
```cmd
"C:\Program Files\Mosquitto\mosquitto.exe" -c "C:\Program Files\Mosquitto\mosquitto.conf" -v
```
`mosquitto.conf` must contain:
```
listener 1883
allow_anonymous true
```

### 3. Flash ESP32 firmware
- Open `firmware/car_esp32/car_esp32.ino` in Arduino IDE
- Set your WiFi SSID/password and laptop IP in the config section
- Upload to ESP32 (board: ESP32 Dev Module)
- Repeat for `firmware/traffic_signal/traffic_signal.ino`

### 4. Train the ML model (first run only)
```bash
# Collect normal drive data first
python scripts/collect_data.py

# Then train
python scripts/train_model.py
```

### 5. Start the dashboard
```bash
python dashboard/app.py
```
Open **http://localhost:5000** in your browser.

### 6. Simulate attacks
```bash
python hacker/hacker.py
```
Choose attack type 1–3 or run all in demo mode (option 4).

---

## Dashboard

White/blue professional UI built with Tailwind CSS and Chart.js:

- **4 stat cards** — Car Status, Speed (PWM), Traffic Signal, Route Integrity
- **Live speed chart** — rolling 60-point PWM history
- **System status panel** — IDS modules and connection state
- **Event log** — timestamped, colour-coded events
- **Attack scenarios** — 3 panels that flash red on detection

---

## Tests

```bash
python -m pytest tests/ -v
```

24 tests covering: GPS checker, speed IDS, traffic IDS, feature extraction, IDS service integration, and dashboard endpoints.

---

## ESP32 Pin Map

| Signal | GPIO |
|---|---|
| Motor A IN1/IN2 | 5, 17 |
| Motor B IN3/IN4 | 32, 33 |
| Motor A/B EN (PWM) | 25, 18 |
| IR receiver | 13 |
| HC-SR04 TRIG/ECHO | 14, 15 |
| OLED SDA/SCL | 21, 22 |
| Buzzer | 16 |
| Encoder CLK/DT/SW | 19, 23, 4 |
