/*
 ESP32 capacitive soil-moisture sensor example.
 Update Wi-Fi credentials and SERVER_URL. Sensor analog output -> GPIO 34.
 This sketch only sends sensor readings; it does not switch a pump.
 Calibrate DRY_RAW/WET_RAW for your sensor. Never connect a pump directly to
 an ESP32 pin. Use properly rated isolated hardware and local safety cutoffs.
*/
#include <WiFi.h>
#include <HTTPClient.h>
const char* WIFI_NAME="YOUR_WIFI_NAME";
const char* WIFI_PASSWORD="YOUR_WIFI_PASSWORD";
const char* SERVER_URL="http://YOUR_SERVER_IP:5000/api/iot/readings";
const int SOIL_PIN=34, ZONE_ID=1;
const int DRY_RAW=3000, WET_RAW=1300; // Example only; calibrate.
float toPercent(int raw){float p=(float)(DRY_RAW-raw)*100.0/(DRY_RAW-WET_RAW);return constrain(p,0,100);}
void setup(){Serial.begin(115200);WiFi.begin(WIFI_NAME,WIFI_PASSWORD);while(WiFi.status()!=WL_CONNECTED){delay(500);Serial.print(".");}Serial.println("Wi-Fi connected");}
void loop(){if(WiFi.status()==WL_CONNECTED){int raw=analogRead(SOIL_PIN);float m=toPercent(raw);HTTPClient http;http.begin(SERVER_URL);http.addHeader("Content-Type","application/json");String body="{\\"zone_id\\":"+String(ZONE_ID)+",\\"moisture\\":"+String(m,1)+",\\"temperature\\":24.0}";int code=http.POST(body);Serial.printf("raw=%d moisture=%.1f%% API=%d\\n",raw,m,code);http.end();}delay(30000);}
