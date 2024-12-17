#include <HX711_ADC.h>
#if defined(ESP8266) || defined(ESP32) || defined(AVR)
#include <EEPROM.h>
#endif

const int HX711_dout = 26; // MCU > HX711 DOUT pin
const int HX711_sck = 24;  // MCU > HX711 SCK pin

HX711_ADC LoadCell(HX711_dout, HX711_sck);

unsigned long t = 0;
float previousValue = 0.0;

void setup() {
  Serial.begin(9600);
  delay(100);
  Serial.println("\nStarting...");

  LoadCell.begin();
  //LoadCell.setReverseOutput();

  LoadCell.setSamplesInUse(40); // Increase averaging for stability

  float calibrationValue = -607.0; // Adjust as per Calibration.ino
  LoadCell.start(2000, true);

  if (LoadCell.getTareTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 wiring and pin designations");
    while (1);
  } else {
    LoadCell.setCalFactor(calibrationValue);
    Serial.println("Startup is complete");
  }
}

void loop() {
  static boolean newDataReady = 0;
  const int serialPrintInterval = 200; // Print every 200ms

  if (LoadCell.update()) newDataReady = true;

  if (newDataReady && millis() > t + serialPrintInterval) {
    float rawValue = LoadCell.getData();
    float smoothedValue = 0.95 * previousValue + 0.05 * rawValue;
    previousValue = smoothedValue;

    Serial.print("Load_cell raw value: ");
    Serial.print(rawValue);
    Serial.print(" | Smoothed value: ");
    Serial.println(smoothedValue);

    newDataReady = 0;
    t = millis();
  }
}
