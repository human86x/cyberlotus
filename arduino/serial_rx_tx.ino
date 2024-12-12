#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Define the PWM pins and states
const int pwmPins[] = {3, 4, 5, 6, 7, 8, 9, 10, 11};
const int pwmValueOff = 255;  // 5V (transistor off)
const int pwmValueOn = 16;    // ~4.3V (transistor on)

void setup() {
  Serial.begin(9600);
  sensors.begin();
  
  // Initialize PWM pins
  for (int i = 0; i < sizeof(pwmPins) / sizeof(pwmPins[0]); i++) {
    pinMode(pwmPins[i], OUTPUT);
    analogWrite(pwmPins[i], pwmValueOff);  // Ensure pins are off initially
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
