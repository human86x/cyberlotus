// Define the range of pins connected to the transistor bases
const int startPin = 2;
const int endPin = 10;

// Define the PWM values for ON and OFF states
const int pwmValueOff = 255;  // 5V (transistor off)
const int pwmValueOn = 36;    // ~4.3V (transistor on)

// Define the delay time for each step (milliseconds)
const int stepDelay = 100;   // 2 seconds

void setup() {
  // Initialize Serial Communication for debugging
  Serial.begin(9600);

  // Set all pins in the range as output
  for (int pin = startPin; pin <= endPin; pin++) {
    pinMode(pin, OUTPUT);
    // Ensure all transistors are off at the start
    analogWrite(pin, pwmValueOff);
  }

  // Debug message
  Serial.println("Setup complete. Starting sequential forward-backward transistor activation.");
}

void loop() {
  // Forward sequence: 2 to 9
  for (int pin = startPin; pin <= endPin; pin++) {
    activateTransistor(pin);
  }

  // Backward sequence: 8 to 2
  for (int pin = endPin - 1; pin >= startPin; pin--) {
    activateTransistor(pin);
  }

  // Debug message for end of sequence
  Serial.println("Completed one full forward-backward sequence. Restarting...");
}

// Function to activate a transistor
void activateTransistor(int pin) {
  // Turn the current transistor ON
  Serial.print("Activating transistor on pin ");
  Serial.println(pin);
  analogWrite(pin, pwmValueOn);

  // Wait for the step delay
  delay(stepDelay);

  // Turn the current transistor OFF
  Serial.print("Deactivating transistor on pin ");
  Serial.println(pin);
  analogWrite(pin, pwmValueOff);
}
