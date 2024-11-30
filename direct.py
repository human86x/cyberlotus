import serial
import time

# Define the serial connection
serial_port = '/dev/ttyACM0'  # Replace with your Arduino's serial port
baud_rate = 9600

try:
    # Open the serial connection
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    time.sleep(2)  # Wait for the Arduino to initialize

    # Send the command to turn on pin 7
    ser.write(b'eo')  # 'e' corresponds to pin 7, 'o' means ON
    print("Command sent: eo (Turn on pin 7)")

    # Close the serial connection
    ser.close()

except serial.SerialException as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
