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

# Function to read tank level
def read_tank_level():
    response = send_command_and_get_response(ser, b'L')
    if response:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading tank level: {response}")
    return None

# Function to update EC value
ec_last_updated = None  # Track the last time EC was updated
ec_last_reading = None  # Store the last EC reading

def update_ec():
    global ec_last_updated, ec_last_reading
    # Get the corrected EC value
    ec = get_correct_EC()
    print(f"***********UPDATED EC----- : {ec}")

    # Only update EC if the value is different from the last one
    if ec != ec_last_reading:
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

        # Update the global variables
        ec_last_reading = ec
        ec_last_updated = datetime.now().isoformat()

    return None

# Function to get EC readings
def get_ec_readings():
    ec_data = {}

    if os.path.exists(EC_TEST_SEQUENCE_FILE):
        print(f"Found file: {EC_TEST_SEQUENCE_FILE}")
    else:
        print(f"File not found: {EC_TEST_SEQUENCE_FILE}")
    try:
        # Execute the sequence and update EC data
        execute_sequence(EC_TEST_SEQUENCE_FILE, load_flow_rates(), update_ec)
        return ec_data
    except Exception as e:
        print(f"Error executing EC test sequence: {e}")
    return None

# Function to read EC value with timestamp check
def check_ec_time():
    target_ec_timing = 10  # Target time interval to skip new EC reading

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

            # Check if the timestamp is recent (less than 5 minutes old)
            if time_difference < target_ec_timing:
                print("EC data is recent; skipping new EC reading.")
                ec_value = get_ec_readings_from_file()
                return ec_value  # Skip new reading if data is recent

        print("Performing new EC reading...")
        ec_value = get_ec_readings()
        update_ec()  # Ensure the timestamp gets updated after a new reading
        return ec_value

    except Exception as e:
        print(f"Error reading EC: {e}")
    return None

def get_ec_readings_from_file():
    """
    Reads the EC value from the sensor_data.json file.
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
    # Load the current sensor data from file to preserve previously collected values
    try:
        with open(SENSOR_DATA_FILE, "r") as file:
            sensor_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or there's an error in reading, initialize an empty sensor_data dictionary
        sensor_data = {
            "solution_temperature": None,
            "tank_level": None,
            "ec": None,
            "ph": None,
            "timestamp": datetime.now().isoformat(),
            "ec_last_updated": None  # Ensure this field exists
        }

    # Attempt to get EC readings from check_ec_time
    ec_readings = check_ec_time()
    ec_value = None
    ec_timestamp = None

    # If check_ec_time doesn't provide a valid EC reading, load it from the file
    if ec_readings is not None and ec_readings != 0:  # New EC data available
        ec_value = ec_readings
        ec_timestamp = datetime.now().isoformat()
        # Update the EC field in the sensor data only if it's a new value
        sensor_data["ec"] = ec_value
        sensor_data["ec_last_updated"] = ec_timestamp  # Update EC last updated time
    else:
        print("EC reading not updated. Fetching from file.")
        ec_value = get_ec_readings_from_file()
        if ec_value is not None:
            # EC reading is valid, update it
            sensor_data["ec"] = ec_value
            # Ensure ec_last_updated is preserved or updated if it exists
            if "ec_last_updated" not in sensor_data or sensor_data["ec_last_updated"] is None:
                sensor_data["ec_last_updated"] = datetime.now().isoformat()

    # Collect other sensor data, but don't overwrite existing values
    sensor_data["solution_temperature"] = read_solution_temperature(ser)  # Update temperature
    sensor_data["tank_level"] = read_tank_level()  # Update tank level
    sensor_data["ph"] = read_ph()  # Update pH (even if placeholder, could be improved later)
    sensor_data["timestamp"] = datetime.now().isoformat()  # Update timestamp to reflect current time

    # Debugging: print the updated sensor data
    print(f"Updated sensor data: {sensor_data}")

    # Save the updated sensor data back to the file
    save_sensor_data(sensor_data)

    return sensor_data


# Function to save sensor data to JSON file
def save_sensor_data(data, filename=SENSOR_DATA_FILE):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Placeholder function for pH sensor
def read_ph():
    return None  # Placeholder for pH sensor

def collect_ec_reading():
    # Collect EC readings
    ec_readings = []
    for _ in range(10):  # Assuming you're taking 10 readings
        reading = get_ec_value_from_sensor()
        if reading:
            ec_readings.append(reading)
    
    # Process and calculate the median of valid readings
    if ec_readings:
        valid_readings = [r for r in ec_readings if isinstance(r, (int, float))]  # Ensure valid data
        if valid_readings:
            median_ec = median(valid_readings)
            return median_ec
    return None

def run_sensor_service():
    global sensor_data  # Ensure sensor_data is accessible
    last_ec_timestamp = sensor_data.get('ec_last_updated')

    # Check the time difference between the last EC timestamp and current time
    current_time = datetime.now()
    if last_ec_timestamp:
        last_ec_time = datetime.fromisoformat(last_ec_timestamp)
        time_difference = (current_time - last_ec_time).total_seconds() / 60.0
    else:
        time_difference = 99999  # Force reading if no previous timestamp

    # Trigger reading if the time difference exceeds the threshold
    if time_difference >= trigger_value:
        ec_value = collect_ec_reading()
        if ec_value:
            sensor_data['ec'] = ec_value
            sensor_data['ec_last_updated'] = current_time.isoformat()
            print(f"EC reading updated: {ec_value}")
        else:
            print("EC reading failed.")
    else:
        print("EC data is recent; skipping new reading.")

if __name__ == "__main__":
    run_sensor_service()
