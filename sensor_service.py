import time
import json
from datetime import datetime
import serial

# Serial configuration
serial_port = '/dev/ttyACM0'  # Update with your port
baud_rate = 9600

# Establish serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)  # Allow Arduino to initialize

# Function to send a command and handle "HEARTBEAT" responses
def send_command_and_get_response(command, retries=1):
    for _ in range(retries):
        ser.write(command)
        line = ser.readline().decode('utf-8').strip()
        if line == "HEARTBEAT":
            time.sleep(0.1)  # Short delay before retrying
            continue
        return line
    print(f"Error: No valid response for command {command.decode('utf-8')}")
    return None

# Function to read solution temperature from Dallas temperature sensor
def read_solution_temperature():
    response = send_command_and_get_response(b'T')
    if response is not None:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading temperature: {response}")
    return None

# Function to read tank level from ultrasonic sensor
def read_tank_level():
    response = send_command_and_get_response(b'L')
    if response is not None:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading tank level: {response}")
    return None

# Function to read EC (TDS) sensor value
def read_ec():
    response = send_command_and_get_response(b'D')
    if response is not None:
        try:
            print(f"------------Reading EC:{response}")
            return float(response)
        except ValueError:
            print(f"Error reading EC: {response}")
    return None

# Placeholder function for pH sensor (if needed later)
def read_ph():
    return None  # Placeholder for pH sensor

# Function to read all sensor data
def read_sensors():
    return {
        "solution_temperature": read_solution_temperature(),
        "tank_level": read_tank_level(),
        "ec": read_ec(),
        "ph": read_ph(),
        "timestamp": datetime.now().isoformat()
    }

# Function to save sensor data to JSON file
def save_sensor_data(data, filename="data/sensor_data.json"):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Main loop to keep reading sensors
def run_sensor_service():
    while True:
        sensor_data = read_sensors()
        print(f"Sensor Data: {sensor_data}")

        save_sensor_data(sensor_data)
        time.sleep(5)  # Adjust as needed

if __name__ == "__main__":
    run_sensor_service()
