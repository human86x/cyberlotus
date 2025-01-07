import serial
import time

def connect_arduino():
    """
    Tries to connect to an Arduino Mega via /dev/ttyACM0 through /dev/ttyACM10.
    Returns the serial connection if successful, otherwise raises an exception.
    """
    for i in range(11):  # Check ports /dev/ttyACM0 to /dev/ttyACM10
        port = f"/dev/ttyACM{i}"
        try:
            print(f"Trying to connect to {port}...")
            connection = serial.Serial(port, baudrate=9600, timeout=1)
            time.sleep(2)  # Allow time for the Arduino to reset
            print(f"Connected successfully to {port}")
            return connection
        except serial.SerialException:
            print(f"Failed to connect to {port}.")
            continue

    raise Exception("Unable to connect to Arduino on any /dev/ttyACM* port.")

# Usage example
#t#ry:
#    arduino = connect_arduino()
#    # Add code to interact with the Arduino
#    arduino.write(b"Hello Arduino!")
#    arduino.close()
#except Exception as e:
#    print(e)
