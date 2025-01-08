import time
import json
import os
from datetime import datetime, timedelta
import sys

# Add the current script's directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "config_tools"))

from config_tools.sequencer import execute_sequence
from config_tools.calibrator import get_correct_EC
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from control_libs.arduino import connect_to_arduino, send_command_and_get_response
from control_libs.electric_conductivity import get_ec
from control_libs.temperature import read_solution_temperature
# Establish serial connection
global ser
ser = connect_to_arduino()
time.sleep(2)  # Allow Arduino to initialize

# File paths
EC_TEST_SEQUENCE_FILE = 'sequences/EC_test.json'
SENSOR_DATA_FILE = "data/sensor_data.json"

# Function to send a command and handle "HEARTBEAT" responses
#def send_command_and_get_response(command, retries=1):
#    for _ in range(retries):
#        ser.write(command)
#        line = ser.readline().decode('utf-8').strip()
#        if line == "HEARTBEAT":
#            time.sleep(0.1)  # Short delay before retrying
#            continue
#        return line
#    print(f"Error: No valid response for command {command.decode('utf-8')}")
#    return None

# Function to read solution temperature
#def read_solution_temperature():
#    response = send_command_and_get_response(b'T')
#    if response:
#        try:
#            return float(response)
#        except ValueError:
#            print(f"Error reading temperature: {response}")
#    return None

# Function to read tank level
def read_tank_level():
    response = send_command_and_get_response(ser, b'L')
    if response:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading tank level: {response}")
    return None

# Function to get EC readings

import json
from datetime import datetime

# Assuming this is the path to your JSON file
SENSOR_DATA_FILE = "sensor_data.json"

def update_ec():
    # Get the corrected EC value
    ec = get_correct_EC()
    print(f"***********UPDATED EC----- : {ec}")
    
    # Initialize the new data to update
    updated_data = {
        "ec": ec,
        "ec_last_updated": datetime.now().isoformat()
    }
    
    # Load existing data
    try:
        with open(SENSOR_DATA_FILE, 'r') as file:
            sensor_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle cases where the file doesn't exist or is corrupted
        print("Error: Sensor data file not found or invalid. Creating a new file.")
        sensor_data = {}

    # Update only the relevant fields in the loaded data
    sensor_data.update(updated_data)
    
    # Debugging: Show the updated data
    print(f"***********sensor data----- : {sensor_data}")
    
    # Save the updated data back to the file
    with open(SENSOR_DATA_FILE, 'w') as file:
        json.dump(sensor_data, file, indent=4)

    return None


def get_ec_readings():
    ec_data = {}
    target_ec_timing = 10
    if os.path.exists(EC_TEST_SEQUENCE_FILE):
        print(f"Found file: {EC_TEST_SEQUENCE_FILE}")
    else:
        print(f"File not found: {EC_TEST_SEQUENCE_FILE}")
    try:
        #execute_sequence(, {}, lambda data: ec_data.update(data))
        a = execute_sequence(EC_TEST_SEQUENCE_FILE, load_flow_rates(), update_ec)
        # test test test print(f"Sequence return = : {a}")
        return a
    except Exception as e:
        print(f"Error executing EC test sequence: {e}")
    return None

# Function to read EC value with timestamp check
def check_ec_time():
    try:
        if os.path.exists(SENSOR_DATA_FILE):
            with open(SENSOR_DATA_FILE, "r") as file:
                sensor_data = json.load(file)

            last_timestamp = sensor_data.get("ec_last_updated", "1970-01-01T00:00:00")
            
            # Ensure the timestamp is in datetime format
            if isinstance(last_timestamp, str):
                last_timestamp = datetime.fromisoformat(last_timestamp)
            else:
                print("Warning: 'ec_last_updated' is not a valid string. Using default timestamp.")
                last_timestamp = datetime(1970, 1, 1)

            # Calculate the time difference in minutes
            time_difference = (datetime.now() - last_timestamp).total_seconds() / 60.0

            # Debug output: print the last timestamp, current time, and the difference in minutes
            print(f"Last EC timestamp: {last_timestamp}")
            print(f"Current time: {datetime.now()}")
            print(f"Time difference in minutes: {time_difference:.2f}")
            print(f"Trigger value (minutes): 5")

            # Check if the timestamp is recent (less than 0.2 minutes old)
            if time_difference < target_ec_timing:
                print("EC data is recent; skipping new EC reading.")
                ec_value = get_ec_readings_from_file()
                return ec_value  # Skip new reading if data is recent

        print("Performing new EC reading...")
        return get_ec_readings()

    except Exception as e:
        print(f"Error reading EC: {e}")
    return None



def get_ec_readings_from_file():
    """
    Reads the EC value from the sensor_data.json file.

    Returns:
        float or None: The EC value if found, otherwise None.
    """
    try:
        if not os.path.exists(SENSOR_DATA_FILE):
            print(f"File not found: {SENSOR_DATA_FILE}")
            return None

        with open(SENSOR_DATA_FILE, "r") as file:
            sensor_data = json.load(file)

        # Get the EC value
        ec_value = sensor_data.get("ec")
        if ec_value is not None:
            return ec_value

        print("EC value not found in the file.")
        return None
    except Exception as e:
        print(f"Error reading EC data from file: {e}")
        return None

# Function to read all sensor data
def read_sensors():
    # Attempt to get EC readings from check_ec_time
    ec_readings = check_ec_time()
    ec_value = None
    ec_timestamp = None

    # If check_ec_time doesn't provide a valid EC reading, load it from the file
    if ec_readings is not None and ec_readings != 0:  # New EC data available
        ec_value = ec_readings
        ec_timestamp = datetime.now().isoformat()
    else:
        print("EC reading not updated. Fetching from file.")
        ec_value = get_ec_readings_from_file()
        ec_timestamp = datetime.now().isoformat()

    # Collect other sensor data
    return {
        "solution_temperature": read_solution_temperature(ser),
        "tank_level": read_tank_level(),
        "ec": ec_value,
        "ph": read_ph(),
        "timestamp": datetime.now().isoformat()
        
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
