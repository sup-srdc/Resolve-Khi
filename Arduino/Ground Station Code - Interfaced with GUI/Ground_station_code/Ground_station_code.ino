#include <esp_now.h>
#include <WiFi.h>

#define LED_PIN 2

// Struct for RF Data
typedef struct struct_message {
  unsigned long Header;
  float Temperature;
  float Altitude;
  float Pressure;
  float Heading;
  float Xacc;
  float Yacc;
  float Zacc;
  float Angaccx;
  float Angaccy;
  float Angaccz;
  float Magx;
  float Magy;
  float Magz;
  float Sat;
  float Lat;
  float Long;
  float GPSAlt;
  unsigned long TimeStamp;
} struct_message;

// Create a struct_message called myData
  char macStr[18];

struct_message myData;
unsigned long tic_msg;
unsigned long T_blink = 800;
unsigned int  state_led = 1;


// New ESP-NOW receive callback
void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
  memcpy(&myData, incomingData, sizeof(myData));

  // Get MAC address from recv_info
  snprintf(macStr, sizeof(macStr),
           "%02X:%02X:%02X:%02X:%02X:%02X",
           recv_info->src_addr[0], recv_info->src_addr[1], recv_info->src_addr[2],
           recv_info->src_addr[3], recv_info->src_addr[4], recv_info->src_addr[5]);

  
   Serial.write((uint8_t*)&myData, sizeof(myData));     // Send Data to Matlab

  
  if((millis() - tic_msg) > T_blink){
    state_led = 1 - state_led;
    digitalWrite(LED_PIN, state_led);
    tic_msg = millis();
  }
  // Serial.print("From MAC: ");
  // Serial.println(macStr);

  // Serial.print("/*");
  // Serial.print(myData.Temperature); Serial.print(",");
  // Serial.print(myData.Altitude);    Serial.print(",");
  // Serial.print(myData.Pressure);    Serial.print(",");
  // Serial.print(myData.Heading);     Serial.print(",");
  // Serial.print(myData.Xacc);        Serial.print(",");
  // Serial.print(myData.Yacc);        Serial.print(",");
  // Serial.print(myData.Zacc);        Serial.print(",");
  // Serial.print(myData.Angaccx);     Serial.print(",");
  // Serial.print(myData.Angaccy);     Serial.print(",");
  // Serial.print(myData.Angaccz);     Serial.print(",");
  // Serial.print(myData.Magx);        Serial.print(",");
  // Serial.print(myData.Magy);        Serial.print(",");
  // Serial.print(myData.Magz);        Serial.print(",");
  // Serial.print(myData.Sat);         Serial.print(",");
  // Serial.print(myData.Lat);         Serial.print(",");
  // Serial.print(myData.Long);        Serial.print(",");
  // Serial.print(myData.GPSAlt);
  // Serial.print("*/\n");



}

void setup() {

    // Buzzer configuration
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);
  delay(200);
  digitalWrite(LED_PIN, LOW);


  Serial.begin(115200);

  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    //Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Register receive callback
  esp_now_register_recv_cb(OnDataRecv);

  // Serial.println("Receiver ready...");

  // myData.Temperature = 1;
  // myData.Altitude =2;
  // myData.Pressure = 3;
  // myData.Heading = 4;
  // myData.Xacc = 5;
  // myData.Yacc = 6;
  // myData.Zacc = 7;
  // myData.Angaccx = 8;
  // myData.Angaccy = 9;
  // myData.Angaccz = 10;
  // myData.Magx = 11;
  // myData.Magy= 12;
  // myData.Magz= 13;
  // myData.Sat =14;
  // myData.Lat= 15;
  // myData.Long =16;
  // myData.GPSAlt = 17;

  // while(1){

  //  Serial.write((uint8_t*)&myData, sizeof(myData));
  //   delay(20);
  // }

}

void loop() {
  //   snprintf(macStr, sizeof(macStr),
  //          "%02X:%02X:%02X:%02X:%02X:%02X",
  //          recv_info->src_addr[0], recv_info->src_addr[1], recv_info->src_addr[2],
  //          recv_info->src_addr[3], recv_info->src_addr[4], recv_info->src_addr[5]);

  // Serial.write(macStr);
  // delay(1000);
  // Nothing here - ESP-NOW handles reception via callback
}
