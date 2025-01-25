import sys
import os
import json
import time
import statistics
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from control_libs.arduino import get_serial_connection, connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state
from control_libs.app_core import load_config, CALIBRATION_FILE
from config_tools.sequencer import execute_sequence
from config_tools.calibrator import load_calibration_data, save_calibration_data
from control_libs.system_stats import system_state
from control_libs.app_core import SEQUENCE_DIR
from config_tools.flow_tune import load_flow_rates
from control_libs.temperature import read_solution_temperature

ser = get_serial_connection()


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


def get_correct_EC():
    global ser
    """
    Get the corrected EC value by reading the EC sensor multiple times, 
    filtering invalid readings, and applying temperature correction and calibration factor.

    Returns:
        int: The corrected EC value as an integer, or None if no valid readings were obtained.
    """
    calibration_factor = get_EC_calibration_factor()
    num_readings = 4  # Change number of readings to 4
    ec_values = []

    print("Collecting EC readings...")
    for _ in range(num_readings):
        time.sleep(1)
        raw_ec_value = get_ec(ser)
        print(f"Retrieved EC value: '{raw_ec_value}'")
        
        # Validate and convert the raw EC value
        if raw_ec_value is None or raw_ec_value == 0:
            print("Error: Invalid EC value read from the sensor.")
            continue
        try:
            raw_ec_value = float(raw_ec_value)
        except ValueError:
            print(f"Error: Invalid EC value '{raw_ec_value}' received, cannot convert to float.")
            continue

        # Only consider values within a realistic range
        if 0 <= raw_ec_value <= 10000:
            ec_values.append(raw_ec_value)
    
    # Check if we have enough valid readings
    if len(ec_values) == 0:
        print("Error: No valid EC readings collected.")
        return None

    # Calculate the median EC value
    estimated_ec_value = statistics.median(ec_values)
    print(f"Estimated EC value (median of valid readings): {estimated_ec_value}")

    # Read solution temperature
    solution_temperature = read_solution_temperature(ser)
    if solution_temperature is None:
        print("Error: Failed to read solution temperature.")
        return None  # or handle the error gracefully, e.g., retry
    else:
        try:
            solution_temperature = float(solution_temperature)
        except ValueError:
            print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
            return None

    print(f"Solution temperature: {solution_temperature}°C")

    # Apply temperature correction if needed
    if solution_temperature != 25:
        corrected_ec_value = estimated_ec_value / (1 + 0.02 * (solution_temperature - 25))
        print(f"Corrected EC value at 25°C: {corrected_ec_value}")
    else:
        corrected_ec_value = estimated_ec_value

    # Apply the calibration factor
    corrected_ec_value *= calibration_factor
    print(f"Final corrected EC value after applying calibration factor: {corrected_ec_value}")

    # Convert the final EC value to an integer before returning
    corrected_ec_value = int(round(corrected_ec_value))
    
    ##########################################################
    
    system_state["ec"]["value"] = corrected_ec_value
    system_state["ec"]["timestamp"] = int(time.time())
    
    ##########################################################
    
    return corrected_ec_value



def get_ec(ser):
    response = send_command_and_get_response(ser, b'D')
    if response is not None:
        try:
            #print(f"------------Reading EC:{response}")
            #return float(response)
            
            

            return response
        except ValueError:
            print(f"Error reading EC: {response}")
    return None





def get_complex_ec_reading():
    global SEQUENCE_DIR
    """
    Retrieve EC readings by executing the sequence defined in the configuration.

    Returns:
        dict: The readings from the sequence execution.
    """
    try:
        # Load the EC testing sequence from the configuration
        sequence = load_config("EC_test_sequence")
        SEQUENCE_FILE = SEQUENCE_DIR + sequence
        
        # Load flow rates from the configuration
        flow_rates = load_flow_rates()  # This loads the flow rates as intended

        if not flow_rates:
            print("Error: Flow rates not loaded.")
            return {}

        # Execute the sequence and return the readings
        readings = execute_sequence(SEQUENCE_FILE, flow_rates, get_correct_EC)

        # Ensure readings are returned or handle case where no readings are received
        if not readings:
            print("Error: No readings returned from the sequence.")
            readings = {}

        # Update the system state with the EC readings
        system_state["ec"]["value"] = readings
        system_state["ec"]["timestamp"] = int(time.time())
        print(f"Updated the EC values from complex reading using {SEQUENCE_FILE} sequence.")
        
        return readings

    except Exception as e:
        print(f"Error while retrieving EC readings: {e}")
        raise

def get_complex_ec_calibration():
    global SEQUENCE_DIR
    """
    Retrieve EC readings by executing the sequence defined in the configuration.

    Returns:
        dict: The readings from the sequence execution.
    """
    try:
        # Load the EC testing sequence from the configuration
        sequence = load_config("EC_calibration_sequence")
        SEQUENCE_FILE = SEQUENCE_DIR + sequence
        
        # Load flow rates from the configuration
        flow_rates = load_flow_rates()  # This loads the flow rates as intended

        if not flow_rates:
            print("Error: Flow rates not loaded.")
            return {}

        # Execute the sequence and return the readings
        readings = execute_sequence(SEQUENCE_FILE, flow_rates, calibrate_ec_sensor)

        # Ensure readings are returned or handle case where no readings are received
        if not readings:
            print("Error: No readings returned from the sequence.")
            readings = {}

        # Update the system state with the EC readings
        system_state["ec"]["value"] = readings
        system_state["ec"]["timestamp"] = int(time.time())
        print(f"Updated the EC values from complex reading using {SEQUENCE_FILE} sequence.")
        
        return readings

    except Exception as e:
        print(f"Error while retrieving EC readings: {e}")
        raise


def calibrate_ec_sensor():
    global ser
    """
    Calibrate the EC sensor by determining the calibration factor.
    The function performs multiple readings, applies temperature correction, 
    and calculates the calibration factor based on the target EC value.

    Returns:
        dict: Calibration data containing the calibration factor and status.
    """
    print("Starting EC sensor calibration...")
    
    try:
        calibration_data = load_calibration_data()
        target_ec_value = calibration_data.get("EC_calibration_solution", 2000)
        print(f"Target EC value (calibration solution): {target_ec_value}")

        num_readings = 15
        ec_values = []

        # Collect EC readings
        print("Collecting EC readings...")
        for _ in range(num_readings):
            time.sleep(1)
            raw_ec_value = get_ec(ser)
            print(f"Retrieved EC value: '{raw_ec_value}'")

            if raw_ec_value is None or raw_ec_value == 0:
                print("Error: Invalid EC value read from the sensor.")
                continue

            try:
                raw_ec_value = float(raw_ec_value)
            except ValueError:
                print(f"Error: Invalid EC value '{raw_ec_value}' received, cannot convert to float.")
                continue

            if 0 <= raw_ec_value <= 5000:
                ec_values.append(raw_ec_value)

        # Check for valid readings
        if len(ec_values) == 0:
            print("Error: No valid EC readings collected.")
            return {"status": "error", "message": "No valid EC readings collected."}

        # Calculate the median EC value
        estimated_ec_value = statistics.median(ec_values)
        print(f"Estimated EC value (median of valid readings): {estimated_ec_value}")

        # Read solution temperature
        solution_temperature = read_solution_temperature(ser)
        if solution_temperature is None:
            print("Error: Failed to read solution temperature.")
            return {"status": "error", "message": "Failed to read solution temperature."}

        try:
            solution_temperature = float(solution_temperature)
        except ValueError:
            print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
            return {"status": "error", "message": "Invalid temperature value received."}

        print(f"Solution temperature: {solution_temperature}°C")

        # Apply temperature correction
        if solution_temperature != 25:
            corrected_ec_value = estimated_ec_value / (1 + 0.02 * (solution_temperature - 25))
            print(f"Corrected EC value at 25°C: {corrected_ec_value}")
        else:
            corrected_ec_value = estimated_ec_value

        # Calculate calibration factor
        calibration_factor = target_ec_value / corrected_ec_value
        print(f"Calibration factor: {calibration_factor}")

        # Save the calibration data
        calibration_data["EC_calibration_factor"] = calibration_factor
        save_calibration_data(calibration_data)

        # Update system state
        system_state["ec_calibration"] = {
            "value": calibration_factor,
            "timestamp": int(time.time())
        }

        print("EC sensor calibration complete.")
        return {
            "status": "success",
            "calibration_factor": calibration_factor,
            "message": "EC sensor calibration complete."
        }

    except Exception as e:
        print(f"Error during EC sensor calibration: {e}")
        return {"status": "error", "message": f"Unexpected error: {e}"}





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
