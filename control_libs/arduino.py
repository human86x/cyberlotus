import serial
import time

ser = None

def connect_to_arduino():
    global ser
    """
    Ensures only one connection is created and reused.
    """
    if not hasattr(connect_to_arduino, "connection"):
        for i in range(11):  # Check ports /dev/ttyACM0 to /dev/ttyACM10
            port = f"/dev/ttyACM{i}"
            try:
                print(f"Trying to connect to {port}...")
                connect_to_arduino.connection = serial.Serial(port, baudrate=9600, timeout=1)
                time.sleep(2)  # Allow time for the Arduino to reset
                print(f"Connected successfully to {port}")
                ser = connect_to_arduino.connection
                return connect_to_arduino.connection
            except serial.SerialException:
                print(f"Failed to connect to {port}.")
                continue
        raise Exception("Unable to connect to Arduino on any /dev/ttyACM* port.")
    return connect_to_arduino.connection


def get_serial_connection():
    global ser
    if ser and ser.is_open:
        return ser
    else:
        print("[ERROR] Serial connection is not established.")
        return None

def close_serial_connection():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("[INFO] Serial connection closed.")



# Usage example
#t#ry:
#    arduino = connect_arduino()
#    # Add code to interact with the Arduino
#    arduino.write(b"Hello Arduino!")
#    arduino.close()
#except Exception as e:
#    print(e)

#ser = arduino_connect()#serial.Serial(serial_port, baud_rate, timeout=1)
#time.sleep(2)  # Allow Arduino to initialize

# Function to send a command and handle "HEARTBEAT" responses
def send_command_and_get_response(ser, command, retries=1):
    for _ in range(retries):
        ser.write(command)  # No need to encode if command is already bytes
        line = ser.readline().decode('utf-8').strip()
        if line == "HEARTBEAT":
            time.sleep(0.1)  # Short delay before retrying
            continue
        return line
    print(f"Error: No valid response for command {command.decode('utf-8')}")
    return None
