# Car IDS — Complete Circuit Wiring Guide

**Date:** 2026-04-29
**Hardware inventory verified**

---

## Overview — Two ESP32 Units

```
 UNIT 1: CAR ESP32                          UNIT 2: TRAFFIC SIGNAL ESP32
 ┌──────────────────────────┐               ┌──────────────────────────┐
 │  L298N Motor Driver      │               │  IR LED (940nm)          │
 │  IR Receiver (TSOP1738)  │               │  Red LED (visual)        │
 │  HC-SR04 Ultrasonic      │               │  Green LED (visual)      │
 │  Rotary Encoders x2      │               │                          │
 │  OLED Display (SSD1306)  │               │  Simple circuit          │
 │  Buzzer                  │               │  ~10 wires total         │
 │  DC Motors x2            │               │                          │
 │  ~25 wires total         │               │                          │
 └──────────────────────────┘               └──────────────────────────┘
```

---

## UNIT 1: CAR ESP32 — Complete Pin Assignment

```
ESP32 Dev Module (38-pin)
┌─────────────────────────────────────┐
│                USB                  │
│            ┌────────┐               │
│     3V3  ──┤1     38├── GND        │
│      EN  ──┤2     37├── GPIO 23    │
│  GPIO 36 ──┤3     36├── GPIO 22 ──── OLED SCL (I2C)
│  GPIO 39 ──┤4     35├── GPIO  1    │
│  GPIO 34 ──┤5     34├── GPIO  3    │  ← Encoder A (Motor A)
│  GPIO 35 ──┤6     33├── GPIO 21 ──── OLED SDA (I2C)
│  GPIO 32 ──┤7     32├── GND        │  ← L298N IN3
│  GPIO 33 ──┤8     31├── GPIO 19    │  ← L298N IN4
│  GPIO 25 ──┤9     30├── GPIO 18 ──── L298N ENB (PWM)
│  GPIO 26 ──┤10    29├── GPIO  5    │  ← L298N IN1
│  GPIO 27 ──┤11    28├── GPIO 17    │  ← L298N IN2
│  GPIO 14 ──┤12    27├── GPIO 16 ──── Buzzer (+)
│  GPIO 12 ──┤13    26├── GPIO  4    │
│     GND  ──┤14    25├── GPIO  2    │  ← Onboard LED
│  GPIO 13 ──┤15    24├── GPIO 15    │  ← IR Receiver OUT / HC-SR04 ECHO
│      5V  ──┤16    23├── GPIO  0    │
│            └────────┘               │
│         (pin numbers vary by board) │
└─────────────────────────────────────┘
```

### Final Pin Map (Car ESP32)

| GPIO | Connected To | Direction | Notes |
|------|-------------|-----------|-------|
| 5 | L298N IN1 | OUT | Motor A direction 1 |
| 17 | L298N IN2 | OUT | Motor A direction 2 |
| 25 | L298N ENA | OUT (PWM) | Motor A speed control |
| 32 | L298N IN3 | OUT | Motor B direction 1 |
| 33 | L298N IN4 | OUT | Motor B direction 2 |
| 18 | L298N ENB | OUT (PWM) | Motor B speed control |
| 13 | IR TX-RX Module OUT | IN | Obstacle-type IR module (hardware interrupt) |
| 14 | HC-SR04 TRIG | OUT | Ultrasonic trigger |
| 15 | HC-SR04 ECHO | IN | Ultrasonic echo |
| 34 | Encoder A signal | IN | Motor A speed sensor (input-only pin) |
| 35 | Encoder B signal | IN | Motor B speed sensor (input-only pin) |
| 21 | OLED SDA | I2C | SSD1306 data |
| 22 | OLED SCL | I2C | SSD1306 clock |
| 16 | Buzzer (+) | OUT | Active buzzer alert |

**Note:** GPIO 34, 35, 36, 39 are **input-only** on ESP32 — they cannot output. Perfect for encoders.

---

## UNIT 1: CAR — Wiring by Component

### 1. Power System

```
                    ┌─────────────────────────────────────────────┐
                    │              POWER DISTRIBUTION              │
                    └─────────────────────────────────────────────┘

  Battery (7.4V LiPo)
  ┌──────────┐
  │  (+) RED ├──────┬──────────────────────────────── L298N VCC (12V input)
  │          │      │                                  (motor power, direct)
  │  (-) BLK ├──┐   │
  └──────────┘  │   │
                │   │   ┌──────────────────┐
                │   └──►│ BUCK CONVERTER   │
                │       │ IN+     OUT+ ────├──────┬── ESP32 5V pin
                │       │                  │      ├── L298N +5V (logic power)
                └──────►│ IN-     OUT- ────├──┐   ├── HC-SR04 VCC
                        │                  │  │   └── OLED VCC
                        │ (Adjust to 5.0V) │  │
                        └──────────────────┘  │
                                              │
                  COMMON GROUND ──────────────┴── ESP32 GND
                  (ALL GND pins                   L298N GND
                   connect here)                  HC-SR04 GND
                                                  OLED GND
                                                  IR Receiver GND
                                                  Encoders GND
                                                  Buzzer GND
```

**CRITICAL: Adjust buck converter BEFORE connecting ESP32.**
1. Connect battery to buck converter IN+ / IN-
2. Use multimeter on OUT+ / OUT-
3. Turn the potentiometer screw until output reads **5.0V**
4. THEN connect to ESP32 and other components

**Switch placement (optional but recommended):**
Wire one of your switches between Battery (+) and the rest of the circuit for easy power on/off.

---

### 2. L298N Motor Driver

```
                    ┌─────────────────────────────────────────────┐
                    │              L298N MOTOR DRIVER              │
                    └─────────────────────────────────────────────┘

  L298N Board (top view)
  ┌─────────────────────────────────────┐
  │                                     │
  │  MOTOR A         MOTOR B            │
  │  ┌─────┐         ┌─────┐           │
  │  │OUT1 ├─►Motor A │OUT3 ├─►Motor B │
  │  │OUT2 ├─►  (+/-) │OUT4 ├─►  (+/-) │
  │  └─────┘         └─────┘           │
  │                                     │
  │  ENA  IN1  IN2  IN3  IN4  ENB      │ ← Pin header row
  │   │    │    │    │    │    │        │
  │  +12V  +5V  GND                    │ ← Screw terminals
  │   │    │    │                       │
  └───┼────┼────┼───────────────────────┘
      │    │    │
      │    │    └── Common GND (to buck converter OUT-, ESP32 GND)
      │    └── 5V from buck converter OUT+ (remove jumper if VCC > 12V)
      └── Battery (+) direct (7.4V for motors)

  WIRING TO ESP32:

  L298N ENA ──────── ESP32 GPIO 25  (PWM speed control Motor A)
  L298N IN1 ──────── ESP32 GPIO  5  (Motor A direction)
  L298N IN2 ──────── ESP32 GPIO 17  (Motor A direction)
  L298N IN3 ──────── ESP32 GPIO 32  (Motor B direction)
  L298N IN4 ──────── ESP32 GPIO 33  (Motor B direction)
  L298N ENB ──────── ESP32 GPIO 18  (PWM speed control Motor B)
```

**L298N Jumper Note:**
- If the 5V jumper is ON (default), the L298N generates its own 5V from the 12V input — but only works well above 7V input.
- With 7.4V battery: **keep the jumper ON**. The L298N's onboard regulator will provide 5V.
- Alternative: Remove jumper and feed 5V from buck converter to the +5V terminal.

**Motor Direction Logic:**

| IN1 | IN2 | Motor A |
|-----|-----|---------|
| HIGH | LOW | Forward |
| LOW | HIGH | Reverse |
| LOW | LOW | Stop (coast) |
| HIGH | HIGH | Brake |

Same logic for IN3/IN4 → Motor B.

**Motor wiring:**
```
  L298N OUT1 ──── Motor A wire 1 (red)
  L298N OUT2 ──── Motor A wire 2 (black)
  L298N OUT3 ──── Motor B wire 1 (red)
  L298N OUT4 ──── Motor B wire 2 (black)
```
If a motor spins backwards, swap its two wires.

---

### 3. IR Transmitter-Receiver Module (Obstacle Avoidance Type)

```
                    ┌─────────────────────────────────────────────┐
                    │     IR TX-RX MODULE (FC-51 / HW-201)        │
                    └─────────────────────────────────────────────┘

  Module (front view — two "eyes" facing forward)
  ┌──────────────────────────────┐
  │  ┌────┐    ┌────┐    ○ POT  │
  │  │ TX │    │ RX │   (adjust │
  │  │(LED)    │(PD)│  sensitiv)│
  │  └────┘    └────┘           │
  │                             │
  │  VCC    GND    OUT          │
  └──┼──────┼──────┼────────────┘
     │      │      │
     │      │      └── OUT ──── ESP32 GPIO 13
     │      └── GND ──── GND
     └── VCC ──── 3.3V (or 5V — check module markings)

  MOUNTING ON CAR:
  ┌─────────────────────────────────────────┐
  │                                         │
  │   Mount on FRONT of car chassis,        │
  │   receiver (RX) side facing FORWARD     │
  │   toward the traffic signal.            │
  │                                         │
  │   ┌─── car direction of travel ───►     │
  │   │                                     │
  │   │  ┌──────┐                           │
  │   │  │RX  TX│ ← IR module              │
  │   │  └──────┘                           │
  │   │   ↑ point this toward               │
  │   │     traffic signal                  │
  │   │                                     │
  │   │  The built-in TX LED will also      │
  │   │  emit IR — this is fine, ignore it. │
  │   │  We only care about the RX side     │
  │   │  detecting IR from the traffic      │
  │   │  signal's separate IR LED.          │
  └─────────────────────────────────────────┘

  POTENTIOMETER ADJUSTMENT:
  Turn the small screw on the module to adjust detection sensitivity.
  - Turn CLOCKWISE = more sensitive (detects weaker IR from farther away)
  - Turn until the OUT LED on the module just barely turns off in ambient light
  - Then back off slightly — this gives max range without false triggers
  - Test range: aim traffic signal IR LED at module, check detection at 30-50cm
```

**How it works (simplified vs TSOP1738):**
- Output is normally HIGH (no IR detected)
- Goes LOW when IR light hits the receiver photodiode
- ESP32 uses hardware interrupt (`attachInterrupt`) on CHANGE
- When LOW → IR detected → car stops (traffic red)
- No 38kHz demodulation — traffic signal just turns IR LED on/off directly
- No IRremote library needed on either ESP32 — just digitalRead/digitalWrite
- Effective range: 30-50cm with potentiometer tuned (sufficient for demo)

---

### 4. HC-SR04 Ultrasonic Sensor

```
                    ┌─────────────────────────────────────────────┐
                    │          HC-SR04 ULTRASONIC SENSOR           │
                    └─────────────────────────────────────────────┘

  HC-SR04 (front view — two "eyes" facing forward)
  ┌───────────────────────┐
  │   ┌────┐    ┌────┐    │
  │   │TRIG│    │ECHO│    │
  │   └────┘    └────┘    │
  │  VCC  TRIG  ECHO  GND │
  └──┼────┼─────┼─────┼───┘
     │    │     │     │
     │    │     │     └── GND ──── GND
     │    │     │
     │    │     └── ECHO ──── ESP32 GPIO 15
     │    │              ⚠ NEEDS VOLTAGE DIVIDER (see below)
     │    │
     │    └── TRIG ──────── ESP32 GPIO 14
     │
     └── VCC ────────────── 5V (from buck converter)

  ⚠ VOLTAGE DIVIDER FOR ECHO PIN:
  HC-SR04 ECHO outputs 5V, but ESP32 GPIOs are 3.3V tolerant.
  Some ESP32 boards handle 5V on input pins, but to be safe:

  HC-SR04 ECHO ──┬── 1kΩ resistor ──── ESP32 GPIO 15
                 │
                 └── 2kΩ resistor ──── GND

  This divides 5V down to ~3.3V:  5V × (2kΩ / (1kΩ + 2kΩ)) = 3.33V

  If you don't have exact resistor values, use any 1:2 ratio
  (e.g., 1kΩ + 2kΩ, 2.2kΩ + 4.7kΩ, 470Ω + 1kΩ)
```

**Mounting:** Point the two ultrasonic transducers (the "eyes") **forward** on the car chassis. Mount at bumper height. The sensor detects obstacles from 2cm to 200cm. The firmware triggers emergency stop at <15cm.

---

### 5. Rotary Encoders (LM393 modules)

```
                    ┌─────────────────────────────────────────────┐
                    │         ROTARY ENCODERS (LM393 x2)          │
                    └─────────────────────────────────────────────┘

  LM393 Encoder Module (typical 3-4 pin):
  ┌──────────────┐
  │  VCC (+)     ├──── 3.3V (or 5V — check module)
  │  GND (-)     ├──── GND
  │  D0 (signal) ├──── ESP32 GPIO (see below)
  │  A0 (analog) ├──── (not used — leave unconnected)
  └──────────────┘

  ENCODER A (Motor A wheel):
     VCC ──── 3.3V
     GND ──── GND
     D0  ──── ESP32 GPIO 34 (input-only pin)

  ENCODER B (Motor B wheel):
     VCC ──── 3.3V
     GND ──── GND
     D0  ──── ESP32 GPIO 35 (input-only pin)

  MOUNTING:
  ┌──────────────────────────┐
  │   WHEEL (side view)      │
  │                          │
  │   ┌────┐                 │
  │   │    │ ← encoder disk  │
  │   │ ○──┼─── motor shaft  │
  │   │    │                 │
  │   └────┘                 │
  │      ↑                   │
  │   LM393 module slot      │
  │   (IR gap sensor reads   │
  │    slots in the disk)    │
  └──────────────────────────┘

  The slotted disk attaches to the motor shaft.
  The LM393 module straddles the disk edge.
  Each slot passing through = 1 pulse on D0.
```

**Note:** Rotary encoders are P2 (recommended, not required). If mounting is difficult on Day 1, skip them — the firmware uses PWM duty cycle as a proxy for speed, which works fine for the IDS demo.

---

### 6. OLED Display (SSD1306, I2C)

```
                    ┌─────────────────────────────────────────────┐
                    │        OLED DISPLAY (SSD1306, I2C)          │
                    └─────────────────────────────────────────────┘

  SSD1306 Module (4-pin I2C):
  ┌──────────────┐
  │  GND         ├──── GND
  │  VCC         ├──── 3.3V (some modules accept 5V — check yours)
  │  SCL         ├──── ESP32 GPIO 22
  │  SDA         ├──── ESP32 GPIO 21
  └──────────────┘

  ⚠ GPIO 21 and 22 are the DEFAULT I2C pins on ESP32.
    The Wire library uses them automatically. No extra config needed.

  I2C Address: 0x3C (most common) or 0x3D
  If display doesn't work, try the other address in code.
```

**Mounting:** Mount OLED on top of the car facing upward so evaluators can see "SAFE" / "INTRUSION" during the demo.

---

### 7. Buzzer

```
                    ┌─────────────────────────────────────────────┐
                    │          ACTIVE BUZZER (5V)                  │
                    └─────────────────────────────────────────────┘

  Active Buzzer (2-pin):
  ┌──────────┐
  │   (+) ───├──── ESP32 GPIO 16
  │   (-) ───├──── GND
  └──────────┘

  The longer leg is (+). Some buzzers have a (+) mark on top.

  "Active" means it has a built-in oscillator —
  just send HIGH to sound, LOW to stop. No tone() needed.

  ⚠ If GPIO 16 doesn't drive enough current (buzzer is quiet):
     Use a transistor switch:

     ESP32 GPIO 16 ──── 1kΩ resistor ──── NPN base (e.g., 2N2222)
                                          NPN collector ──── Buzzer (+)
                                          NPN emitter   ──── GND
                                          Buzzer (-)    ──── 5V
```

---

### 8. Car ESP32 — Complete Wiring Summary

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    CAR ESP32 — ALL CONNECTIONS                                │
│                                                                              │
│  ┌─────────┐    7.4V direct    ┌──────────┐   OUT1 ──── Motor A (+)        │
│  │ Battery ├───────────────────┤ L298N    │   OUT2 ──── Motor A (-)        │
│  │  7.4V   ├──┐               │          │   OUT3 ──── Motor B (+)        │
│  └─────────┘  │  ┌──────────┐ │   ENA ◄──── GPIO 25 (PWM)                │
│               └─►│ Buck Conv│ │   IN1 ◄──── GPIO  5                       │
│                  │ → 5V out ├─┤   IN2 ◄──── GPIO 17                       │
│                  └──┬───────┘ │   IN3 ◄──── GPIO 32                       │
│                     │         │   IN4 ◄──── GPIO 33                       │
│                     │ 5V      │   ENB ◄──── GPIO 18 (PWM)                │
│                     │         │   GND ──┐                                 │
│                     │         └─────────┼────────────────────┐            │
│                     │                   │  COMMON GND        │            │
│               ┌─────┴─────┐             │                    │            │
│               │  ESP32    │             │                    │            │
│               │           │             │                    │            │
│               │  5V  GND ─┼─────────────┘                    │            │
│               │           │                                  │            │
│               │ GPIO 13 ──┼──── IR Receiver OUT              │            │
│               │ GPIO 14 ──┼──── HC-SR04 TRIG                 │            │
│               │ GPIO 15 ──┼──── HC-SR04 ECHO (via divider)   │            │
│               │ GPIO 34 ──┼──── Encoder A (D0)               │            │
│               │ GPIO 35 ──┼──── Encoder B (D0)               │            │
│               │ GPIO 21 ──┼──── OLED SDA                     │            │
│               │ GPIO 22 ──┼──── OLED SCL                     │            │
│               │ GPIO 16 ──┼──── Buzzer (+)                   │            │
│               └───────────┘                                  │            │
│                                                              │            │
│  IR Recv GND ─┬── HC-SR04 GND ─┬── Encoder A GND ──────────┘            │
│               ├── Encoder B GND ┤                                         │
│               ├── OLED GND ─────┤                                         │
│               └── Buzzer (-) ───┘                                         │
│                                                                            │
│  IR Recv VCC ──── 3.3V (from ESP32 3.3V pin)                             │
│  HC-SR04 VCC ─── 5V (from buck converter)                                │
│  OLED VCC ────── 3.3V (from ESP32 3.3V pin)                              │
│  Encoder VCC ─── 3.3V (from ESP32 3.3V pin)                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Wire count: ~24 connections**

---

## UNIT 2: TRAFFIC SIGNAL ESP32

Much simpler circuit — just LEDs.

### Pin Assignment

| GPIO | Connected To | Direction | Notes |
|------|-------------|-----------|-------|
| 2 | IR LED (940nm) | OUT | Transmits IR signal (modulated at 38kHz) |
| 4 | Red LED | OUT | Visual indicator — RED state |
| 5 | Green LED | OUT | Visual indicator — GREEN state |

### Wiring

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                 TRAFFIC SIGNAL ESP32 — ALL CONNECTIONS                        │
│                                                                              │
│  Power: USB from laptop (no battery needed — sits on the desk)              │
│                                                                              │
│               ┌───────────┐                                                  │
│               │  ESP32    │                                                  │
│               │           │                                                  │
│               │ GPIO  2 ──┼──── 100Ω resistor ──── IR LED (+) anode         │
│               │           │                         IR LED (-) cathode → GND │
│               │           │                                                  │
│               │ GPIO  4 ──┼──── 220Ω resistor ──── Red LED (+) anode        │
│               │           │                         Red LED (-) cathode → GND│
│               │           │                                                  │
│               │ GPIO  5 ──┼──── 220Ω resistor ──── Green LED (+) anode      │
│               │           │                         Green LED (-) → GND      │
│               │           │                                                  │
│               │      GND ─┼──── Common GND for all LEDs                     │
│               └───────────┘                                                  │
│                                                                              │
│  LED POLARITY: longer leg = (+) anode, shorter leg = (-) cathode            │
│  Flat side on LED casing = cathode (-)                                       │
│                                                                              │
│  BREADBOARD LAYOUT:                                                          │
│  ┌────────────────────────────────────────────┐                             │
│  │  ESP32 plugged across center channel       │                             │
│  │                                            │                             │
│  │  GPIO 2 ── row A ── 100Ω ── row B ── IR LED (+)                        │
│  │                                    IR LED (-) ── GND rail               │
│  │                                            │                             │
│  │  GPIO 4 ── row C ── 220Ω ── row D ── Red LED (+)                       │
│  │                                    Red LED (-) ── GND rail              │
│  │                                            │                             │
│  │  GPIO 5 ── row E ── 220Ω ── row F ── Green LED (+)                     │
│  │                                    Green LED (-) ── GND rail            │
│  │                                            │                             │
│  │  ESP32 GND ── GND rail                     │                             │
│  └────────────────────────────────────────────┘                             │
│                                                                              │
│  Wire count: ~10 connections                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

**IR LED Note (simplified approach):** Since the car uses an IR TX-RX obstacle
avoidance module (not a TSOP1738), the traffic signal does NOT need 38kHz
modulation. Just turn the IR LED on/off with digitalWrite:
- RED state → `digitalWrite(IR_LED_PIN, HIGH)` → IR LED on → car detects IR → stops
- GREEN state → `digitalWrite(IR_LED_PIN, LOW)` → IR LED off → car sees no IR → drives

No IRremote library needed on either ESP32. This is simpler and more reliable.

Aim the IR LED **directly at the car's IR module** during the demo. Best range: 30-50cm.
Use a high-power IR LED (940nm) with a 100 ohm resistor for maximum brightness.

---

## Wiring Order (Recommended Build Sequence)

Do this step by step. Test after each step.

```
Step 1: Power system                          ⏱ 15 min
  ├── Wire battery → switch → buck converter
  ├── Adjust buck converter to 5.0V
  └── TEST: Multimeter reads 5V on output

Step 2: ESP32 power                           ⏱ 5 min
  ├── Buck converter 5V → ESP32 5V pin
  ├── Buck converter GND → ESP32 GND
  └── TEST: ESP32 powers on, blue LED blinks

Step 3: L298N motor driver                    ⏱ 15 min
  ├── Battery 7.4V → L298N 12V terminal
  ├── Buck 5V → L298N +5V terminal (or keep jumper)
  ├── GND → L298N GND
  ├── Wire IN1-IN4, ENA, ENB to ESP32
  ├── Wire Motor A and Motor B to OUT terminals
  └── TEST: Flash basic motor test sketch
            — motors spin forward, stop, reverse

Step 4: IR receiver                           ⏱ 5 min
  ├── TSOP1738: VCC → 3.3V, GND → GND, OUT → GPIO 13
  └── TEST: Point any IR remote at receiver
            — Serial.println shows signal detected

Step 5: Ultrasonic sensor                     ⏱ 10 min
  ├── HC-SR04: VCC → 5V, GND → GND
  ├── TRIG → GPIO 14
  ├── ECHO → voltage divider → GPIO 15
  └── TEST: Serial.println(sonar.ping_cm())
            — shows distance when hand in front

Step 6: Rotary encoders                       ⏱ 10 min
  ├── Encoder A: VCC → 3.3V, GND → GND, D0 → GPIO 34
  ├── Encoder B: VCC → 3.3V, GND → GND, D0 → GPIO 35
  └── TEST: Spin wheel manually, count pulses

Step 7: OLED display                          ⏱ 5 min
  ├── SDA → GPIO 21, SCL → GPIO 22
  ├── VCC → 3.3V, GND → GND
  └── TEST: Flash I2C scanner sketch
            — should find device at 0x3C

Step 8: Buzzer                                ⏱ 2 min
  ├── (+) → GPIO 16, (-) → GND
  └── TEST: digitalWrite(16, HIGH) → buzzer sounds

Step 9: Traffic signal ESP32                  ⏱ 10 min
  ├── Plug second ESP32 into breadboard
  ├── Wire IR LED + resistor to GPIO 2
  ├── Wire Red LED + resistor to GPIO 4
  ├── Wire Green LED + resistor to GPIO 5
  └── TEST: Flash traffic signal sketch
            — LEDs alternate, IR LED pulses on RED
```

**Total estimated wiring time: ~75 minutes**

---

## Troubleshooting Checklist

| Symptom | Check |
|---------|-------|
| ESP32 won't power on | Verify buck converter is outputting 5V, not higher |
| Motors don't spin | Check L298N enable jumper is ON; check ENA/ENB wires |
| Motor spins wrong direction | Swap the two motor wires at L298N OUT terminals |
| IR receiver not detecting | Verify VCC is 3.3V (not 5V if module is 3.3V-only) |
| HC-SR04 reads 0 always | Check voltage divider on ECHO pin; verify TRIG wire |
| OLED blank | Run I2C scanner — if no device found, check SDA/SCL wires |
| Buzzer silent | Test with 5V directly — if it sounds, GPIO current is too low → add transistor |
| Encoder no pulses | Verify slotted disk is mounted and passing through sensor gap |
| WiFi won't connect | ESP32 only supports 2.4GHz WiFi, not 5GHz |
