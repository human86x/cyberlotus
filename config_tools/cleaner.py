import json
import time
import os
from sequencer import execute_sequence
from flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from flow_tune import PUMP_COMMANDS





# File paths
#FLOW_RATES_FILE = '../data/flow_rates.json'
#PUMP_COMMANDS_FILE = '../data/relay_names.json'
EC_SEQUENCE_FILE = '../sequences/EC_cal_clean.json'


import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sensor_service import read_ec  # Import after modifying the path





def main():
    """
    Main function to handle the calibration menu.
    """
    while True:
        print("\n--- Cleaning Menu ---")
        print("1. Clean EC_cal pump")
        print("2. Exit")
        
        
        choice = input("Select an option: ")

        if choice == "1":
            print("Loading EC cleaning sequence...")
            # Load flow rates
            SEQUENCE_FILE = '../sequences/EC_cal_clean.json'
            flow_rates = load_flow_rates()
            if not flow_rates:
                print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
                continue

            # Execute the sequence with calibration callback
            execute_sequence(SEQUENCE_FILE, flow_rates)
        elif choice == "2":
            print("Exiting calibration tool. Goodbye!")
            break
        elif choice == "3":
            print("Reading EC values")
            ec_value = read_ec()
            #print("EC DEBUG - {read_ec()}")
    
            print(f"Current EC value: {ec_value}")
            #read_ec()
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
