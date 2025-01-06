import json
import time
import os
from sequencer import execute_sequence
from flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from flow_tune import PUMP_COMMANDS

# File paths
EC_SEQUENCE_FILE = '../sequences/EC_calibration.json'

import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sensor_service import read_ec  # Import after modifying the path




def get_EC_calibration_factor(filename="../data/calibration.json"):
    """
    Get the EC calibration factor from the calibration JSON file.

    Args:
        filename (str): Path to the calibration JSON file.

    Returns:
        float: The EC calibration factor. Defaults to 1.0 if not found.
    """
    try:
        with open(filename, "r") as file:
            calibration_data = json.load(file)
            return float(calibration_data.get("EC_calibration_factor", 1.0))
    except FileNotFoundError:
        print(f"Calibration file {filename} not found. Using default calibration factor of 1.0.")
        return 1.0
    except ValueError:
        print(f"Invalid data in {filename}. Using default calibration factor of 1.0.")
        return 1.0
    except Exception as e:
        print(f"Error loading calibration factor from {filename}: {e}")
        return 1.0








def save_calibration_data(data, filename="../data/calibration.json"):
    """
    Save calibration data to a JSON file.
    """
    try:
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Calibration data saved to {filename}.")
    except Exception as e:
        print(f"Error saving calibration data: {e}")

def load_calibration_data(filename="../data/calibration.json"):
    """
    Load calibration data from a JSON file.
    """
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Calibration file {filename} not found. Returning empty data.")
        return {}
    except Exception as e:
        print(f"Error loading calibration data: {e}")
        return {}

def calibrate_ec_sensor():
    """
    Calibrate the EC sensor by calculating the calibration factor and saving it to a file.
    """
    print("Starting EC sensor calibration...")

    # Load calibration solution value
    calibration_data = load_calibration_data()
    target_ec_value = calibration_data.get("EC_calibration_solution", 2000)
    print(f"Target EC value (calibration solution): {target_ec_value}")

    # Read EC value from the sensor
    ec_value = read_ec()
    if ec_value is None or ec_value == 0:
        print("Error: Unable to read EC value from the sensor or EC value is zero.")
        return

    print(f"Current EC value: {ec_value}")

    # Calculate the calibration factor
    calibration_factor = target_ec_value / float(ec_value)
    print(f"Calibration factor: {calibration_factor}")
    time.sleep(2000)
    # Save the calibration factor to the JSON file
    calibration_data["EC_calibration_factor"] = calibration_factor
    save_calibration_data(calibration_data)

    print("EC sensor calibration complete.")

def set_calibration_solution():
    """
    Set the EC calibration solution value and save it to the JSON file.
    """
    try:
        target_ec_value = float(input("Enter the EC value of the calibration solution: "))
        calibration_data = load_calibration_data()
        calibration_data["EC_calibration_solution"] = target_ec_value
        save_calibration_data(calibration_data)
        print(f"Calibration solution value set to {target_ec_value}.")
    except ValueError:
        print("Invalid input. Please enter a numeric value.")

def main():
    """
    Main function to handle the calibration menu.
    """
    while True:
        print("\n--- Calibration Menu ---")
        print("1. Calibrate EC Sensor")
        print("2. Set Calibration Solution Value")
        print("3. Read EC Value")
        print("4. Exit")

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
            set_calibration_solution()
        elif choice == "3":
            print("Reading EC values...")
            ec_value = get_EC_calibration_factor() * read_ec()
            print(f"Current EC value: {ec_value}")
        elif choice == "4":
            print("Exiting calibration tool. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
