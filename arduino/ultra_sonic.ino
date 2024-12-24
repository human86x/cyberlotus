#define TRIG_PIN 9
#define ECHO_PIN 10

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.begin(9600); // Initialize serial communication for debugging
}

void loop() {
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

  // Print the distance to the Serial Monitor
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  delay(500); // Wait before the next measurement
}
