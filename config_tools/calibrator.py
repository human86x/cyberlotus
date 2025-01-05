import json
import time
import os
from sequencer import execute_sequence
from flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from flow_tune import PUMP_COMMANDS





# File paths
#FLOW_RATES_FILE = '../data/flow_rates.json'
#PUMP_COMMANDS_FILE = '../data/relay_names.json'
EC_SEQUENCE_FILE = '../sequences/EC_calibration.json'


import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sensor_service import read_ec  # Import after modifying the path




#from sensor_service import read_ec

def calibrate_ec_sensor():
    """
    Calibrate the EC sensor by retrieving the EC value and guiding the user through the process.
    """
    print("Starting EC sensor calibration...")

    # Read EC value from the sensor
    ec_value = read_ec()
    if ec_value is None:
        print("Error: Unable to read EC value from the sensor.")
        return

    print(f"Current EC value: {ec_value}")
    
    # Guide user to perform manual adjustments if necessary
    input("Adjust the EC sensor setup as needed. Press Enter when ready to continue.")

    # Optionally save the calibrated EC value
    save_calibration_data({"calibrated_ec": ec_value})
    print("EC sensor calibration complete.")

def save_calibration_data(data, filename="data/calibration_data.json"):
    """
    Save calibration data to a JSON file.
    """
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Calibration data saved to {filename}.")
    except Exception as e:
        print(f"Error saving calibration data: {e}")

def main():
    """
    Main function to handle the calibration menu.
    """
    while True:
        print("\n--- Calibration Menu ---")
        print("1. Calibrate EC Sensor")
        print("2. Exit")
        choice = input("Select an option: ")

        if choice == "1":
            print("Loading EC calibration sequence...")
            # Load flow rates
            flow_rates = load_flow_rates()
            if not flow_rates:
                print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
                continue

            # Execute the sequence with calibration callback
            execute_sequence(EC_SEQUENCE_FILE, flow_rates, calibrate_ec_sensor)
        elif choice == "2":
            print("Exiting calibration tool. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
