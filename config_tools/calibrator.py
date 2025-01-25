import json
import time
import os
import sys
import statistics
from config_tools.sequencer import execute_sequence
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from control_libs.electric_conductivity import get_ec, calibrate_ec_sensor, get_correct_EC, get_EC_calibration_factor
from control_libs.temperature import read_solution_temperature
from control_libs.arduino import connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state
base_dir = os.path.dirname(os.path.abspath(__file__))
from control_libs.app_core import CALIBRATION_FILE
# Use absolute paths for file locations
EC_SEQUENCE_FILE = os.path.join(base_dir, '../sequences/EC_calibration.json')
EC_BASELINE_FILE = os.path.join(base_dir, '../sequences/EC_baseline.json')

global ser
ser = connect_to_arduino()


def save_calibration_data(data):
    try:
        with open(CALIBRATION_FILE, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Calibration data saved to {CALIBRATION_FILE}.")
    except Exception as e:
        print(f"Error saving calibration data: {e}")

def load_calibration_data():
    try:
        with open(CALIBRATION_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Calibration file {CALIBRATION_FILE} not found. Returning empty data.")
        return {}
    except Exception as e:
        print(f"Error loading calibration data: {e}")
        return {}



#def main():
#    while True:
#        print("\n--- Calibration Menu ---")
#        print("1. Calibrate EC Sensor")
#        print("2. Set Calibration Solution Value")
#        print("3. Read EC Value")
#        print("4. Set Water EC Baseline")
#        print("5. Exit")#
#
#        choice = input("Select an option: ")

        #if choice == "1":
        #    temp = load_flow_rates()
        #    print(f"flow rates: {temp}")#
#
#            execute_sequence(EC_SEQUENCE_FILE, load_flow_rates(), calibrate_ec_sensor)
#        elif choice == "2":
#            set_calibration_solution()
#        elif choice == "3":
#            ec_value = get_correct_EC()
#            print(f"Current EC value: {ec_value}")
#        elif choice == "4":
#            execute_sequence(EC_BASELINE_FILE, load_flow_rates(), set_baseline_ec)
#        elif choice == "5":
#            print("Exiting calibration tool. Goodbye!")
#            break
#        else:
#            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
