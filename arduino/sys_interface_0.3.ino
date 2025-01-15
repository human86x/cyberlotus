#include <OneWire.h>
#include <DallasTemperature.h>

// Temperature sensor definitions
#define ONE_WIRE_BUS 3 // Updated to pin 3
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Relay definitions (pumps on pins 33-52)
const int pumpPins[] = {33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52};

// Ultrasonic sensor definitions
#define TRIG_PIN 11
#define ECHO_PIN 12

// TDS sensor definitions (used for EC in this case)
#define TDS_SENSOR_PIN A0 // Analog pin for the sensor
#define VREF 5.0          // Reference voltage for Arduino (3.3V or 5V)
#define TDS_FACTOR 0.5    // TDS factor for calculation (not needed for raw EC)

// pH sensor definitions
#define PH_SENSOR_PIN A1 // Analog pin for pH sensor
#define NUM_READINGS 10  // Number of readings for averaging

// Flag to check if a sensor is active
bool isSensorActive = false;

void setup() {
  Serial.begin(9600);
  delay(100);

  // Initialize temperature sensor
  sensors.begin();

  // Initialize pump pins
  for (int i = 0; i < sizeof(pumpPins) / sizeof(pumpPins[0]); i++) {
    pinMode(pumpPins[i], OUTPUT);
    digitalWrite(pumpPins[i], HIGH); // Ensure pumps are off initially for low-level trigger
  }

  // Initialize ultrasonic sensor pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  // Handle commands from serial
  if (Serial.available()) {
    char command = Serial.read();  // Read the command character

    if (command == 'T') {
      sensors.requestTemperatures();
      float temperature = sensors.getTempCByIndex(0);
      Serial.print(temperature);
      Serial.print("\n");
      isSensorActive = true;
    } else if (command == 'L') {
      float distance = getDistance();
      Serial.print(distance);
      Serial.print("\n");
      isSensorActive = true;
    } else if (command == 'D') {
      float ecValue = getECValue();
      Serial.print(ecValue);
      Serial.print("\n");
      isSensorActive = true;
    } else if (command == 'P') {
      float phValue = readPHSensor();
      Serial.print(phValue);
      Serial.print("\n");
      isSensorActive = true;
    } else if (command == 'H') {
      Serial.println("HEARTBEAT");
    } else {
      switch (command) {
        case 'a': controlPump(0); break;
        case 'b': controlPump(1); break;
        case 'c': controlPump(2); break;
        case 'd': controlPump(3); break;
        case 'e': controlPump(4); break;
        case 'f': controlPump(5); break;
        case 'g': controlPump(6); break;
        case 'h': controlPump(7); break;
        case 'i': controlPump(8); break;
        case 'j': controlPump(9); break;
        case 'k': controlPump(10); break;
        case 'l': controlPump(11); break;
        case 'm': controlPump(12); break;
        case 'n': controlPump(13); break;
        case 'o': controlPump(14); break;
        case 'p': controlPump(15); break;
        case 'q': controlPump(16); break;
        case 'r': controlPump(17); break;
        case 's': controlPump(18); break;
        case 't': controlPump(19); break;
        default:
          Serial.println("Invalid command");
          break;
      }
      isSensorActive = false;
    }
  }
}

void controlPump(int pumpIndex) {
  if (pumpIndex < 0 || pumpIndex >= sizeof(pumpPins) / sizeof(pumpPins[0])) {
    Serial.println("Invalid pump index");
    return;
  }

  while (!Serial.available());
  char state = Serial.read();

  if (state == 'o') {
    digitalWrite(pumpPins[pumpIndex], LOW);
    Serial.print("Pump ");
    Serial.print(pumpIndex);
    Serial.println(" ON");
  } else if (state == 'f') {
    digitalWrite(pumpPins[pumpIndex], HIGH);
    Serial.print("Pump ");
    Serial.print(pumpIndex);
    Serial.println(" OFF");
  } else {
    Serial.println("Invalid state command");
  }
}

float getDistance() {
  long duration;
  float distance;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  duration = pulseIn(ECHO_PIN, HIGH);
  distance = (duration * 0.0343) / 2;
  return distance;
}

float getECValue() {
  int analogValue = analogRead(TDS_SENSOR_PIN);
  return analogValue;
}

float readPHSensor() {
  long sum = 0;
  for (int i = 0; i < NUM_READINGS; i++) {
    sum += analogRead(PH_SENSOR_PIN);
    delay(10);
  }
  float analogValue = sum / NUM_READINGS;
  float slope = 0.018;
  float intercept = 7.0;
  float pH = slope * analogValue + intercept;
  return pH;
}