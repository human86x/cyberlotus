#include <OneWire.h>
#include <DallasTemperature.h>

// Temperature sensor definitions
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Relay definitions (pumps on pins 35-51 and 36-20)
const int pumpPins[] = {35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34};

// Ultrasonic sensor definitions
#define TRIG_PIN_1 10
#define ECHO_PIN_1 9
#define TRIG_PIN_2 6
#define ECHO_PIN_2 7
#define TRIG_PIN_3 3
#define ECHO_PIN_3 4
#define TRIG_PIN_4 21
#define ECHO_PIN_4 20

// TDS sensor definitions
#define TDS_SENSOR_PIN A0
#define VREF 5.0
#define ADC_RES 1024.0
#define TDS_FACTOR 0.05

// pH sensor definitions
#define PH_SENSOR_PIN A1
#define NUM_READINGS 10

// Soil moisture sensor definitions
#define SOIL_MOISTURE_PIN A5
const int dryValue = 600;
const int wetValue = 300;

// Function prototypes
void controlPump(char pumpCommand, char state);
void precisePumpDelivery(char pumpCommand, int duration);
void turnOffAllPumps();
float getDistance(int trigPin, int echoPin);
float getECValue();
float readPHSensor();
float getSoilMoisture();

void setup() {
  Serial.begin(9600);
  delay(100);

  sensors.begin();

  for (int i = 0; i < sizeof(pumpPins) / sizeof(pumpPins[0]); i++) {
    pinMode(pumpPins[i], OUTPUT);
    digitalWrite(pumpPins[i], HIGH);
  }

  pinMode(TRIG_PIN_1, OUTPUT);
  pinMode(ECHO_PIN_1, INPUT);
  pinMode(TRIG_PIN_2, OUTPUT);
  pinMode(ECHO_PIN_2, INPUT);
  pinMode(TRIG_PIN_3, OUTPUT);
  pinMode(ECHO_PIN_3, INPUT);
  pinMode(TRIG_PIN_4, OUTPUT);
  pinMode(ECHO_PIN_4, INPUT);

  pinMode(SOIL_MOISTURE_PIN, INPUT);
  pinMode(TDS_SENSOR_PIN, INPUT);
  pinMode(PH_SENSOR_PIN, INPUT);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    // Connection test command (must be first)
    if (command == "PING") {
      Serial.println("PONG");
      return;
    }
    // Temperature reading
    else if (command == "T") {
      sensors.requestTemperatures();
      float temperature = sensors.getTempCByIndex(0);
      Serial.println(temperature);
    }
    // Ultrasonic sensor readings
    else if (command == "F") {
      Serial.println(getDistance(TRIG_PIN_1, ECHO_PIN_1));
    }
    else if (command == "S") {
      Serial.println(getDistance(TRIG_PIN_2, ECHO_PIN_2));
    }
    else if (command == "W") {
      Serial.println(getDistance(TRIG_PIN_3, ECHO_PIN_3));
    }
    else if (command == "C") {
      Serial.println(getDistance(TRIG_PIN_4, ECHO_PIN_4));
    }
    // TDS/EC reading
    else if (command == "D") {
      Serial.println(getECValue());
    }
    // pH reading
    else if (command == "P") {
      Serial.println(readPHSensor());
    }
    // Heartbeat
    else if (command == "H") {
      Serial.println("HEARTBEAT");
    }
    // All pumps off
    else if (command == "X") {
      turnOffAllPumps();
    }
    // Soil moisture
    else if (command == "Q") {
      Serial.println(getSoilMoisture());
    }
    // Simple pump control (2-character commands)
    else if (command.length() == 2) {
      char pumpCommand = command.charAt(0);
      char state = command.charAt(1);
      controlPump(pumpCommand, state);
    }
    // Precise pump timing (command + duration)
    else if (command.length() >= 2 && isDigit(command.charAt(1))) {
      char pumpCommand = command.charAt(0);
      int duration = command.substring(1).toInt();
      precisePumpDelivery(pumpCommand, duration);
    }
    // Invalid command
    else {
      Serial.println("INVALID_CMD");
    }
  }
}

float getSoilMoisture() {
  int moistureValue = analogRead(SOIL_MOISTURE_PIN);
  int moisturePercentage = map(moistureValue, dryValue, wetValue, 0, 100);
  moisturePercentage = constrain(moisturePercentage, 0, 100);
  return moisturePercentage;
}

void controlPump(char pumpCommand, char state) {
  int pumpIndex = -1;

  if (pumpCommand >= 'a' && pumpCommand <= 'z') {
    pumpIndex = pumpCommand - 'a';
  }
  else {
    switch (pumpCommand) {
      case '!': pumpIndex = 26; break;
      case '@': pumpIndex = 27; break;
      case '#': pumpIndex = 28; break;
      case '$': pumpIndex = 29; break;
      case '%': pumpIndex = 30; break;
      case '^': pumpIndex = 31; break;
      case '&': pumpIndex = 32; break;
      case '*': pumpIndex = 33; break;
      case '(': pumpIndex = 34; break;
      case ')': pumpIndex = 35; break;
      case '-': pumpIndex = 36; break;
      case '_': pumpIndex = 37; break;
      case '=': pumpIndex = 38; break;
      case '+': pumpIndex = 39; break;
      case '[': pumpIndex = 40; break;
      case ']': pumpIndex = 41; break;
      case '{': pumpIndex = 42; break;
      case '}': pumpIndex = 43; break;
      case ';': pumpIndex = 44; break;
      case ':': pumpIndex = 45; break;
      case ',': pumpIndex = 46; break;
      case '.': pumpIndex = 47; break;
      default: Serial.println("INVALID_PUMP"); return;
    }
  }

  if (pumpIndex < 0 || pumpIndex >= sizeof(pumpPins) / sizeof(pumpPins[0])) {
    Serial.println("INVALID_PUMP_IDX");
    return;
  }

  if (state == 'o') {
    digitalWrite(pumpPins[pumpIndex], LOW);
    Serial.print("ON_");
    Serial.println(pumpCommand);
  }
  else if (state == 'f') {
    digitalWrite(pumpPins[pumpIndex], HIGH);
    Serial.print("OFF_");
    Serial.println(pumpCommand);
  }
  else {
    Serial.println("INVALID_STATE");
  }
}

void precisePumpDelivery(char pumpCommand, int duration) {
  int pumpIndex = pumpCommand - 'a';

  if (pumpIndex < 0 || pumpIndex >= sizeof(pumpPins) / sizeof(pumpPins[0])) {
    Serial.println("INVALID_PUMP_IDX");
    return;
  }

  if (duration <= 0) {
    Serial.println("INVALID_DURATION");
    return;
  }

  digitalWrite(pumpPins[pumpIndex], LOW);
  Serial.print("ON_");
  Serial.print(pumpCommand);
  Serial.print("_");
  Serial.println(duration);

  delay(duration);
  digitalWrite(pumpPins[pumpIndex], HIGH);
}

void turnOffAllPumps() {
  for (int i = 0; i < sizeof(pumpPins) / sizeof(pumpPins[0]); i++) {
    digitalWrite(pumpPins[i], HIGH);
  }
  Serial.println("ALL_OFF");
}

float getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  return (duration * 0.0343) / 2;
}

float getECValue() {
  int rawValue = analogRead(TDS_SENSOR_PIN);
  float voltage = rawValue * (VREF / ADC_RES);
  return voltage * TDS_FACTOR;
}

float readPHSensor() {
  long sum = 0;
  for (int i = 0; i < NUM_READINGS; i++) {
    sum += analogRead(PH_SENSOR_PIN);
    delay(10);
  }
  return sum / NUM_READINGS;
}