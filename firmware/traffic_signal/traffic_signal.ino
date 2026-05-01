/*
 * Car IDS — Traffic Signal Controller
 * Publishes: traffic/signal (RED/GREEN state)
 * Drives: IR LED (on during RED), Red/Green visible LEDs
 * No IRremote needed — direct digitalWrite for IR
 */

#include <WiFi.h>
#include <PubSubClient.h>

// ── WiFi + MQTT Config ───────────────────────────────────────
const char* WIFI_SSID   = "YOUR_SSID";        // ← CHANGE THIS
const char* WIFI_PASS   = "YOUR_PASSWORD";     // ← CHANGE THIS
const char* MQTT_BROKER = "192.168.1.X";       // ← CHANGE to laptop IP
const int   MQTT_PORT   = 1883;

// ── Pin Definitions ──────────────────────────────────────────
#define IR_LED_PIN    2    // IR LED (940nm) with 100 ohm resistor
#define RED_LED_PIN   4    // Red visible LED with 220 ohm resistor
#define GREEN_LED_PIN 5    // Green visible LED with 220 ohm resistor

WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);

bool isRed = false;
unsigned long lastToggle = 0;
const unsigned long RED_DURATION   = 5000;   // 5 seconds red
const unsigned long GREEN_DURATION = 5000;   // 5 seconds green

// ── MQTT Reconnect ───────────────────────────────────────────
void reconnectMqtt() {
  while (!mqtt.connected()) {
    Serial.print("MQTT connecting...");
    if (mqtt.connect("traffic_ctrl")) {
      Serial.println(" connected");
    } else {
      Serial.print(" failed, rc=");
      Serial.println(mqtt.state());
      delay(2000);
    }
  }
}

// ── Set Signal State ─────────────────────────────────────────
void setSignal(bool red) {
  isRed = red;

  if (red) {
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(IR_LED_PIN, HIGH);     // IR on during RED — car stops
    mqtt.publish("traffic/signal", "{\"state\":\"RED\"}");
    Serial.println("Signal: RED");
  } else {
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(GREEN_LED_PIN, HIGH);
    digitalWrite(IR_LED_PIN, LOW);      // IR off during GREEN — car drives
    mqtt.publish("traffic/signal", "{\"state\":\"GREEN\"}");
    Serial.println("Signal: GREEN");
  }
}

// ── Setup ────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  pinMode(IR_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);

  digitalWrite(IR_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(GREEN_LED_PIN, LOW);

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
  reconnectMqtt();

  // Start with GREEN
  setSignal(false);
  lastToggle = millis();

  Serial.println("Traffic signal controller ready");
}

// ── Loop ─────────────────────────────────────────────────────
void loop() {
  if (!mqtt.connected()) reconnectMqtt();
  mqtt.loop();

  unsigned long duration = isRed ? RED_DURATION : GREEN_DURATION;
  if (millis() - lastToggle >= duration) {
    lastToggle = millis();
    setSignal(!isRed);
  }
}
