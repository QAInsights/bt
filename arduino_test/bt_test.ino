/*
 * BLE Test Peripheral for bt.py (with OLED display)
 * 
 * Board: ESP32 (install "esp32" board package in Arduino IDE)
 * Libraries needed:
 *   - Adafruit SSD1306  (Library Manager -> search "Adafruit SSD1306")
 *   - Adafruit GFX      (installed automatically with SSD1306)
 *
 * Wiring (SSD1306 I2C OLED):
 *   SDA -> GPIO 21
 *   SCL -> GPIO 22
 *   VCC -> 3.3V
 *   GND -> GND
 *
 * Usage:
 *   1. Flash this to your ESP32
 *   2. Run: uv run .\bt.py scan
 *   3. Select "BT_Test" from the device list
 *   4. Write a message -> it appears on the OLED
 *   5. Listen -> see tick notifications every 2 seconds
 */

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED config
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_ADDR 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// UUIDs
#define SERVICE_UUID        "89c52e89-c665-4378-a274-e08065ee12e3"
#define CHAR_WRITE_UUID     "16d4d7fa-58a5-4672-b363-d73c680a9f85"
#define CHAR_READ_UUID      "26d4d7fa-58a5-4672-b363-d73c680a9f86"
#define CHAR_NOTIFY_UUID    "36d4d7fa-58a5-4672-b363-d73c680a9f87"

BLEServer* pServer = NULL;
BLECharacteristic* pWriteChar = NULL;
BLECharacteristic* pReadChar = NULL;
BLECharacteristic* pNotifyChar = NULL;

bool deviceConnected = false;
bool oldDeviceConnected = false;
uint32_t counter = 0;
String lastWritten = "hello";
String statusLine = "Waiting...";

unsigned long lastNotifyTime = 0;
const unsigned long NOTIFY_INTERVAL = 2000;

// --- Update OLED display ---
void updateDisplay(String line1, String line2 = "", String line3 = "") {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    
    // Header
    display.setCursor(0, 0);
    display.println("== BT_Test ==");
    display.drawLine(0, 10, SCREEN_WIDTH, 10, SSD1306_WHITE);
    
    // Status
    display.setCursor(0, 14);
    display.println(deviceConnected ? "Connected" : "Advertising...");
    
    // Content lines
    display.setCursor(0, 28);
    display.println(line1);
    
    if (line2.length() > 0) {
        display.setCursor(0, 40);
        display.println(line2);
    }
    
    if (line3.length() > 0) {
        display.setCursor(0, 52);
        display.println(line3);
    }
    
    display.display();
}

// --- Connection callbacks ---
class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println(">> Client connected!");
        updateDisplay("Client connected!");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println(">> Client disconnected.");
        updateDisplay("Disconnected.", "Restarting ads...");
    }
};

// --- Write callback ---
class WriteCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) {
        String value = pCharacteristic->getValue().c_str();
        if (value.length() > 0) {
            Serial.print(">> Received write: ");
            Serial.println(value);
            
            // Store for READ echo
            lastWritten = value;
            pReadChar->setValue(lastWritten.c_str());
            
            // Show on OLED
            updateDisplay("WRITE received:", value);
        }
    }
};

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== BLE Test Peripheral ===");

    // Init OLED
    if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
        Serial.println("OLED init failed!");
    }
    updateDisplay("Starting BLE...");

    // Init BLE
    BLEDevice::init("BT_Test");
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create service
    BLEService* pService = pServer->createService(SERVICE_UUID);

    // WRITE characteristic
    pWriteChar = pService->createCharacteristic(
        CHAR_WRITE_UUID,
        BLECharacteristic::PROPERTY_WRITE
    );
    pWriteChar->setCallbacks(new WriteCallbacks());

    // READ characteristic
    pReadChar = pService->createCharacteristic(
        CHAR_READ_UUID,
        BLECharacteristic::PROPERTY_READ
    );
    pReadChar->setValue(lastWritten.c_str());

    // NOTIFY characteristic
    pNotifyChar = pService->createCharacteristic(
        CHAR_NOTIFY_UUID,
        BLECharacteristic::PROPERTY_NOTIFY
    );
    pNotifyChar->addDescriptor(new BLE2902());

    // Start
    pService->start();
    BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();

    Serial.println("BLE ready! Advertising as 'BT_Test'");
    updateDisplay("Advertising...", "Name: BT_Test");
}

void loop() {
    if (deviceConnected) {
        unsigned long now = millis();
        if (now - lastNotifyTime >= NOTIFY_INTERVAL) {
            lastNotifyTime = now;
            counter++;

            String msg = "tick:" + String(counter);
            pNotifyChar->setValue(msg.c_str());
            pNotifyChar->notify();

            Serial.print("<< Sent notify: ");
            Serial.println(msg);
            
            // Show on OLED
            updateDisplay("NOTIFY sent:", msg, "Last write: " + lastWritten);
        }
    }

    // Handle reconnection
    if (!deviceConnected && oldDeviceConnected) {
        delay(500);
        pServer->startAdvertising();
        Serial.println("Restarted advertising...");
        updateDisplay("Advertising...", "Name: BT_Test");
        oldDeviceConnected = false;
    }

    if (deviceConnected && !oldDeviceConnected) {
        oldDeviceConnected = true;
    }

    delay(10);
}
