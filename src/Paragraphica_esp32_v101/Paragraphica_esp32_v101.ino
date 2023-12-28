// Pargarphica 2.0
// made for to run on a ESP32-S3 DevKit-1
// use board: ESP32S3 Dev Module 
// http://192.168.4.1

#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h> // For hosting a Access Point
#include <vector>
#include <HTTPClient.h> // For requesting GET requests
#include <WiFiClient.h>
#include <ArduinoJson.h> // For parsing and creating JSON payloads
#include <SPI.h>
#include "esp_task_wdt.h"
#include <TinyGPSPlus.h>
#include <HardwareSerial.h>
#include <map>
#include <Preferences.h> // to store SSID and password, in the non-volatile storage
#include <Adafruit_GFX.h> // display
#include <Adafruit_ILI9341.h> // display
#include <SD.h>

//                       ESP32-S3 DevKit-1
//                      +-----------------+
//                      | 3v3         GND |
//                      | 3v3          TX | -- RX GPS 
//                      | RST          RX | -- TX GPS
//     Button (Left) -- | 4             1 | -- Button (Right)
//             Pot 1 -- | 5             2 | -- TFT DC
//             Pot 2 -- | 6            42 |
//             Pot 3 -- | 7            41 | 
//             SD CS -- | 15           40 | 
//                      | 16           39 |
//                      | 17           38 |
//                      | 18           37 | -- TFT MISO
//                      | 8            36 | -- TFT CLK
//                      | 3            35 | -- TFT MOSI
//                      | 46            0 |
//                      | 9            45 |
//                      | 10           48 |
//           SD_MOSI -- | 11           47 | 
//            SD_CLK -- | 12           21 | -- TFT CS
//           SD_MISO -- | 13           20 | X
//             SD_CD -- | 14           19 | X
//                      | 5v          GND |
//                      | GND         GND |
//                      +-----------------+

const long updateInterval = 20000;  // Scan every 20 seconds
bool cameraReady = false;

// NETWORK SETTINGS
// ========================================================================
// Acces Point Wifi settings
const char *apSSID = "Paragraphica";
const char *apPASSWORD = "starmole"; // you can leave it blank for an open network

// Paragraphica API connection
const char *API_URL = "http://92.242.187.242:5000/api";
const char *API_KEY = "234f7855xitxrB6960Pp4c5M95fb6b08f91a33g"; // Replace this with your actual API key

const char *HANDSHAKE_URL = "http://92.242.187.242:5000/handshake";

String ssidList;
unsigned long lastScanTime = 0; 

AsyncWebServer server(80);
Preferences preferences;

// GPS LOCATION SETTINGS
// ========================================================================
// Hardwhere tested: Seed Studio Groov Air530
const int TX_PIN = 43;
const int RX_PIN = 44;
float lat;
float lng;
TinyGPSPlus gps;
HardwareSerial GPS_Serial(1); // Using UART1. Change the number if using another UART.
bool gpsFix = false; // flag to indicate if GPS has a fix

// Pots to GPIO analouge pins
// ========================================================================
const int potPin1 = 34;
const int potPin2 = 35;
const int potPin3 = 32;

String options1[] = {"0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"};
String options2[] = {"photography", "old analogue", "oil painting", "watercolor painting", "pencil sketch"};
String options3[] = {"1900", "1950", "1960", "1970", "1980", "1990", "2000", "2010"};
 
String selectedOption1 = "";
String selectedOption2 = "";
String selectedOption3 = "";

// Buttons
// ========================================================================
const int buttonPin1 = 1; // right
const int buttonPin2 = 0; // left
const int buttonPin3 = 42; // mode
const int buttonPin4 = 5; // trigger

bool wasButton1Pressed = false;
bool wasButton2Pressed = false;
bool wasButton3Pressed = false;
bool wasButton4Pressed = false;

const long debounceDelay = 50;  // Debounce time in milliseconds

// Display
// ========================================================================
int currentPage = 1;

const int TFT_CS = 21; // CS
const int TFT_DC = 2; // D/C
const int TFT_MOSI = 35; // MOSI
const int TFT_CLK = 36; // CLOCK
const int TFT_MISO = 37; // MISO
const int TFT_RST = 38; // RESET
const int TFT_LITE = 39; // Backlight Controle

//Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC);
Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_MOSI, TFT_CLK, TFT_RST, TFT_MISO);

// SD Card
// ========================================================================
// aidafruit 4
bool sdCardInitialized = false;
const int SD_CS = 15; // CS
const int SD_CLK = 12; // CLOCK
const int SD_MOSI = 11; // MOSI
const int SD_MISO = 10; // MISO
const int SD_CD = 14;// Card Detect

// BIT MAP images
// ========================================================================
const uint16_t qrCodeBitmap[] = {
  // ... byte array data ...
};

struct Replacement {
    String placeholder;
    String value;
};

void setup()
{
    Serial.begin(115200);

    // Set device as a Wi-Fi Access Point
    WiFi.softAP(apSSID, apPASSWORD);
    Serial.print("Access Point IP: ");
    Serial.println(WiFi.softAPIP());

    // Assign pins for display and turn backlight on
    pinMode(TFT_LITE, OUTPUT);
    backlightOn();

    if(connectUsingStoredWifi()) {
      Serial.println("Connected to stored Wifi");
    }else{
      Serial.println("Did not conenect to stored Wifi");
    }

    // start Access Point
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        Serial.println("User requesting Access Point");
        String error = "";
        String success = "";
        
        Replacement replacements[] = {
            {"{{error}}", error},
            {"{{success}}", success},
            {"{%SSID_LIST%}", ssidList}
        };
        
        String form = getForm(replacements, 3);
        request->send(200, "text/html", form); 
    });

    server.on("/", HTTP_POST, [](AsyncWebServerRequest *request){ 
        request->redirect("/"); 
    });

    server.on("/setup", HTTP_POST, [](AsyncWebServerRequest *request) {
        String ssid = request->arg("ssid");
        String password = request->arg("password");

        connectToWiFi(ssid.c_str(), password.c_str());

        String error = "";
        String success = "";

        if (WiFi.status() == WL_CONNECTED) {
            success = "Connected successfully!";
        } else {
            error = "Failed to connect.";
        }

        Replacement replacements[] = {
            {"{{error}}", error},
            {"{{success}}", success},
            {"{%SSID_LIST%}", ssidList}
        };

        String form = getForm(replacements, 3);
        request->send(200, "text/html", form); 
    });
  
    // Start server
    server.begin();

    // initaiate buttons
    pinMode(buttonPin1, INPUT_PULLUP);
    pinMode(buttonPin2, INPUT_PULLUP);
    pinMode(buttonPin3, INPUT_PULLUP);
    pinMode(buttonPin4, INPUT_PULLUP);

    // Start the GPS hardware serial.
    GPS_Serial.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN); // Replace RX_PIN and TX_PIN with your RX and TX pins.
    delay(500);
    
    // set SD card pin 
    pinMode(SD_CD, INPUT_PULLUP);

    backlightOn();
    tft.begin();
    tft.setRotation(1);
    tft.fillScreen(ILI9341_BLACK);
    update();
    
}

void loop()
{   
    // every 60 secounds scan the network for SSID's
    unsigned long currentMillis = millis();
    if (currentMillis - lastScanTime > updateInterval) {
        update();
        lastScanTime = currentMillis;
    }

    // read potential meters
    selectedOption1 = readOptionFromPot(potPin1, options1, sizeof(options1) / sizeof(options1[0]));
    selectedOption2 = readOptionFromPot(potPin2, options2, sizeof(options2) / sizeof(options2[0]));
    selectedOption3 = readOptionFromPot(potPin3, options3, sizeof(options3) / sizeof(options3[0]));

    // read buttons
    checkButtonPress(buttonPin1, wasButton1Pressed, button1Logic);
    checkButtonPress(buttonPin2, wasButton2Pressed, button2Logic);
    checkButtonPress(buttonPin3, wasButton3Pressed, button3Logic);
    checkButtonPress(buttonPin4, wasButton4Pressed, button4Logic);

    delay(10);
}

void update(){
  Serial.println("Update ----------------");

  connectUsingStoredWifi();

  if (WiFi.status() != WL_CONNECTED) {
    generateSSIDList(); // stores the list in global variable
  }
  getLocation();
  checkSDCard();
  updateHeader(isConnectedToWiFi(), lat, lng, currentPage, sdCardInitialized); // updates the screen header info
  updateScreenByMode(currentPage);
  
  Serial.print("GPS Status: ");
  Serial.print(lat, 6);
  Serial.print(", ");
  Serial.println(lng, 6);
  Serial.print("Wifi Status: ");
  Serial.println(isConnectedToWiFi());

}

// BUTTONS
void button1Logic() {
    Serial.println("Button 1 Pressed");
    // Add more code specific to Button 1 here
}

void button2Logic() {
    Serial.println("Button 2 Pressed");
    // Add more code specific to Button 2 here
}

void button3Logic() {
    Serial.println("Button 3 Pressed");
    // Add more code specific to Button 3 here
}

void button4Logic() {
    Serial.println("Button 4 Pressed");
    triggerButtonFunction();
    // Add more code specific to Button 4 here
}




void connectToWiFi(const char *ssid, const char *password)
{
    WiFi.begin(ssid, password);

    uint8_t retries = 15;
    while (WiFi.status() != WL_CONNECTED && retries--)
    {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("Connected to WiFi");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());

        preferences.begin("wifi", false);
        preferences.putString("SSID", ssid);
        preferences.putString("Password", password);
        preferences.end();

        // turn AP network off for 10 secounds then back on 
    }
    else
    {
        Serial.println("Failed to connect to WiFi");
        // Reboot or handle failure here
    }
}

bool isConnectedToWiFi() {
    return WiFi.status() == WL_CONNECTED;
}

bool connectUsingStoredWifi() {
    preferences.begin("wifi", false);
    String storedSSID = preferences.getString("SSID", "");
    String storedPassword = preferences.getString("Password", "");
    preferences.end();

    if (storedSSID != "") {
        WiFi.begin(storedSSID.c_str(), storedPassword.c_str());

        // Wait for connection or a timeout
        unsigned long startTime = millis();
        while (WiFi.status() != WL_CONNECTED && millis() - startTime < 5000) {
            delay(100);
        }

        if (WiFi.status() == WL_CONNECTED) {
            return true; // Successful connection using stored credentials
        }
    }

    return false; // Either no stored credentials or failed to connect using them
}

bool isServerRunning() {
    HTTPClient handshakeHttp;
    handshakeHttp.begin(HANDSHAKE_URL);
    int handshakeCode = handshakeHttp.GET();
    handshakeHttp.end();

    if (handshakeCode == HTTP_CODE_OK) {
        Serial.println("Server is up!");
        return true;
    } else {
        Serial.println("Server down or handshake failed.");
        return false;
    }
}

String createJsonPayload() {
    StaticJsonDocument<200> doc;
    JsonObject location = doc.createNestedObject("location");
    location["lat"] = String(lat, 6);
    location["lon"] = String(lng, 6);

    doc["image_strength"] = selectedOption1;
    doc["style"] = selectedOption2;
    doc["year"] = selectedOption3;

    String jsonPayload;
    serializeJson(doc, jsonPayload);
    return jsonPayload;
}

void triggerButtonFunction() {   
    if (lat == 0) {
        Serial.println("Waiting for GPS Signal...");
        return;
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Not connected to a network!");
        return;
    }
    
    if (!isServerRunning()) return;

    HTTPClient http;
    http.begin(API_URL);
    http.setTimeout(40000);  // set timeout to 40 seconds
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-KEY", API_KEY);

    String jsonPayload = createJsonPayload();
    int httpCode = http.POST(jsonPayload);

    if (httpCode == HTTP_CODE_OK) {
        Serial.println("API Request seccessful");
        processServerResponse(http);
    } else {
        Serial.println("HTTP Request failed. Error: " + String(httpCode));
    }

    http.end();   
}

void processServerResponse(HTTPClient &http) {
    // Parse the JSON payload
    DynamicJsonDocument doc(1024); 
    String payload = http.getString();
    deserializeJson(doc, payload);

    String image_file_path = doc["stability_image"].as<String>();
    String description = doc["description"].as<String>();
    String status_report = doc["status_report"].as<String>();

    String imageFileName = selectedOption1 + "_" + selectedOption2 + "_" + selectedOption3 + "_" + String(lat, 6) + "-" + String(lng, 6) + ".jpg";

    saveImageToSD(image_file_path, imageFileName);

    // Print the extracted data to the Serial monitor for debugging purposes
    Serial.println("Image URL: " + image_file_path);
    Serial.println("Description: " + description);
    Serial.println("Status Report: " + status_report);

    // [TBD]: Display the image and delete from server...
}

void saveImageToSD(String &url, String &imageName)
{   
    if (!sdCardInitialized) {
        Serial.println("SD card not initialized. Skipping save operation.");
        return;
    }

    HTTPClient httpImage;
    httpImage.begin(url);

    int httpCode = httpImage.GET();

    if (httpCode == HTTP_CODE_OK)
    {
        // Open a file to write to
        File file = SD.open(imageName, FILE_WRITE);
        if (!file)
        {
            Serial.println("Failed to open file for writing");
            return;
        }

        // Get the http stream
        WiFiClient &stream = httpImage.getStream();

        // Read from the stream and write to the file
        while (httpImage.connected() && (stream.available() > 0))
        {
            byte buffer[64];  // Buffer to store chunks of data
            int bytesRead = stream.read(buffer, sizeof(buffer));
            file.write(buffer, bytesRead);
        }

        file.close();  // Close the file
        Serial.println("Image saved to SD card successfully");
    }
    else
    {
        Serial.println("Failed to download the image. HTTP Code: " + String(httpCode));
    }

    httpImage.end();
}

void checkSDCard() {
  if (digitalRead(SD_CD) == HIGH) { // This depends on your CD pin's behavior. Use HIGH if it goes HIGH when a card is present.
    if (!sdCardInitialized) {
      if (SD.begin(SD_CS)) {
        Serial.println("SD card initialized successfully");
        sdCardInitialized = true;
      } else {
        Serial.println("Card initialization failed");
        sdCardInitialized = false;
      }
    }else{
      Serial.println("SD inserted");
    }
  } else {
    Serial.println("Card removed");
    sdCardInitialized = false;
    SD.end();  // This closes the SD card connection.
  }
}

String readOptionFromPot(int potPin, String options[], int optionsLength)
{
    int val = analogRead(potPin);
    int index = map(val, 0, 4095, 0, optionsLength - 1); // Map from 12-bit ADC to index
    return options[index];
}

void generateSSIDList() {

    WiFi.disconnect();
    delay(100);
    // Step 1: Scan for networks and log to the serial console.
    int numNetworks = WiFi.scanNetworks(false, true);  // Passive scan, and don't clear results

    if (numNetworks < 0) {
    Serial.print("Error scanning for networks, error code: ");
    Serial.println(numNetworks);
    return;
}

    Serial.print("Network scanned: ");
    Serial.println(numNetworks);

    // Step 2: Populate the SSIDs into a vector, but only if they are not empty.
    std::vector<String> ssids;
    for (int i = 0; i < numNetworks; i++) {
        String ssid = WiFi.SSID(i);
        if (ssid != "") {
            ssids.push_back(ssid);
        }
    }

    // Step 3: Construct the HTML option list and save it to a global variable.
    String listOptions = "";
    for (const auto &ssid : ssids) {
        listOptions += "<option value=\"" + ssid + "\">" + ssid + "</option>";
    }
    ssidList = listOptions;
}

void checkButtonPress(int buttonPin, bool &wasPressed, void (*callback)()) {
    bool isPressed = (digitalRead(buttonPin) == LOW);

    if (isPressed && !wasPressed) {
        // If a callback function is provided, execute it
        if (callback) callback();
    }

    wasPressed = isPressed;
}

void getLocation() {

  // Read data from the GPS module
  while (GPS_Serial.available()) {
    gps.encode(GPS_Serial.read());
  }

  // Check if GPS data is valid
  if (gps.location.isValid()) {
    if (!gpsFix) {  // If it was not previously fixed
      Serial.println("GPS has a fix.");
      gpsFix = true;
    }

    lat = gps.location.lat();
    lng = gps.location.lng();
  } 
  else {
    if (gpsFix) {  // If it was previously fixed
      Serial.println("Lost GPS fix!");
      gpsFix = false;
    } else {
      Serial.println("Waiting for GPS signal...");
    }
  }
}


