from control_libs.arduino import send_command_and_get_response, get_serial_connection
from control_libs.system_stats import system_state
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.temperature import read_solution_temperature
from config_tools.flow_tune import load_flow_rates
from config_tools.sequencer import execute_sequence
import time
import json
import statistics

ser = get_serial_connection()

def get_ph(ser):
    response = send_command_and_get_response(ser, b'P')

    system_state[f"ph_raw"]["value"] = response
    system_state[f"ph_raw"]["timestamp"] = int(time.time())

    if response is not None:
        try:
            return response
        except ValueError:
            print(f"Error reading pH: {response}")
    return None

def get_ph_calibration_factor():
    try:
        with open(CALIBRATION_FILE, "r") as file:
            calibration_data = json.load(file)
            return float(calibration_data.get("pH_calibration_factor", 1.0))
    except FileNotFoundError:
        print(f"Calibration file {CALIBRATION_FILE} not found. Using default calibration factor of 1.0.")
        return 1.0
    except Exception as e:
        print(f"Error loading calibration factor: {e}")
        return 1.0

import time
import statistics
import json

CALIBRATION_FILE = "calibration_data.json"
system_state = {"ph_calibration_LOW": {}, "ph_calibration_HIGH": {}}

def calibrate_ph(calibration_type):
    """
    Calibrate the pH sensor using a known calibration solution.

    Args:
        calibration_type (str): "LOW" for pH 4 or "HIGH" for pH 9 calibration.

    Returns:
        dict: A dictionary containing slope, intercept, and calibration factor.
    """
    if calibration_type not in ["LOW", "HIGH"]:
        print("Error: Invalid calibration type. Use 'LOW' or 'HIGH'.")
        return None

    # Define the target pH value based on calibration type
    target_ph = 4.0 if calibration_type == "LOW" else 9.0

    print(f"Starting pH calibration for {calibration_type} solution (Target pH: {target_ph})...")

    # Read solution temperature
    solution_temperature = read_solution_temperature(ser)
    if solution_temperature is None:
        print("Error: Failed to read solution temperature.")
        return None

    try:
        solution_temperature = float(solution_temperature)
    except ValueError:
        print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
        return None

    print(f"Solution temperature: {solution_temperature}°C")

    # Collect multiple pH readings
    num_readings = 4
    ph_values = []

    for _ in range(num_readings):
        time.sleep(1)
        raw_ph_value = get_ph(ser)
        print(f"Retrieved pH value: '{raw_ph_value}'")

        if raw_ph_value is None:
            print("Error: Invalid pH value read from the sensor.")
            continue

        try:
            raw_ph_value = float(raw_ph_value)
        except ValueError:
            print(f"Error: Invalid pH value '{raw_ph_value}' received, cannot convert to float.")
            continue

        ph_values.append(raw_ph_value)

    if len(ph_values) == 0:
        print("Error: No valid pH readings collected.")
        return None

    # Calculate the median pH value from readings
    estimated_ph_value = statistics.median(ph_values)
    print(f"Estimated pH value (median of valid readings): {estimated_ph_value}")

    # Apply temperature correction if needed
    if solution_temperature != 25:
        corrected_ph_value = estimated_ph_value / (1 + 0.02 * (solution_temperature - 25))
        print(f"Corrected pH value at 25°C: {corrected_ph_value}")
    else:
        corrected_ph_value = estimated_ph_value

    # Save the raw calibration data
    try:
        with open(CALIBRATION_FILE, "r") as file:
            calibration_data = json.load(file)
    except FileNotFoundError:
        calibration_data = {}
    except Exception as e:
        print(f"Error reading calibration file: {e}")
        calibration_data = {}

    calibration_data[f"raw_{calibration_type}_value"] = corrected_ph_value
    calibration_data[f"target_{calibration_type}_pH"] = target_ph

    # Save updated calibration data to file
    try:
        with open(CALIBRATION_FILE, "w") as file:
            json.dump(calibration_data, file, indent=4)
        print(f"Calibration data saved to {CALIBRATION_FILE}.")
    except Exception as e:
        print(f"Error saving calibration data: {e}")

    if "raw_LOW_value" in calibration_data and "raw_HIGH_value" in calibration_data:
        # Calculate the slope and intercept
        low_reading = calibration_data["raw_LOW_value"]
        high_reading = calibration_data["raw_HIGH_value"]
        slope = (9.0 - 4.0) / (high_reading - low_reading)
        intercept = 4.0 - slope * low_reading

        # Save slope and intercept
        calibration_data["slope"] = slope
        calibration_data["intercept"] = intercept

        try:
            with open(CALIBRATION_FILE, "w") as file:
                json.dump(calibration_data, file, indent=4)
            print(f"Slope and intercept saved to {CALIBRATION_FILE}.")
        except Exception as e:
            print(f"Error saving slope and intercept: {e}")

        print(f"Calibration complete. Slope: {slope}, Intercept: {intercept}")
        return {"slope": slope, "intercept": intercept, "calibration_factor": corrected_ph_value}
    else:
        print(f"Waiting for both LOW and HIGH calibration to calculate slope and intercept.")
        return None



def perform_ph_calibration(calibration_type):
    global SEQUENCE_DIR
    """
    Retrieve pH readings by executing the sequence defined in the configuration.

    Returns:
        dict: The readings from the sequence execution.

    
    """
    if calibration_type == "LOW":
        sequence = load_config("pH_calibration_low_sequence")
    else:
        sequence = load_config("pH_calibration_high_sequence")

    try:
        # Load the pH testing sequence from the configuration
        #sequence = load_config("pH_calibration_sequence")
        SEQUENCE_FILE = SEQUENCE_DIR + sequence
        
        # Load flow rates from the configuration
        flow_rates = load_flow_rates()  # This loads the flow rates as intended

        if not flow_rates:
            print("Error: Flow rates not loaded.")
            return {}

        # Execute the sequence and return the readings
        print(f"Sending sequence file to the sequencer {SEQUENCE_FILE}.")
        
        #sreadings = execute_sequence(SEQUENCE_FILE, flow_rates, calibrate_ph(calibration_type))
        readings = execute_sequence(SEQUENCE_FILE, flow_rates, lambda: calibrate_ph(calibration_type))

        # Ensure readings are returned or handle case where no readings are received
        if not readings:
            print("Error: No readings returned from the sequence.")
            readings = {}

        # Update the system state with the pH readings
        system_state[f"ph_calibration_{calibration_type}"]["value"] = readings
        system_state[f"ph_calibration_{calibration_type}"]["timestamp"] = int(time.time())
        print(f"Updated the pH values from complex reading using {SEQUENCE_FILE} sequence.")
        
        return readings

    except Exception as e:
        print(f"Error while retrieving pH readings: {e}")
        raise






def get_correct_ph():
    """
    Retrieve and correct pH value using saved calibration factor.

    Returns:
        float: Corrected pH value or None if an error occurs.
    """
    global ser

    # Retrieve the calibration factor
    calibration_factor = get_ph_calibration_factor()
    if calibration_factor is None:
        print("Error: Calibration factor not found or invalid.")
        return None

    num_readings = 4
    ph_values = []

    print("Collecting pH readings...")
    for _ in range(num_readings):
        time.sleep(1)
        raw_ph_value = get_ph(ser)
        print(f"Retrieved raw pH value: '{raw_ph_value}'")

        if raw_ph_value is None:
            print("Warning: Invalid pH value read from the sensor, skipping.")
            continue

        try:
            raw_ph_value = float(raw_ph_value)
        except ValueError:
            print(f"Warning: Invalid pH value '{raw_ph_value}' received, skipping.")
            continue

        if 0 <= raw_ph_value <= 14:
            ph_values.append(raw_ph_value)
        else:
            print(f"Warning: Raw pH value '{raw_ph_value}' out of valid range, skipping.")

    if len(ph_values) == 0:
        print("Error: No valid pH readings collected.")
        return None

    # Calculate the median pH value from readings
    estimated_ph_value = statistics.median(ph_values)
    print(f"Estimated pH value (median of valid readings): {estimated_ph_value}")

    # Retrieve the solution temperature
    solution_temperature = read_solution_temperature(ser)
    if solution_temperature is None:
        print("Error: Failed to read solution temperature.")
        return None

    try:
        solution_temperature = float(solution_temperature)
    except ValueError:
        print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
        return None

    print(f"Solution temperature: {solution_temperature}°C")

    # Apply temperature correction if the temperature is not 25°C
    if solution_temperature != 25:
        corrected_ph_value = estimated_ph_value / (1 + 0.02 * (solution_temperature - 25))
        print(f"Temperature-corrected pH value at 25°C: {corrected_ph_value}")
    else:
        corrected_ph_value = estimated_ph_value

    # Apply the calibration factor
    corrected_ph_value *= calibration_factor
    print(f"Final corrected pH value after applying calibration factor: {corrected_ph_value}")

    # Round the corrected value to two decimal places
    corrected_ph_value = round(corrected_ph_value, 2)

    # Update system state
    system_state["ph"]["value"] = corrected_ph_value
    system_state["ph"]["timestamp"] = int(time.time())

    return corrected_ph_value
