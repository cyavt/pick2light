#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>

#define WIFI_SSID       "Ngoc Tan"
#define WIFI_PASS       "99999999"

#define MQTT_BROKER     "192.168.1.19"
#define MQTT_PORT       1883
#define MQTT_USERNAME   ""
#define MQTT_PASSWORD   ""

#define ZONE_ID         "zone-a"
#define DEVICE_ID       "PTL-A001"

#define LED_PIN         48
#define LED_COUNT       1
#define BUTTON_PIN      0 // Test nút BOOT (active LOW)

#define HEARTBEAT_MS    5000

char topicCmd[64];     // ptl/device/zone-a/PTL-A001/cmd
char topicEvent[64];   // ptl/device/zone-a/PTL-A001/event
char topicStatus[64];  // ptl/device/zone-a/PTL-A001/status

WiFiClient espClient;
PubSubClient mqtt(espClient);
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

unsigned long lastHeartbeat = 0;
unsigned long lastDebounce = 0;
bool buttonPressed = false;
String currentTaskId = "";
bool ledActive = false;

uint32_t parseColor(const char* hex) {
    if (hex[0] == '#') hex++;
    long color = strtol(hex, NULL, 16);
    uint8_t r = (color >> 16) & 0xFF;
    uint8_t g = (color >> 8) & 0xFF;
    uint8_t b = color & 0xFF;
    return strip.Color(r, g, b);
}

void setLED(uint32_t color) {
    for (int i = 0; i < LED_COUNT; i++) {
        strip.setPixelColor(i, color);
    }
    strip.show();
}

void blinkLED(uint32_t color, int times, int delayMs) {
    for (int i = 0; i < times; i++) {
        setLED(color);
        delay(delayMs);
        setLED(0);
        delay(delayMs);
    }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, payload, length);
    if (err) {
        Serial.printf("[MQTT] JSON parse error: %s\n", err.c_str());
        return;
    }

    const char* action = doc["action"] | "unknown";
    Serial.printf("[MQTT] ← %s | action=%s\n", topic, action);

    if (strcmp(action, "led_on") == 0) {
        const char* color = doc["color"] | "#00FF00";
        int quantity = doc["quantity"] | 0;
        const char* taskId = doc["task_id"] | "";

        currentTaskId = String(taskId);
        ledActive = true;

        // Bật LED theo màu
        uint32_t c = parseColor(color);
        setLED(c);

        Serial.printf("[LED] ON — color=%s, qty=%d, task=%s\n", color, quantity, taskId);
    } else if (strcmp(action, "led_off") == 0) {
        currentTaskId = "";
        ledActive = false;
        setLED(0);
        Serial.println("[LED] OFF");
    }
}


void connectWiFi() {
    Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
}

void connectMQTT() {
    mqtt.setServer(MQTT_BROKER, MQTT_PORT);
    mqtt.setCallback(mqttCallback);
    mqtt.setBufferSize(512);

    while (!mqtt.connected()) {
        Serial.printf("[MQTT] Connecting to %s:%d...\n", MQTT_BROKER, MQTT_PORT);

        String clientId = String("esp32-") + DEVICE_ID;
        bool ok;
        if (strlen(MQTT_USERNAME) > 0) {
            ok = mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD);
        } else {
            ok = mqtt.connect(clientId.c_str());
        }

        if (ok) {
            Serial.println("[MQTT] Connected!");
            // Subscribe to command topic
            mqtt.subscribe(topicCmd);
            Serial.printf("[MQTT] Subscribed: %s\n", topicCmd);

            // Blink xanh 2 lần = kết nối thành công
            blinkLED(strip.Color(0, 255, 0), 2, 200);
        } else {
            Serial.printf("[MQTT] Failed (rc=%d), retry in 5s...\n", mqtt.state());
            // Blink đỏ = lỗi
            blinkLED(strip.Color(255, 0, 0), 3, 150);
            delay(5000);
        }
    }
}

void handleButton() {
    bool state = digitalRead(BUTTON_PIN) == LOW;  // Active LOW

    if (state && !buttonPressed && (millis() - lastDebounce > 300)) {
        buttonPressed = true;
        lastDebounce = millis();

        if (ledActive && currentTaskId.length() > 0) {
            // Publish button_pressed event
            JsonDocument doc;
            doc["event"] = "button_pressed";
            doc["device_id"] = DEVICE_ID;
            doc["task_id"] = currentTaskId;
            doc["timestamp"] = millis();

            char buffer[256];
            serializeJson(doc, buffer);
            mqtt.publish(topicEvent, buffer);

            Serial.printf("[BTN] Pressed! → %s\n", topicEvent);

            // Blink nhanh = xác nhận đã gửi, chờ server gửi led_off
            uint32_t currentColor = strip.getPixelColor(0);
            setLED(0);
            delay(100);
            setLED(currentColor);
        } else {
            Serial.println("[BTN] Pressed but no active task");
        }
    }

    if (!state) {
        buttonPressed = false;
    }
}

void sendHeartbeat() {
    if (millis() - lastHeartbeat < HEARTBEAT_MS) return;
    lastHeartbeat = millis();

    JsonDocument doc;
    doc["event"] = "heartbeat";
    doc["device_id"] = DEVICE_ID;
    doc["zone_id"] = ZONE_ID;
    doc["uptime"] = millis() / 1000;
    doc["rssi"] = WiFi.RSSI();
    doc["free_heap"] = ESP.getFreeHeap();

    char buffer[256];
    serializeJson(doc, buffer);
    mqtt.publish(topicStatus, buffer);

    Serial.printf("[HB] → rssi=%d, heap=%d\n", WiFi.RSSI(), ESP.getFreeHeap());
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n=== Pick-to-Light ESP32-S3 ===");
    Serial.printf("Zone: %s | Device: %s\n", ZONE_ID, DEVICE_ID);

    snprintf(topicCmd,    sizeof(topicCmd),    "ptl/device/%s/%s/cmd",    ZONE_ID, DEVICE_ID);
    snprintf(topicEvent,  sizeof(topicEvent),  "ptl/device/%s/%s/event",  ZONE_ID, DEVICE_ID);
    snprintf(topicStatus, sizeof(topicStatus), "ptl/device/%s/%s/status", ZONE_ID, DEVICE_ID);

    pinMode(BUTTON_PIN, INPUT_PULLUP);
    strip.begin();
    strip.setBrightness(80);
    strip.show();

    connectWiFi();
    connectMQTT();
}

void loop() {
    if (!mqtt.connected()) {
        connectMQTT();
    }
    mqtt.loop();

    handleButton();
    // sendHeartbeat();
}
