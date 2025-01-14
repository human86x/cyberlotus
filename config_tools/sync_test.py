import serial
import time

# Set the correct port and baud rate for Linux
arduino_port = '/dev/ttyACM1'  # Replace with your actual port if different
baud_rate = 9600

# Initialize serial connection
ser = serial.Serial(arduino_port, baud_rate, timeout=1)
time.sleep(2)  # Allow time for Arduino to reset

def test_pumps():
    for i in range(18):  # Pumps 'a' to 'r'
        pump_letter = chr(ord('a') + i)
        
        print(f"Activating Pump {pump_letter.upper()}")
        ser.write(f"{pump_letter}o".encode())  # Turn pump ON
        time.sleep(2)  # Pump runs for 2 seconds
        
        print(f"Deactivating Pump {pump_letter.upper()}")
        ser.write(f"{pump_letter}f".encode())  # Turn pump OFF
        time.sleep(1)  # Short delay before the next pump

    print("Pump test completed.")

try:
    test_pumps()
except KeyboardInterrupt:
    print("Test interrupted. Shutting down all pumps.")
    for i in range(18):
        ser.write(f"{chr(ord('a') + i)}f".encode())  # Ensure all pumps are OFF
    ser.close()
