#include <esp_now.h>
#include <WiFi.h>
#define LED_PIN 2

void setup() {

  pinMode(LED_PIN, OUTPUT);    // LED configuration
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);

}

void loop() {

  Serial.println(WiFi.macAddress());
  delay(1000);
  digitalWrite(LED_PIN, HIGH);
  delay(800);
  digitalWrite(LED_PIN, LOW);
  // Nothing here - ESP-NOW handles reception via callback
  
}
