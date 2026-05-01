# Car IDS — TODOs

> Generated from engineering review on 2026-04-29

## Post-Demo Enhancements

### 1. MQTT Broker Authentication (ACL + Credentials)
**What:** Enable Mosquitto ACL so only authorized clients can publish to `car/*` and `traffic/*` topics.
**Why:** Flaw #1 — anyone on WiFi can inject messages. Root cause of Flaws #2 and #5.
**How:** Mosquitto `password_file` + `acl_file`. ~30 min to configure + test.
**Closes:** Known Flaws #1, #2, #5.
**Depends on:** Nothing — can be done after core build.

### 2. Gradual Drift Attack Detection (EWMA/CUSUM)
**What:** Long-window trend detector catching speed increases of 2-3 PWM/sec sustained over 30+ seconds.
**Why:** Flaw #4 — Isolation Forest on 1-second windows misses slow ramps.
**How:** EWMA with 30-second lookback. Compare `EWMA(now)` vs `EWMA(30s ago)`.
**Depends on:** Core IDS working first.

## Day 3 Polish

### 3. Buzzer Alert on Intrusion
**What:** Wire buzzer to ESP32 GPIO. Sound 500ms on intrusion correction or heartbeat timeout.
**Why:** High demo impact — evaluators hear the attack being detected.
**How:** Active buzzer, HIGH/LOW on GPIO. ~10 min. Add enable/disable flag.
**Depends on:** ESP32 firmware Task 5+ (car/command handler).

## Pre-Build

### 4. Adapt Plan Commands for Windows 11
**What:** Replace macOS commands (brew, ipconfig getifaddr en0, source venv/bin/activate) with Windows equivalents.
**Why:** Issue 6 — project is being built on Windows 11, plan was written for macOS.
**How:** Mosquitto Windows installer, `venv\Scripts\activate`, `ipconfig` for IP.
**Depends on:** Nothing — do before starting Task 1.
