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

def calibrate_ec_sensor():
    """
    Calibrate the EC sensor.
    """
    print("Starting EC sensor calibration...")

    # Perform the calibration logic here
    input("Perform calibration manually and press Enter to continue...")

    print("EC sensor calibration complete.")

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
