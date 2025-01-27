#include <OneWire.h>
#include <DallasTemperature.h>

// Temperature sensor definitions
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// Relay definitions (pumps on pins 36-52)
const int pumpPins[] = {35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51};

// Ultrasonic sensor definitions
#define TRIG_PIN_1 9
#define ECHO_PIN_1 8
#define TRIG_PIN_2 6
#define ECHO_PIN_2 7
#define TRIG_PIN_3 3
#define ECHO_PIN_3 4

// TDS sensor definitions
#define TDS_SENSOR_PIN A0
#define VREF 5.0
#define TDS_FACTOR 0.5

// pH sensor definitions
#define PH_SENSOR_PIN A1
#define NUM_READINGS 10

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
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');

    if (command == "T") {
      sensors.requestTemperatures();
      float temperature = sensors.getTempCByIndex(0);
      Serial.println(temperature);
    } else if (command == "L1") {
      Serial.println(getDistance(TRIG_PIN_1, ECHO_PIN_1));
    } else if (command == "L2") {
      Serial.println(getDistance(TRIG_PIN_2, ECHO_PIN_2));
    } else if (command == "L3") {
      Serial.println(getDistance(TRIG_PIN_3, ECHO_PIN_3));
    } else if (command == "D") {
      Serial.println(getECValue());
    } else if (command == "P") {
      Serial.println(readPHSensor());
    } else if (command == "H") {
      Serial.println("HEARTBEAT");
    } else if (command == "X") {
      turnOffAllPumps();
    } else if (command.length() == 2) {
      char pumpCommand = command.charAt(0);
      char state = command.charAt(1);
      controlPump(pumpCommand, state);
    } else if (command.length() >= 2 && isDigit(command.charAt(1))) {
      char pumpCommand = command.charAt(0);
      int duration = command.substring(1).toInt(); // Extract duration as an integer
      precisePumpDelivery(pumpCommand, duration);
    } else {
      Serial.println("Invalid command");
    }
  }
}

void controlPump(char pumpCommand, char state) {
  int pumpIndex = pumpCommand - 'a';

  if (pumpIndex < 0 || pumpIndex >= sizeof(pumpPins) / sizeof(pumpPins[0])) {
    Serial.println("Invalid pump index");
    return;
  }

  if (state == 'o') {
    digitalWrite(pumpPins[pumpIndex], LOW);
    Serial.print("ON_");
    Serial.println(pumpCommand);
  } else if (state == 'f') {
    digitalWrite(pumpPins[pumpIndex], HIGH);
    Serial.print("OFF_");
    Serial.println(pumpCommand);
  } else {
    Serial.println("Invalid state command");
  }
}

void precisePumpDelivery(char pumpCommand, int duration) {
  int pumpIndex = pumpCommand - 'a'; // Calculate the pump index

  if (pumpIndex < 0 || pumpIndex >= sizeof(pumpPins) / sizeof(pumpPins[0])) {
    Serial.println("Invalid pump index");
    return;
  }

  if (duration <= 0) {
    Serial.println("Invalid duration");
    return;
  }

  digitalWrite(pumpPins[pumpIndex], LOW); // Turn the pump ON
  Serial.print("ON_");
  Serial.print(pumpCommand);
  Serial.print("_for_");
  Serial.print(duration);
  Serial.println("ms");

  delay(duration); // Keep the pump ON for the specified duration

  digitalWrite(pumpPins[pumpIndex], HIGH); // Turn the pump OFF
  Serial.print("OFF_");
  Serial.println(pumpCommand);
}

void turnOffAllPumps() {
  for (int i = 0; i < sizeof(pumpPins) / sizeof(pumpPins[0]); i++) {
    digitalWrite(pumpPins[i], HIGH);
  }
  Serial.println("All pumps turned OFF");
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
  return analogRead(TDS_SENSOR_PIN);
}

float readPHSensor() {
  long sum = 0;
  for (int i = 0; i < NUM_READINGS; i++) {
    sum += analogRead(PH_SENSOR_PIN);
    delay(10);
  }
  float analogValue = sum / NUM_READINGS;
  //float slope = 0.018;
  //loat intercept = 7.0;
  return analogValue;
}
