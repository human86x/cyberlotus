import time
import json
import os
from datetime import datetime, timedelta
import sys

# Add the current script's directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "config_tools"))

from config_tools.sequencer import execute_sequence
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from device_connections import connect_arduino

# Establish serial connection
ser = connect_arduino()
time.sleep(2)  # Allow Arduino to initialize

# File paths
EC_TEST_SEQUENCE_FILE = 'sequences/EC_test.json'
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

# Function to read solution temperature
def read_solution_temperature():
    response = send_command_and_get_response(b'T')
    if response:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading temperature: {response}")
    return None

# Function to read tank level
def read_tank_level():
    response = send_command_and_get_response(b'L')
    if response:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading tank level: {response}")
    return None

# Function to get EC readings
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
        if os.path.exists(SENSOR_DATA_FILE):
            with open(SENSOR_DATA_FILE, "r") as file:
                sensor_data = json.load(file)

            last_timestamp = datetime.fromisoformat(sensor_data.get("ec_last_updated", "1970-01-01T00:00:00"))
            if datetime.now() - last_timestamp < timedelta(minutes=0.2):
                print("EC data is recent; skipping new EC reading.")
                return 0  # Skip new reading if data is recent

        print("Performing new EC reading...")
        return get_ec_readings()
    except Exception as e:
        print(f"Error reading EC: {e}")
    return None

# Function to read all sensor data
def read_sensors():
    ec_readings = read_ec()
    ec_value = None
    ec_timestamp = None

    if ec_readings != 0:  # New EC data available
        ec_value = ec_readings
        ec_timestamp = datetime.now().isoformat()

    return {
        "solution_temperature": read_solution_temperature(),
        "tank_level": read_tank_level(),
        "ec": ec_value,
        "ph": read_ph(),
        "timestamp": datetime.now().isoformat(),
        "ec_last_updated": ec_timestamp,
    }

# Function to save sensor data to JSON file
def save_sensor_data(data, filename=SENSOR_DATA_FILE):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Placeholder function for pH sensor
def read_ph():
    return None  # Placeholder for pH sensor

# Main loop to keep reading sensors
def run_sensor_service():
    while True:
        sensor_data = read_sensors()
        print(f"Sensor Data: {sensor_data}")

        save_sensor_data(sensor_data)
        time.sleep(5)  # Adjust as needed

if __name__ == "__main__":
    run_sensor_service()
