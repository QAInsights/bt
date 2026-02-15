/*
    BLE Device for testing the bt CLI tool
    - Advertises a BLE service with read/write characteristics
    - Displays written values on OLED
    - Allows reading counter value
*/

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1 
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Service and characteristic UUIDs
#define SERVICE_UUID           "89c52e89-c665-4378-a274-e08065ee12e3"
#define WRITE_CHAR_UUID        "16d4d7fa-58a5-4672-b363-d73c680a9f85"
#define READ_CHAR_UUID         "26d4d7fa-58a5-4672-b363-d73c680a9f86"
#define NOTIFY_CHAR_UUID       "36d4d7fa-58a5-4672-b363-d73c680a9f87"

int counter = 0;
String lastWritten = "Ready to receive";
BLECharacteristic *pNotifyChar = nullptr;

class WriteCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    String value = pCharacteristic->getValue();
    if (value.length() > 0) {
      lastWritten = value;
      Serial.print("Written: ");
      Serial.println(value);
      
      // Update OLED
      display.clearDisplay();
      display.setTextSize(1);
      display.setCursor(0, 0);
      display.println("BT Write Received:");
      display.println(value);
      display.println("");
      display.print("Counter: ");
      display.println(counter);
      display.display();
      
      // Send notification
      if (pNotifyChar) {
        pNotifyChar->setValue((uint8_t *)value.c_str(), value.length());
        pNotifyChar->notify();
      }
    }
  }
};

class ReadCallbacks : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic *pCharacteristic) {
    counter++;
    String counterStr = String(counter);
    pCharacteristic->setValue((uint8_t *)counterStr.c_str(), counterStr.length());
    Serial.print("Read: ");
    Serial.println(counterStr);
  }
};

void setup() {
  Serial.begin(115200);
  delay(100);
  
  // Initialize I2C for OLED
  Wire.begin(D4, D5);
  
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("OLED failed"));
    for(;;);
  }
  
  // Show startup message
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("BLE Device Ready");
  display.println("Service: test-ble");
  display.println("");
  display.println("Scanning for bt CLI...");
  display.display();
  
  // Initialize BLE
  BLEDevice::init("test-ble");
  BLEServer *pServer = BLEDevice::createServer();
  
  BLEService *pService = pServer->createService(SERVICE_UUID);
  
  // Write characteristic
  BLECharacteristic *pWriteChar = pService->createCharacteristic(
    WRITE_CHAR_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  pWriteChar->setCallbacks(new WriteCallbacks());
  
  // Read characteristic
  BLECharacteristic *pReadChar = pService->createCharacteristic(
    READ_CHAR_UUID,
    BLECharacteristic::PROPERTY_READ
  );
  pReadChar->setCallbacks(new ReadCallbacks());
  pReadChar->setValue("0");
  
  // Notify characteristic
  pNotifyChar = pService->createCharacteristic(
    NOTIFY_CHAR_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pNotifyChar->addDescriptor(new BLE2902());
  pNotifyChar->setValue("waiting...");
  
  pService->start();
  
  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->start();
  
  Serial.println("BLE advertising started");
}

void loop() {
  delay(1000);
}

