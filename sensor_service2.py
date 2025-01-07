import time
import json
import os
from datetime import datetime, timedelta
import sys

# Add the current script's directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "config_tools"))


#import     serial

from config_tools.sequencer import execute_sequence  # Updated import path
#from config_tools.flow_tune import load_flow_rates  # Updated import path
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
#from .flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands

#from config_tools import flow_tune #load_flow_rates
from device_connections import connect_arduino

# Serial configuration
#serial_port = '/dev/ttyACM0'  # Update with your port
#baud_rate = 9600

# Establish serial connection
ser = connect_arduino()#serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)  # Allow Arduino to initialize

# File paths
EC_TEST_SEQUENCE_FILE = '../sequences/EC_test.json'
SENSOR_DATA_FILE = "data/sensor_data.json"

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

# Function to get EC readings from the EC test sequence
def get_ec_readings():
    ec_data = {}
    try:
        execute_sequence(EC_TEST_SEQUENCE_FILE, {}, lambda data: ec_data.update(data))
        if 'ec' in ec_data:
            return ec_data['ec']
    except Exception as e:
        print(f"Error executing EC test sequence: {e}")
    return None

# Function to read EC value with timestamp check
def read_ec():
    try:
        # Check if the file exists and read its contents
        if os.path.exists(SENSOR_DATA_FILE):
            with open(SENSOR_DATA_FILE, "r") as file:
                sensor_data = json.load(file)

            # Check timestamp
            last_timestamp = datetime.fromisoformat(sensor_data.get("timestamp", "1970-01-01T00:00:00"))
            if datetime.now() - last_timestamp < timedelta(minutes=0.2):
                print("EC data is recent; skipping new EC reading.")
                return sensor_data.get("ec")

        # If the data is outdated or the file does not exist, read new EC data
        print("Performing new EC reading...")
        return get_ec_readings()
    except Exception as e:
        print(f"Error reading EC: {e}")
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
def save_sensor_data(data, filename=SENSOR_DATA_FILE):
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
