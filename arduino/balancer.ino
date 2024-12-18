#include <OneWire.h>
#include <DallasTemperature.h>
#include <HX711_ADC.h>
#if defined(ESP8266) || defined(ESP32) || defined(AVR)
#include <EEPROM.h>
#endif

// Temperature sensor definitions
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// PWM definitions
const int pwmPins[] = {3, 4, 5, 6, 7, 8, 9, 10, 11};
const int pwmValueOff = 255;  // 5V (transistor off)
const int pwmValueOn = 16;    // ~4.3V (transistor on)

// HX711 load cell definitions
const int HX711_dout = 26; // MCU > HX711 DOUT pin
const int HX711_sck = 24;  // MCU > HX711 SCK pin
HX711_ADC LoadCell(HX711_dout, HX711_sck);

// Timing and smoothing variables
unsigned long t = 0;
float previousValue = 0.0;

void setup() {
  Serial.begin(9600);
  delay(100);

  // Initialize temperature sensors
  sensors.begin();
  
  // Initialize PWM pins
  for (int i = 0; i < sizeof(pwmPins) / sizeof(pwmPins[0]); i++) {
    pinMode(pwmPins[i], OUTPUT);
    analogWrite(pwmPins[i], pwmValueOff);  // Ensure pins are off initially
  }

  // Initialize HX711 load cell
  Serial.println("\nStarting load cell...");
  LoadCell.begin();
  LoadCell.setSamplesInUse(40); // Increase averaging for stability

  float calibrationValue = -607.0; // Adjust as per Calibration.ino
  LoadCell.start(2000, true);

  if (LoadCell.getTareTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 wiring and pin designations");
    while (1);
  } else {
    LoadCell.setCalFactor(calibrationValue);
    Serial.println("Load cell startup is complete");
  }
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();  // Read the first command character
    
    if (command == 'R') {
      // Handle temperature request
      sensors.requestTemperatures();
      float temperature = sensors.getTempCByIndex(0);
      Serial.println(temperature);  // Send temperature as a string
    } else if (command == 'W') {
      // Handle weight data request
      handleWeightRequest();
    } else {
      // Handle pin control
      switch (command) {
        case 'a': controlPin(0); break;  // Pin 3
        case 'b': controlPin(1); break;  // Pin 4
        case 'c': controlPin(2); break;  // Pin 5
        case 'd': controlPin(3); break;  // Pin 6
        case 'e': controlPin(4); break;  // Pin 7
        case 'l': controlPin(5); break;  // Pin 8
        case 'g': controlPin(6); break;  // Pin 9
        case 'h': controlPin(7); break;  // Pin 10
        case 'j': controlPin(8); break;  // Pin 11
        default:
          Serial.println("Invalid command");
          break;
      }
    }
  }
}

// Helper function to control pin states
void controlPin(int pinIndex) {
  if (pinIndex < 0 || pinIndex >= sizeof(pwmPins) / sizeof(pwmPins[0])) {
    Serial.println("Invalid pin index");
    return;  // Ensure valid pin index
  }

  // Wait for the second character (state: 'o' or 'f')
  while (!Serial.available());
  char state = Serial.read();

  if (state == 'o') {
    analogWrite(pwmPins[pinIndex], pwmValueOn);  // Activate pin
    Serial.print("Activating transistor on pin ");
    Serial.println(pwmPins[pinIndex]);
  } else if (state == 'f') {
    analogWrite(pwmPins[pinIndex], pwmValueOff);  // Deactivate pin
    Serial.print("Deactivating transistor on pin ");
    Serial.println(pwmPins[pinIndex]);
  } else {
    Serial.println("Invalid state command");
  }
}

// Function to handle weight sensor data
void handleWeightRequest() {
  static boolean newDataReady = 0;
  const int serialPrintInterval = 200; // Print every 200ms

  if (LoadCell.update()) newDataReady = true;

  if (newDataReady && millis() > t + serialPrintInterval) {
    float rawValue = LoadCell.getData();
    float smoothedValue = 0.95 * previousValue + 0.05 * rawValue;
    previousValue = smoothedValue;

    //Serial.print("Load cell raw value: ");
    Serial.print(rawValue);
    //Serial.print(" | Smoothed value: ");
    //Serial.println(smoothedValue);

    newDataReady = 0;
    t = millis();
  }
}
