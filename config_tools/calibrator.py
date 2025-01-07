import json
import time
import os
import sys
import statistics
from sequencer import execute_sequence
from flow_tune import send_command_with_heartbeat, load_flow_rates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from control_libs.electric_conductivity import get_ec
from control_libs.temperature import read_solution_temperature

# File paths
EC_SEQUENCE_FILE = '../sequences/EC_calibration.json'
EC_BASELINE_FILE = '../sequences/EC_baseline.json'
CALIBRATION_FILE = '../data/calibration.json'

def get_correct_EC():
    #sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    #from sensor_service import read_ec, read_solution_temperature  # Import after modifying the path

    """
    Get the corrected EC value by reading the EC sensor, applying temperature correction, and using the calibration factor.

    Returns:
        float: The corrected EC value.
    """
    calibration_factor = get_EC_calibration_factor()
    raw_ec_value = get_ec()
    if raw_ec_value is None or raw_ec_value == 0:
        print("Error: Invalid EC value read from the sensor.")
        return None

    try:
        raw_ec_value = float(raw_ec_value)
    except ValueError:
        print(f"Error: Invalid EC value '{raw_ec_value}' received, cannot convert to float.")
        return None

    print(f"Raw EC value: {raw_ec_value}")

    solution_temperature = read_solution_temperature()
    try:
        solution_temperature = float(solution_temperature)
    except ValueError:
        print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
        return None

    print(f"Solution temperature: {solution_temperature}°C")

    if solution_temperature != 25:
        corrected_ec_value = raw_ec_value / (1 + 0.02 * (solution_temperature - 25))
        print(f"Corrected EC value at 25°C: {corrected_ec_value}")
    else:
        corrected_ec_value = raw_ec_value

    corrected_ec_value *= calibration_factor
    print(f"Final corrected EC value after applying calibration factor: {corrected_ec_value}")

    return corrected_ec_value

def get_EC_calibration_factor():
    try:
        with open(CALIBRATION_FILE, "r") as file:
            calibration_data = json.load(file)
            return float(calibration_data.get("EC_calibration_factor", 1.0))
    except FileNotFoundError:
        print(f"Calibration file {CALIBRATION_FILE} not found. Using default calibration factor of 1.0.")
        return 1.0
    except Exception as e:
        print(f"Error loading calibration factor: {e}")
        return 1.0

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

def calibrate_ec_sensor():
    print("Starting EC sensor calibration...")
    calibration_data = load_calibration_data()
    target_ec_value = calibration_data.get("EC_calibration_solution", 2000)
    print(f"Target EC value (calibration solution): {target_ec_value}")

    num_readings = 15
    ec_values = []
    for _ in range(num_readings):
        time.sleep(1)
        ec_value = get_ec()
        print(f"Retrieved EC value: '{ec_value}'")
        if ec_value is None or ec_value == 0:
            print("Error: Invalid EC value read from the sensor.")
            continue
        try:
            ec_value = float(ec_value)
        except ValueError:
            print(f"Error: Invalid EC value '{ec_value}' received, cannot convert to float.")
            continue
        if 100 <= ec_value <= 5000:
            ec_values.append(ec_value)

    if len(ec_values) == 0:
        print("Error: No valid EC readings collected.")
        return

    estimated_ec_value = statistics.median(ec_values)
    print(f"Estimated EC value: {estimated_ec_value}")
    solution_temperature = read_solution_temperature()
    try:
        solution_temperature = float(solution_temperature)
    except ValueError:
        print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
        return

    print(f"Solution temperature: {solution_temperature}°C")

    if solution_temperature != 25:
        corrected_ec_value = estimated_ec_value / (1 + 0.02 * (solution_temperature - 25))
    else:
        corrected_ec_value = estimated_ec_value

    calibration_factor = target_ec_value / corrected_ec_value
    print(f"Calibration factor: {calibration_factor}")

    calibration_data["EC_calibration_factor"] = calibration_factor
    save_calibration_data(calibration_data)
    print("EC sensor calibration complete.")

def set_baseline_ec():
    print("Setting EC baseline...")
    num_readings = 15
    ec_values = []
    for _ in range(num_readings):
        time.sleep(1)
        ec_value = get_correct_EC()
        print(f"Retrieved EC value: '{ec_value}'")
        if ec_value is None or ec_value == 0:
            print("Error: Invalid EC value read from the sensor.")
            continue
        try:
            ec_value = float(ec_value)
        except ValueError:
            print(f"Error: Invalid EC value '{ec_value}' received, cannot convert to float.")
            continue
        if 0 <= ec_value <= 10000:
            ec_values.append(ec_value)

    if len(ec_values) == 0:
        print("Error: No valid EC readings collected.")
        return

    estimated_ec_value = statistics.median(ec_values)
    print(f"Baseline EC value: {estimated_ec_value}")

    calibration_data = load_calibration_data()
    calibration_data["EC_baseline"] = estimated_ec_value
    save_calibration_data(calibration_data)
    print("EC baseline set and saved.")

def main():
    while True:
        print("\n--- Calibration Menu ---")
        print("1. Calibrate EC Sensor")
        print("2. Set Calibration Solution Value")
        print("3. Read EC Value")
        print("4. Set Water EC Baseline")
        print("5. Exit")

        choice = input("Select an option: ")

        if choice == "1":
            execute_sequence(EC_SEQUENCE_FILE, load_flow_rates(), calibrate_ec_sensor)
        elif choice == "2":
            set_calibration_solution()
        elif choice == "3":
            ec_value = get_correct_EC()
            print(f"Current EC value: {ec_value}")
        elif choice == "4":
            execute_sequence(EC_BASELINE_FILE, load_flow_rates(), set_baseline_ec)
        elif choice == "5":
            print("Exiting calibration tool. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
