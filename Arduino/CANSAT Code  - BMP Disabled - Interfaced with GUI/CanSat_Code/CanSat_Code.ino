#include <NMEAGPS.h>
#include <HardwareSerial.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include <Adafruit_BMP085.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <WiFi.h>
#include <MechaQMC5883.h>



#define BAUDRATE 115200
#define SET   1
#define RESET 0
#define DELAY_AFTER_WIRED_TX   3
#define DELAY_AFTER_WIFI_TX    3


// Configure Communication Channel (wired vs wireless), Sensors to poll, and their poll periods

  uint8_t flag_Wifi_Comm = SET;              // SET --> Wifi Transmission, RESET -->Serial Transmission on selected COM port
  
  uint8_t flag_send_full_sensor_data = SET;
  uint8_t flag_read_MPU      = SET;
  uint8_t flag_read_Mag      = SET;
  uint8_t flag_read_GPS      = SET;
  uint8_t flag_read_Temp     =  SET;
  uint8_t flag_read_Alt      =  SET;
  uint8_t flag_read_Pressure = SET;

  uint8_t flag_disableBMP    = SET;       // Enable/Disable BMP

  unsigned long sent_pkt_count, dropped_pkt_count, tic_status_msg, toc_status_msg, toc;
  unsigned long tic_env, tic_Alt, tic_GPS;
  unsigned long T_env = 2000, T_Alt = 10, T_GPS = 1000, T_status_msg;
  uint8_t ref_alt = 10;                   // Lahore's Altitude with reference to Sea Level




// Sensor objects
Adafruit_MPU6050 mpu;
Adafruit_BMP085 bmp;
MechaQMC5883 qmc;

float seaLevelPressure, baseLinePressure;

// GPS objects
NMEAGPS gps;
gps_fix fix;
HardwareSerial gpsSerial(2); // UART2: RX=16, TX=17

// SD card chip select (use correct pin for your module)
#define SD_CS 5
File kmlFile;
unsigned long lastSaveTime = 0;
int fileIndex = 0; // counter for filenames
bool sdCardAvailable = false; // Flag to track SD card status

/*----------------------------------WIFI Starts-------------------------------------------*/
//uint8_t broadcastAddress[] = {0x28, 0x56, 0x2F, 0x49, 0xB1, 0x48}; //28:56:2f:49:b1:48
uint8_t broadcastAddress[] = {0x44, 0x1D, 0x64, 0xF2, 0xD2, 0xE0};  //gs1
//struct for RF Data
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

typedef struct imu_message {
  float Xacc;
  float Yacc;
  float Zacc;
  float Angaccx;
  float Angaccy;
  float Angaccz;
  float Magx;
  float Magy;
  float Magz;
 } IMU_reading_m;




struct_message myData;
IMU_reading_m imu_reading;
esp_now_peer_info_t peerInfo;


// callback when data is sent
// void OnDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {       // On some platforms
//   //Serial.print("\r\nLast Packet Send Status:\t");
//   //Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
// }

// void OnDataSent(const esp_now_send_info_t *tx_info, esp_now_send_status_t status) {   // On other platforms
//   Serial.printf("Callback Successfully Called \n");
// }

wifi_interface_t current_wifi_interface;
/*----------------------------------WIFI Ends-------------------------------------------*/

/*--------------------------------SD CARD Functions-----------------------------------------*/
void readFile(fs::FS &fs, const char * path) {
  Serial.printf("Reading file: %s\n", path);
  File file = fs.open(path);
  if (!file) {
    Serial.println("Failed to open file for reading");
    return;
  }
  while (file.available()) {
    Serial.write(file.read());
  }
  file.close();
}

void writeFile(fs::FS &fs, const char * path, const char * message) {
  Serial.printf("Writing file: %s\n", path);
  File file = fs.open(path, FILE_WRITE);
  if (!file) {
    Serial.println("Failed to open file for writing");
    return;
  }
  if (file.print(message)) {
    Serial.println("File written");
  } else {
    Serial.println("Write failed");
  }
  file.close();
}

void appendFile(fs::FS &fs, const char * path, String message) {
  File file = fs.open(path, FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open file for appending");
    return;
  }
  if (file.print(message)) {
    // Success message commented out to reduce serial clutter
    // Serial.println("Message appended");
  } else {
    Serial.println("Append failed");
  }
  file.close();
}

void deleteFile(fs::FS &fs, const char * path) {
  Serial.printf("Deleting file: %s\n", path);
  if (fs.remove(path)) {
    Serial.println("File deleted");
  } else {
    Serial.println("Delete failed");
  }
}


/*--------------------------------KML File Functions-----------------------------------------*/
// Function to start a new KML file
void startNewKML() {
  if (!sdCardAvailable) return;
  
  if (kmlFile) {
    // close previous file with footer
    kmlFile.println("</coordinates>");
    kmlFile.println("</LineString>");
    kmlFile.println("</Placemark>");
    kmlFile.println("</Document>");
    kmlFile.println("</kml>");
    kmlFile.flush();
    kmlFile.close();
  }

  // create a new file with unique name
  String filename = "/gps_" + String(fileIndex++) + ".kml";
  kmlFile = SD.open(filename.c_str(), FILE_WRITE);
  
  if (kmlFile) {
    Serial.print("New file created: ");
    Serial.println(filename);
    
    // Write KML header
    kmlFile.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
    kmlFile.println("<kml xmlns=\"http://www.opengis.net/kml/2.2\">");
    kmlFile.println("<Document>");
    kmlFile.println("<name>GPS Path</name>");
    kmlFile.println("<Placemark>");
    kmlFile.println("<LineString>");
    kmlFile.println("<tessellate>1</tessellate>");
    kmlFile.println("<coordinates>");
    kmlFile.flush();
  } else {
    Serial.println("Failed to create new KML file!");
  }
}

void setup() {
  Serial.begin(BAUDRATE);
  gpsSerial.begin(9600, SERIAL_8N1, 16, 17); // Initialize GPS serial

  // Buzzer configuration
  pinMode(4, OUTPUT);
  digitalWrite(4, HIGH);
  delay(200);
  digitalWrite(4, LOW);


  // BMP180 configuration
  if(flag_disableBMP == RESET){

    if (!bmp.begin()) {
      Serial.println("Could not find a valid BMP085 sensor, check wiring!");
      while (1) {}
    }
      //seaLevelPressure = bmp.readPressure();
    seaLevelPressure = bmp.readSealevelPressure(ref_alt);  // Lahore's altitude with respect to sealevel, this would give extrapolated seaLevel Pressure
    Serial.println("Sea level pressure: ");
    Serial.println(seaLevelPressure);

    baseLinePressure = 0;                            // Calculations of baseline pressure for relative altitude calculation 
    for (int i = 0; i < 5; i++) {
      baseLinePressure += bmp.readPressure();
      delay(50);
    }
    baseLinePressure = baseLinePressure/5;

  }

  Wire.begin();
  //compass.init();
  qmc.init();
  Serial.println("QMC5883L Compass with Calibration (µT output)");





  // SD card configuration - Modified to handle mount failures
  Serial.println("Initializing SD card...");
  if (!SD.begin(SD_CS)) {
    Serial.println("Card Mount Failed - Continuing without SD card");
    sdCardAvailable = false;
  } else {
    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
      Serial.println("No SD card attached - Continuing without SD card");
      sdCardAvailable = false;
    } else {
      sdCardAvailable = true;
      Serial.print("SD Card Type: ");
      if (cardType == CARD_MMC) {
        Serial.println("MMC");
      } else if (cardType == CARD_SD) {
        Serial.println("SDSC");
      } else if (cardType == CARD_SDHC) {
        Serial.println("SDHC");
      } else {
        Serial.println("UNKNOWN");
      }
      
      uint64_t cardSize = SD.cardSize() / (1024 * 1024);
      Serial.printf("SD Card Size: %lluMB\n", cardSize);
      
      // Only try to write file if SD card is available
      if (sdCardAvailable) {
        writeFile(SD, "/sensor_data.txt", "Xacc,Yacc,Zacc,Angaccx,Angaccy,Angaccz,Magx,Magy,Magz,Temperature,Altitude,Heading,Sat,Lat,Long,GPSAlt\n");
        
        Serial.printf("Total space: %lluMB\n", SD.totalBytes() / (1024 * 1024));
        Serial.printf("Used space: %lluMB\n", SD.usedBytes() / (1024 * 1024));
      }
    }
  }

  // MPU6050 configuration
  Serial.println("Adafruit MPU6050 test!");
  
  // Try to initialize!
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  
  Serial.println("MPU6050 Found!");
  mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
  
  Serial.print("Accelerometer range set to: ");
  switch (mpu.getAccelerometerRange()) {
    case MPU6050_RANGE_2_G:
      Serial.println("+-2G");
      break;
    case MPU6050_RANGE_4_G:
      Serial.println("+-4G");
      break;
    case MPU6050_RANGE_8_G:
      Serial.println("+-8G");
      break;
    case MPU6050_RANGE_16_G:
      Serial.println("+-16G");
      break;
  }
  
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  Serial.print("Gyro range set to: ");
  switch (mpu.getGyroRange()) {
    case MPU6050_RANGE_250_DEG:
      Serial.println("+- 250 deg/s");
      break;
    case MPU6050_RANGE_500_DEG:
      Serial.println("+- 500 deg/s");
      break;
    case MPU6050_RANGE_1000_DEG:
      Serial.println("+- 1000 deg/s");
      break;
    case MPU6050_RANGE_2000_DEG:
      Serial.println("+- 2000 deg/s");
      break;
  }
  mpu.setFilterBandwidth(MPU6050_BAND_184_HZ);
  
  Serial.print("Filter bandwidth set to: ");
  switch (mpu.getFilterBandwidth()) {
    case MPU6050_BAND_260_HZ:
      Serial.println("260 Hz");
      break;
    case MPU6050_BAND_184_HZ:
      Serial.println("184 Hz");
      break;
    case MPU6050_BAND_94_HZ:
      Serial.println("94 Hz");
      break;
    case MPU6050_BAND_44_HZ:
      Serial.println("44 Hz");
      break;
    case MPU6050_BAND_21_HZ:
      Serial.println("21 Hz");
      break;
    case MPU6050_BAND_10_HZ:
      Serial.println("10 Hz");
      break;
    case MPU6050_BAND_5_HZ:
      Serial.println("5 Hz");
      break;
  }

  

  // Wifi configuration
  WiFi.mode(WIFI_STA);
  if (esp_wifi_set_protocol(current_wifi_interface, WIFI_PROTOCOL_LR) != ESP_OK) {
    Serial.println("Error initializing WIFI LR");
    return;
  }
  
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  
  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  
  // Once ESPNow is successfully Init, we will register for Send CB to get the status of Trasnmitted packet
  // esp_now_register_send_cb(OnDataSent);
  
  // Register peer
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  
  // Add peer
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }



  // Start first KML file for GPS data (only if SD card is available)
  if (sdCardAvailable) {
    startNewKML();
  }
  lastSaveTime = millis();
  delay(4000);


  sent_pkt_count = 0;
  dropped_pkt_count = 1;
  tic_status_msg = millis();
  tic_env = millis();
  tic_Alt = millis();
  tic_GPS = millis();
  
}

void loop() {

  // 1- mpu6050 gets data
  sensors_event_t a, g, temp;
  myData.TimeStamp = millis();
  if(flag_read_MPU){
    mpu.getEvent(&a, &g, &temp);

    imu_reading.Xacc = a.acceleration.x;
    imu_reading.Yacc = a.acceleration.y;
    imu_reading.Zacc = a.acceleration.z;
    imu_reading.Angaccx =  g.gyro.x;
    imu_reading.Angaccy =  g.gyro.y;
    imu_reading.Angaccz =  g.gyro.z;

    myData.Xacc = a.acceleration.x;
    myData.Yacc = a.acceleration.y;
    myData.Zacc = a.acceleration.z;
    myData.Angaccx =  g.gyro.x;
    myData.Angaccy =  g.gyro.y;
    myData.Angaccz =  g.gyro.z;
    //delay(1);
  }


  // 2---- Magnetometer
  if(flag_read_Mag){

    uint16_t x, y, z;
    int16_t x_, y_, z_;
    int a;
    float mx, my, mz, m;
    float heading;
    
    qmc.read(&x, &y, &z, &a);
    
    x_ = (int16_t) x;
    y_ = (int16_t) y;
    z_ = (int16_t) z;

    mx = x_ * 0.008333;
    my = y_ * 0.008333;
    mz = z_ * 0.008333;
    m = sqrt (mx*mx + my* my + mz* mz);
    heading = atan2((float)my, (float)mx) * 180.0 / PI;

    //  Serial.print("X: "); Serial.print( mx);
    //  Serial.print("  Y: "); Serial.print(my);
    //  Serial.print("  Z: "); Serial.print(mz);
    //  Serial.print("  Mag: "); Serial.print(m);
    // Serial.print("  Heading: "); Serial.print(a);
    // Serial.print("  Heading_local: "); Serial.print(heading);
    // Serial.println("°");



    myData.Magx = mx;
    myData.Magy = my;
    myData.Magz = mz;


    myData.Heading = heading;

      // Convert heading to cardinal direction
    String direction;
    if (heading >= 337.5 || heading < 22.5)  direction = "N";
    else if (heading >= 22.5 && heading < 67.5)  direction = "NE";
    else if (heading >= 67.5 && heading < 112.5) direction = "E";
    else if (heading >= 112.5 && heading < 157.5) direction = "SE";
    else if (heading >= 157.5 && heading < 202.5) direction = "S";
    else if (heading >= 202.5 && heading < 247.5) direction = "SW";
    else if (heading >= 247.5 && heading < 292.5) direction = "W";
    else if (heading >= 292.5 && heading < 337.5) direction = "NW";
  }


  // 3 --- bmp Reading
  if (flag_disableBMP == RESET){
    toc = millis();
    if( (toc - tic_env) > T_env){
      if(flag_read_Temp )      myData.Temperature = bmp.readTemperature();
      if(flag_read_Pressure )  myData.Pressure    = bmp.readPressure();
      tic_env = toc;
    }
    

    //  4 ---- Alt Reading
    toc = millis();
    if( (toc - tic_Alt) > T_Alt){
        if(flag_read_Alt )       myData.Altitude    = bmp.readAltitude(seaLevelPressure);
        tic_Alt = toc;
    }
  }
  else{          // Dummp Values for BMP
    myData.Temperature = 21;
    myData.Pressure    =  101325;
     myData.Altitude   =  10.1 ;

  }
  

  //  5 ----  GPS get data
  toc = millis();
  if( (toc - tic_GPS) > T_GPS){
  if(flag_read_GPS){
    bool newGPSData = false;
    while (gps.available(gpsSerial)) {
        fix = gps.read();
        newGPSData = true;
        if (fix.valid.location) {
          myData.Lat = fix.latitude();
          myData.Long = fix.longitude();
        }
        if (fix.valid.altitude) {
          myData.GPSAlt = fix.altitude();
        }
        if (fix.valid.satellites) {
          myData.Sat = fix.satellites;
        }
        else{
          myData.Sat = 0;
        }
      }
      //Serial.println("Tried to Read GPS data "); ;
    }
    tic_GPS = toc;
  }

  // 6-----  Send Packet 
  myData.Header = 2864434397;
    if(flag_Wifi_Comm == SET){                  // Send data over Wifi via ESP-NOW
        esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *) &myData, sizeof(myData));
        toc_status_msg = millis();
        if (result == ESP_OK) {
          sent_pkt_count++;
          if((toc_status_msg - tic_status_msg) > 1000){    // print every one second
            Serial.print("Sent with success:        Packets Sent = "); Serial.print(sent_pkt_count); Serial.print(" -- Dropped = "); Serial.println(dropped_pkt_count);
            tic_status_msg = toc_status_msg;
          } 
        }else {
          dropped_pkt_count++;
          if((toc_status_msg - tic_status_msg) > 1000){
            Serial.println("Error sending the data: Packets Sent = "); Serial.print(sent_pkt_count); Serial.print(" -- Dropped = "); Serial.println(dropped_pkt_count); 
             tic_status_msg = toc_status_msg;
          }
        }
        delay(DELAY_AFTER_WIRED_TX) ;
    }       
    else{                                   // Send Data Over UART
     if(flag_send_full_sensor_data == SET)
        Serial.write((uint8_t*)&myData, sizeof(myData));
      else
        Serial.write((uint8_t*)&imu_reading, sizeof(imu_reading));
      
      delay(DELAY_AFTER_WIRED_TX);            // Wait time for Transferring 36 bytes at 115200 is 2.6ms

    }
 


  // 7------- Buzzer decision
    if (myData.Altitude <= 1) // THIS SHOULD BE CHANGED BASED ON THE LOCATION
    {
      digitalWrite(4, LOW);
      //Serial.print("Buzzer On");
    } else {
      digitalWrite(4, LOW);
      //Serial.print("Buzzer Off");
    }
}