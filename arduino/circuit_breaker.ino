#define RELAY_PIN D1  // GPIO5 for Relay control pin (using D1 instead of TX)
#define RESET_PIN D3  // GPIO0 for Arduino Mega RESET (RX pin will trigger this)

void setup() {
  pinMode(RELAY_PIN, OUTPUT);   // Set Relay pin as output
  pinMode(RESET_PIN, OUTPUT);   // Set RESET pin as output (IMPORTANT FIX)

  digitalWrite(RESET_PIN, HIGH); // Ensure D3 starts HIGH (inactive)
  
  Serial.begin(9600);           // Initialize Serial communication
}

void loop() {
  if (Serial.available()) {
    char incomingChar = Serial.read();
    
    if (incomingChar == 'X') {   // Trigger relay
      triggerRelay();
    } else if (incomingChar == 'R') {  // Reset Arduino Mega
      resetMega();
    } else if (incomingChar == 'Y') {  // Deactivate relay
      deactivateRelay();
    }
  }
}

// Trigger relay function
void triggerRelay() {
  digitalWrite(RELAY_PIN, LOW);  // Turn relay ON
}

// Deactivate relay function
void deactivateRelay() {
  digitalWrite(RELAY_PIN, HIGH); // Turn relay OFF
}

// Reset Arduino Mega function
void resetMega() {
  digitalWrite(RESET_PIN, LOW);   // Pull RESET pin LOW
  delay(100);                     // Hold LOW for 100ms
  digitalWrite(RESET_PIN, HIGH);  // Release RESET pin
}
