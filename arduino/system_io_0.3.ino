#include <OneWire.h>
#include <DallasTemperature.h>

// Temperature sensor definitions
#define ONE_WIRE_BUS 33 // Updated to pin 33
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Relay definitions
const int relayPins[] = {4, 5, 6, 7, 8, 50, 48}; // Added pin 48 for the new relay

// Ultrasonic sensor definitions
#define TRIG_PIN 9
#define ECHO_PIN 10

// TDS sensor definitions
#define TDS_SENSOR_PIN A0 // Analog pin for the TDS sensor
#define VREF 5.0          // Reference voltage for Arduino (3.3V or 5V)
#define TDS_FACTOR 0.5    // TDS factor for calculation

// Heartbeat interval (in milliseconds)
const unsigned long HEARTBEAT_INTERVAL = 1000; // Send heartbeat every 1 second
unsigned long lastHeartbeatTime = 0;

bool isSensorActive = false;

void setup() {
  Serial.begin(9600);
  delay(100);

  // Initialize temperature sensor
  sensors.begin();

  // Initialize relay pins
  for (int i = 0; i < sizeof(relayPins) / sizeof(relayPins[0]); i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], HIGH); // Ensure relays are off initially for low-level trigger
  }

  // Initialize ultrasonic sensor pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Serial.println("System Initialized");
}

void loop() {
  // Handle commands from serial
  if (Serial.available()) {
    char command = Serial.read();  // Read the command character

    // Stop heartbeat while processing commands
    unsigned long currentTime = millis();

    if (command == 'T') {
      // Handle temperature request
      sensors.requestTemperatures();
      float temperature = sensors.getTempCByIndex(0);
      //Serial.print("Temperature: ");
      Serial.print(temperature);
      //Serial.println(" °C");
      isSensorActive = true;  // Indicate sensor is active
    } else if (command == 'L') {
      // Handle ultrasonic distance request
      float distance = getDistance();
      //Serial.print("Distance: ");
      Serial.print(distance);
      //Serial.println(" cm");
      isSensorActive = true;  // Indicate sensor is active
    } else if (command == 'D') {
      // Handle TDS request
      float tdsValue = getTDSValue();
      //Serial.print("TDS: ");
      Serial.print(tdsValue, 2);
      //Serial.println(" ppm");
      isSensorActive = true;  // Indicate sensor is active
    } else {
      // Handle pin control
      switch (command) {
        case 'a': controlPin(0); break;  // Pin 4
        case 'b': controlPin(1); break;  // Pin 5
        case 'c': controlPin(2); break;  // Pin 6
        case 'd': controlPin(3); break;  // Pin 7
        case 'e': controlPin(4); break;  // Pin 8
        case 'f': controlPin(5); break;  // Pin 50
        case 'g': controlPin(6); break;  // Pin 48 (new relay)
        default:
          Serial.println("Invalid command");
          break;
      }
      isSensorActive = false;  // Reset sensor activity
    }

    // Reset heartbeat interval when a command is processed
    lastHeartbeatTime = currentTime;
  } else {
    // Send heartbeat message at regular intervals if no command is active and no sensor is being read
    unsigned long currentTime = millis();
    if (!isSensorActive && currentTime - lastHeartbeatTime >= HEARTBEAT_INTERVAL) {
      lastHeartbeatTime = currentTime;
      Serial.println("HEARTBEAT");
    }
  }
}

// Function to control relays
void controlPin(int pinIndex) {
  if (pinIndex < 0 || pinIndex >= sizeof(relayPins) / sizeof(relayPins[0])) {
    Serial.println("Invalid pin index");
    return; // Ensure valid pin index
  }

  // Wait for the second character (state: 'o' or 'f')
  while (!Serial.available());
  char state = Serial.read();

  if (state == 'o') {
    digitalWrite(relayPins[pinIndex], LOW); // Activate relay for low-level trigger
    //Serial.print("Relay ");
    Serial.print(pinIndex);
    //Serial.println(" ON");
  } else if (state == 'f') {
    digitalWrite(relayPins[pinIndex], HIGH); // Deactivate relay for low-level trigger
    //Serial.print("Relay ");
    //Serial.print(pinIndex);
    //Serial.println(" OFF");
  } else {
    Serial.println("Invalid state command");
  }
}

// Function to get distance from the ultrasonic sensor
float getDistance() {
  long duration;
  float distance;

  // Send a 10µs HIGH pulse to the Trig pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Measure the time taken by the echo to return
  duration = pulseIn(ECHO_PIN, HIGH);

  // Calculate the distance (speed of sound = 343 m/s)
  distance = (duration * 0.0343) / 2; // Convert to centimeters

  return distance;
}

// Function to get TDS value
float getTDSValue() {
  int analogValue = analogRead(TDS_SENSOR_PIN);
  float voltage = analogValue * (VREF / 1024.0); // Convert ADC value to voltage
  float tdsValue = (133.42 * pow(voltage, 3) - 255.86 * pow(voltage, 2) + 857.39 * voltage) * TDS_FACTOR;

  // Debugging output
  //Serial.print("Analog Value: ");
  //Serial.print(analogValue);
  //Serial.print(" | Voltage: ");
  //Serial.print(voltage, 2);
  //Serial.println(" V");

  return tdsValue;
}
