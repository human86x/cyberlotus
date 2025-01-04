import json
import time
from sequencer import execute_sequence
from flow_tune import load_flow_rates

# File paths
EC_SEQUENCE_FILE = '../sequences/EC_calibration.json'
CALIBRATION_FILE = '../data/calibration.json'

# Menu options
def display_menu():
    print("\n--- Calibration Menu ---")
    print("1. Calibrate EC Sensor")
    print("2. Exit")
    choice = input("Select an option: ")
    return choice

# Save calibration factor to file
def save_calibration_factor(sensor, factor):
    try:
        with open(CALIBRATION_FILE, 'r') as file:
            calibration_data = json.load(file)
    except FileNotFoundError:
        calibration_data = {}

    calibration_data[sensor] = factor

    with open(CALIBRATION_FILE, 'w') as file:
        json.dump(calibration_data, file, indent=4)

    print(f"Calibration factor for {sensor} saved: {factor}")

# Calibrate EC sensor
def calibrate_ec_sensor():
    """
    Calibrate the EC sensor by executing the calibration sequence.
    """
    print("Starting EC sensor calibration...")

    # Load flow rates
    flow_rates = load_flow_rates()
    if not flow_rates:
        print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
        return

    # Load pump commands
    PUMP_COMMANDS = load_pump_commands()
    if not PUMP_COMMANDS:
        print("Error: Pump commands not loaded. Ensure the relay_names.json file exists and is valid.")
        return

    # Execute the calibration sequence with both flow_rates and PUMP_COMMANDS
    execute_sequence(EC_SEQUENCE_FILE, flow_rates, PUMP_COMMANDS)
    print("EC sensor calibration complete.")

# Main loop
def main():
    while True:
        choice = display_menu()

        if choice == "1":
            calibrate_ec_sensor()
        elif choice == "2":
            print("Exiting calibration utility.")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
