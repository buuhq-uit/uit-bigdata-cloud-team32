#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

// ========= WIFI =========
const char* ssid = "Hiep Thanh";
const char* password = "0979681800";

// ========= SERVER =========
const char* serverUrl = "http://192.168.2.145:5001";

// ========= DHT =========
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ========= SOIL =========
#define SOIL_PIN 34

// ========= BUTTON =========
#define BTN_DEV1 18
#define BTN_DEV2 19

// ========= DEVICE =========
#define DEV1_PIN 23
#define DEV2_PIN 25

bool dev1State = false;
bool dev2State = false;

bool lastBtn1 = HIGH;
bool lastBtn2 = HIGH;

// ========= ADC CALIBRATION =========
#define SOIL_DRY  3500
#define SOIL_WET  1500

void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(BTN_DEV1, INPUT_PULLUP);
  pinMode(BTN_DEV2, INPUT_PULLUP);

  pinMode(DEV1_PIN, OUTPUT);
  pinMode(DEV2_PIN, OUTPUT);

  digitalWrite(DEV1_PIN, LOW);
  digitalWrite(DEV2_PIN, LOW);

  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void loop() {

  // ===== BUTTON TOGGLE DEVICE 1 =====
  bool btn1 = digitalRead(BTN_DEV1);
  if (btn1 == LOW && lastBtn1 == HIGH) {
    dev1State = !dev1State;
    digitalWrite(DEV1_PIN, dev1State ? HIGH : LOW);
    Serial.println(dev1State ? "Device 1 ON" : "Device 1 OFF");
    delay(200);
  }
  lastBtn1 = btn1;

  // ===== BUTTON TOGGLE DEVICE 2 =====
  bool btn2 = digitalRead(BTN_DEV2);
  if (btn2 == LOW && lastBtn2 == HIGH) {
    dev2State = !dev2State;
    digitalWrite(DEV2_PIN, dev2State ? HIGH : LOW);
    Serial.println(dev2State ? "Device 2 ON" : "Device 2 OFF");
    delay(200);
  }
  lastBtn2 = btn2;

  // ===== READ DHT =====
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("DHT read error");
    delay(2000);
    return;
  }

  // ===== READ SOIL =====
  int soilRaw = analogRead(SOIL_PIN);
  int soilPercent = map(soilRaw, SOIL_DRY, SOIL_WET, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  Serial.println("------ SENSOR DATA ------");
  Serial.printf("Temp: %.2f °C\n", temperature);
  Serial.printf("Humidity: %.2f %%\n", humidity);
  Serial.printf("Soil: %d %%\n", soilPercent);
  Serial.printf("Device1: %s | Device2: %s\n",
                dev1State ? "ON" : "OFF",
                dev2State ? "ON" : "OFF");

  // ===== SEND TO SERVER =====
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;

    String url = String(serverUrl) + "/" +
                 String(temperature, 2) + "/" +
                 String(humidity, 2) + "/" +
                 String(soilPercent) + "/" +
                 String(dev1State ? 1 : 0) + "/" +
                 String(dev2State ? 1 : 0);

    Serial.println("Request: " + url);

    http.begin(url);
    int httpCode = http.GET();

    if (httpCode == 200) {
      Serial.println("Data sent OK");
    } else {
      Serial.printf("HTTP error: %d\n", httpCode);
    }

    http.end();
  }

  delay(5000);
}
