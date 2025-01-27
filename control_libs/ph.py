from control_libs.arduino import send_command_and_get_response, get_serial_connection
from control_libs.system_stats import system_state
from control_libs.app_core import load_config, CALIBRATION_FILE
from control_libs.temperature import read_solution_temperature
import time
import json
import statistics

ser = get_serial_connection()



def get_ph(ser):
    response = send_command_and_get_response(ser, b'P')
    if response is not None:
        try:
            #print(f"------------Reading EC:{response}")
            #return float(response)
            
            

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
    


def get_correct_ph():
    global ser
    """
    Get the corrected EC value by reading the EC sensor multiple times, 
    filtering invalid readings, and applying temperature correction and calibration factor.

    Returns:
        int: The corrected EC value as an integer, or None if no valid readings were obtained.
    """
    calibration_factor = get_ph_calibration_factor()
    num_readings = 4  # Change number of readings to 4
    ph_values = []

    print("Collecting EC readings...")
    for _ in range(num_readings):
        time.sleep(1)
        raw_ph_value = get_ph(ser)
        print(f"Retrieved EC value: '{raw_ph_value}'")
        
        # Validate and convert the raw EC value
        if raw_ph_value is None or raw_ph_value == 0:
            print("Error: Invalid EC value read from the sensor.")
            continue
        try:
            raw_ph_value = float(raw_ph_value)
        except ValueError:
            print(f"Error: Invalid EC value '{raw_ph_value}' received, cannot convert to float.")
            continue

        # Only consider values within a realistic range
        if 0 <= raw_ph_value <= 10000:
            ph_values.append(raw_ph_value)
    
    # Check if we have enough valid readings
    if len(ph_values) == 0:
        print("Error: No valid EC readings collected.")
        return None

    # Calculate the median EC value
    estimated_ph_value = statistics.median(ph_values)
    print(f"Estimated EC value (median of valid readings): {estimated_ph_value}")

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
        corrected_ph_value = estimated_ph_value / (1 + 0.02 * (solution_temperature - 25))
        print(f"Corrected EC value at 25°C: {corrected_ph_value}")
    else:
        corrected_ph_value = estimated_ph_value

    # Apply the calibration factor
    corrected_ph_value *= calibration_factor
    print(f"Final corrected EC value after applying calibration factor: {corrected_ph_value}")

    # Convert the final EC value to an integer before returning
    corrected_ph_value = int(round(corrected_ph_value))
    
    ##########################################################
    
    system_state["ph"]["value"] = corrected_ph_value
    system_state["ph"]["timestamp"] = int(time.time())
    
    ##########################################################
    
    return corrected_ph_value
