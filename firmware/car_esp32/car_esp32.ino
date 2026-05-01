/*
 * Car IDS — ESP32 Car Firmware
 * Publishes: car/speed, car/gps, car/ir, car/status
 * Subscribes: car/command, traffic/signal, car/route, ids/heartbeat
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <NewPing.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>

// ── WiFi + MQTT Config ───────────────────────────────────────
const char* WIFI_SSID   = "ACT-ai_102797406186";   // or your 2.4GHz SSID
const char* WIFI_PASS   = "20970154";     // ← your actual password
const char* MQTT_BROKER = "192.168.0.9";            // ← your laptop's IP
const int   MQTT_PORT   = 1883;

// ── Motor Pins ───────────────────────────────────────────────
#define MOTOR_A_IN1  5
#define MOTOR_A_IN2  17
#define MOTOR_B_IN3  32
#define MOTOR_B_IN4  33
#define MOTOR_A_EN   25
#define MOTOR_B_EN   18
#define PWM_FREQ     1000
#define PWM_RES      8

// ── IR Receiver (TX-RX obstacle module) ──────────────────────
#define IR_PIN 13

// ── Ultrasonic ───────────────────────────────────────────────
#define TRIG_PIN     14
#define ECHO_PIN     15
#define MAX_DIST_CM  200
NewPing sonar(TRIG_PIN, ECHO_PIN, MAX_DIST_CM);

// ── OLED Display ─────────────────────────────────────────────
#define SCREEN_W 128
#define SCREEN_H 64
Adafruit_SSD1306 display(SCREEN_W, SCREEN_H, &Wire, -1);
bool oledAvailable = false;

// ── Buzzer ───────────────────────────────────────────────────
#define BUZZER_PIN 16

// ── Rotary Encoder ───────────────────────────────────────────
#define ENC_CLK 19
#define ENC_DT  23
#define ENC_SW   4

// ── State Variables ──────────────────────────────────────────
int  currentPwm      = 0;
int  lastSafePwm     = 80;
bool mqttTrafficRed  = false;
volatile bool irSignalDetected = false;
bool intrusionState  = false;
unsigned long lastHeartbeat = 0;
bool idsOnline       = false;

// Encoder state
volatile int  encoderTarget  = 80;   // speed set by knob (0–200)
volatile bool encoderChanged = false;
volatile bool encBtnPressed  = false;
volatile int  lastClkState   = HIGH;

// GPS route — received from IDS via MQTT, fallback to defaults
float gpsRoute[10][2] = {
  {12.9716f, 77.5946f},
  {12.9720f, 77.5950f},
  {12.9724f, 77.5954f},
  {12.9728f, 77.5958f},
  {12.9732f, 77.5962f}
};
int gpsRouteLen   = 5;
int gpsIndex      = 0;
bool routeReceived = false;

// Timing
unsigned long lastSpeedPub      = 0;
unsigned long lastGpsPub        = 0;
unsigned long lastStatusPub     = 0;
unsigned long lastIrPub         = 0;
unsigned long lastOledUpd       = 0;
unsigned long lastReconnectAt   = 0;   // non-blocking MQTT reconnect
unsigned long obstacleStopAt    = 0;   // non-blocking obstacle pause
bool          obstacleActive    = false;
unsigned long buzzerOffAt       = 0;   // non-blocking buzzer
bool          buzzerOn          = false;

WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

// ── Motor Control ────────────────────────────────────────────
void setSpeed(int pwm) {
  pwm = constrain(pwm, 0, 255);
  currentPwm = pwm;
  if (pwm == 0) {
    digitalWrite(MOTOR_A_IN1, LOW);
    digitalWrite(MOTOR_A_IN2, LOW);
    digitalWrite(MOTOR_B_IN3, LOW);
    digitalWrite(MOTOR_B_IN4, LOW);
  } else {
    digitalWrite(MOTOR_A_IN1, HIGH);
    digitalWrite(MOTOR_A_IN2, LOW);
    digitalWrite(MOTOR_B_IN3, HIGH);
    digitalWrite(MOTOR_B_IN4, LOW);
  }
  ledcWrite(MOTOR_A_EN, pwm);
  ledcWrite(MOTOR_B_EN, pwm);
}

// ── IR Interrupt ─────────────────────────────────────────────
void IRAM_ATTR onIrChange() {
  irSignalDetected = (digitalRead(IR_PIN) == LOW);
}

// ── Rotary Encoder Interrupts ─────────────────────────────────
void IRAM_ATTR onEncoderChange() {
  int clk = digitalRead(ENC_CLK);
  if (clk == LOW && lastClkState == HIGH) {
    if (digitalRead(ENC_DT) == HIGH) {
      encoderTarget = min(encoderTarget + 10, 200);  // CW → faster
    } else {
      encoderTarget = max(encoderTarget - 10, 0);    // CCW → slower
    }
    encoderChanged = true;
  }
  lastClkState = clk;
}

void IRAM_ATTR onEncButton() {
  encBtnPressed = true;   // press knob → emergency stop / resume
}

// ── OLED Continuous Update ────────────────────────────────────
void updateOledContinuous() {
  if (!oledAvailable) return;
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  // Row 1: STATUS (large)
  display.setTextSize(2);
  display.setCursor(0, 0);
  if (!idsOnline) {
    display.println("NO IDS!");
  } else if (intrusionState) {
    display.println("INTRUSION");
  } else {
    display.println("  SAFE");
  }

  // Row 2: Speed bar
  display.setTextSize(1);
  display.setCursor(0, 20);
  display.print("SPD:");
  display.print(currentPwm);
  display.print("  TGT:");
  display.println(encoderTarget);

  // Row 3: Signal
  display.setCursor(0, 32);
  display.print("SIG: ");
  display.println(mqttTrafficRed ? "RED  [STOP]" : "GREEN [GO] ");

  // Row 4: IDS heartbeat age
  display.setCursor(0, 44);
  if (idsOnline) {
    unsigned long age = (millis() - lastHeartbeat) / 1000;
    display.print("HB: ");
    display.print(age);
    display.println("s ago");
  } else {
    display.println("HB: LOST");
  }

  display.display();
}

// ── OLED Alert (called on events) ────────────────────────────
void updateOled(bool intrusion) {
  // delegate to continuous update — keeps display consistent
  (void)intrusion;
  updateOledContinuous();
}

// ── Buzzer Alert (non-blocking) ───────────────────────────────
void buzzAlert(int duration_ms) {
  digitalWrite(BUZZER_PIN, HIGH);
  buzzerOffAt = millis() + duration_ms;
  buzzerOn    = true;
}

// ── Publish Functions ────────────────────────────────────────
void publishSpeed() {
  char buf[32];
  snprintf(buf, sizeof(buf), "{\"pwm\":%d}", currentPwm);
  mqtt.publish("car/speed", buf);
}

void publishGps() {
  char buf[80];
  snprintf(buf, sizeof(buf), "{\"lat\":%.6f,\"lon\":%.6f,\"idx\":%d}",
           gpsRoute[gpsIndex][0], gpsRoute[gpsIndex][1], gpsIndex);
  mqtt.publish("car/gps", buf);
  gpsIndex = (gpsIndex + 1) % gpsRouteLen;
}

// ── MQTT Callback ────────────────────────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) return;

  String t = String(topic);

  if (t == "traffic/signal") {
    const char* state = doc["state"];
    if (state) {
      mqttTrafficRed = (strcmp(state, "RED") == 0);
    }
  }

  else if (t == "car/command") {
    const char* action = doc["action"];
    if (action && strcmp(action, "set_speed") == 0) {
      int val = doc["value"] | 0;
      setSpeed(constrain(val, 0, 255));
      intrusionState = true;
      updateOled(true);
      buzzAlert(300);
    }
  }

  else if (t == "car/route") {
    JsonArray waypoints = doc["waypoints"];
    if (waypoints && waypoints.size() > 0 && waypoints.size() <= 10) {
      gpsRouteLen = waypoints.size();
      for (int i = 0; i < gpsRouteLen; i++) {
        gpsRoute[i][0] = waypoints[i]["lat"];
        gpsRoute[i][1] = waypoints[i]["lon"];
      }
      gpsIndex = 0;
      routeReceived = true;
      Serial.println("Route received from IDS");
    }
  }

  else if (t == "ids/heartbeat") {
    lastHeartbeat = millis();
    idsOnline = true;
  }
}

// ── MQTT Reconnect (non-blocking, retries every 5s) ──────────
void reconnectMqtt() {
  unsigned long now = millis();
  if (now - lastReconnectAt < 5000) return;   // don't hammer the broker
  lastReconnectAt = now;

  Serial.print("MQTT connecting...");
  if (mqtt.connect("car_esp32")) {
    mqtt.subscribe("traffic/signal");
    mqtt.subscribe("car/command");
    mqtt.subscribe("car/route");
    mqtt.subscribe("ids/heartbeat");
    Serial.println(" connected + subscribed");
  } else {
    Serial.print(" failed, rc=");
    Serial.println(mqtt.state());
  }
}

// ── Setup ────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Motor setup
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN3, OUTPUT);
  pinMode(MOTOR_B_IN4, OUTPUT);
  ledcAttach(MOTOR_A_EN, PWM_FREQ, PWM_RES);
  ledcAttach(MOTOR_B_EN, PWM_FREQ, PWM_RES);

  // IR receiver
  pinMode(IR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(IR_PIN), onIrChange, CHANGE);

  // Rotary encoder
  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT,  INPUT_PULLUP);
  pinMode(ENC_SW,  INPUT_PULLUP);
  lastClkState = digitalRead(ENC_CLK);
  attachInterrupt(digitalPinToInterrupt(ENC_CLK), onEncoderChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_SW),  onEncButton,     FALLING);

  // Buzzer
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // OLED
  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    oledAvailable = true;
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 20);
    display.println("Car IDS Booting...");
    display.display();
  } else {
    Serial.println("OLED not found — continuing without display");
  }

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());

  // MQTT
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(60);        // 60s keepalive — tolerates brief loop delays
  mqtt.setSocketTimeout(10);    // 10s socket timeout
  reconnectMqtt();

  // Start moving
  setSpeed(80);
  lastHeartbeat = millis();
  idsOnline = true;

  if (oledAvailable) {
    updateOled(false);
  }

  buzzAlert(100);
  Serial.println("Car IDS firmware ready");
}

// ── Loop ─────────────────────────────────────────────────────
void loop() {
  mqtt.loop();                              // keep connection alive first
  if (!mqtt.connected()) reconnectMqtt();  // non-blocking retry every 5s

  unsigned long now = millis();

  // ── Buzzer tick (non-blocking) ──
  if (buzzerOn && now >= buzzerOffAt) {
    digitalWrite(BUZZER_PIN, LOW);
    buzzerOn = false;
  }

  // ── Heartbeat watchdog: if no IDS heartbeat for 10s, force stop ──
  if (idsOnline && (now - lastHeartbeat > 10000)) {
    idsOnline = false;
    setSpeed(0);                  // ← force full stop
    updateOledContinuous();
    buzzAlert(500);
    Serial.println("WARNING: IDS heartbeat lost — STOPPED");
  }

  // ── Ultrasonic emergency stop (non-blocking) ──
  if (!obstacleActive) {
    int dist = sonar.ping_cm();
    if (dist > 0 && dist < 15) {
      setSpeed(0);
      char statusBuf[64];
      snprintf(statusBuf, sizeof(statusBuf), "{\"event\":\"obstacle\",\"dist_cm\":%d}", dist);
      mqtt.publish("car/status", statusBuf);
      obstacleActive = true;
      obstacleStopAt = now + 1500;   // resume after 1.5s (non-blocking)
    }
  } else if (now >= obstacleStopAt) {
    obstacleActive = false;
    if (!mqttTrafficRed && idsOnline) setSpeed(lastSafePwm);
  }

  // ── Rotary encoder: adjust target speed ──
  if (encoderChanged) {
    encoderChanged = false;
    lastSafePwm = encoderTarget;
    if (idsOnline && !mqttTrafficRed && currentPwm > 0) {
      setSpeed(encoderTarget);
    }
    Serial.print("Encoder target: "); Serial.println(encoderTarget);
  }

  // ── Encoder button: toggle stop / resume ──
  if (encBtnPressed) {
    encBtnPressed = false;
    if (currentPwm > 0) {
      setSpeed(0);
      Serial.println("Encoder btn: STOP");
    } else if (idsOnline && !mqttTrafficRed) {
      setSpeed(encoderTarget);
      Serial.println("Encoder btn: RESUME");
    }
  }

  // ── Traffic signal: stop if MQTT says RED ──
  if (mqttTrafficRed) {
    setSpeed(0);
  } else if (currentPwm == 0 && !mqttTrafficRed && idsOnline && !obstacleActive) {
    setSpeed(lastSafePwm);
  }

  // ── Continuous OLED refresh every 500ms ──
  if (now - lastOledUpd >= 500) {
    lastOledUpd = now;
    updateOledContinuous();
  }

  // ── Publish traffic state every 1s ──
  if (now - lastIrPub >= 1000) {
    lastIrPub = now;
    char irBuf[64];
    snprintf(irBuf, sizeof(irBuf),
      "{\"ir_red\":%s,\"mqtt_red\":%s,\"mismatch\":false}",
      mqttTrafficRed ? "true" : "false",
      mqttTrafficRed ? "true" : "false");
    mqtt.publish("car/ir", irBuf);
  }

  // ── Publish speed every 200ms ──
  if (now - lastSpeedPub >= 200) {
    lastSpeedPub = now;
    publishSpeed();
    if (currentPwm > 20) lastSafePwm = currentPwm;
  }

  // ── Publish GPS every 5s ──
  if (now - lastGpsPub >= 5000) {
    lastGpsPub = now;
    publishGps();
  }

  // ── Publish status heartbeat every 2s ──
  if (now - lastStatusPub >= 2000) {
    lastStatusPub = now;
    mqtt.publish("car/status", "{\"status\":\"alive\"}");

    // Reset intrusion state after 10s of no new alerts
    if (intrusionState && (now - lastHeartbeat < 10000)) {
      intrusionState = false;
      updateOled(false);
    }
  }
}
