from control_libs.arduino import send_command_and_get_response, get_serial_connection
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.temperature import read_solution_temperature
from config_tools.flow_tune import load_flow_rates
from config_tools.sequencer import execute_sequence
from control_libs.electric_conductivity import get_correct_EC
import time
import json
import statistics

ser = get_serial_connection()

def get_ph_and_ec():

    a = get_correct_EC()
    b = get_correct_ph()
    c = f"{a}!{b}"
    return c


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

def get_ph_calibration_factor_low():
    try:
        with open(CALIBRATION_FILE, "r") as file:
            calibration_data = json.load(file)
            x = float(calibration_data.get("pH_calibration_LOW", 1.0))
            
            system_state[f"ph_calibration_LOW"]["value"] = x
            system_state[f"ph_calibration_LOW"]["timestamp"] = int(time.time())
            #print(f"Updated the pH values from complex reading using {SEQUENCE_FILE} sequence.")
            save_system_state(system_state)
            return x
    except FileNotFoundError:
        print(f"Calibration file {CALIBRATION_FILE} not found. Using default calibration factor of 1.0.")
        return 1.0
    except Exception as e:
        print(f"Error loading calibration factor: {e}")
        return 1.0
    #system_state[f"ph_calibration_{calibration_type}"]["value"] = readings
        #system_state[f"ph_calibration_{calibration_type}"]["timestamp"] = int(time.time())
        #print(f"Updated the pH values from complex reading using {SEQUENCE_FILE} sequence.")
        
def get_ph_calibration_factor_high():
    try:
        with open(CALIBRATION_FILE, "r") as file:
            calibration_data = json.load(file)
            x = float(calibration_data.get("pH_calibration_HIGH", 1.0))
            system_state[f"ph_calibration_HIGH"]["value"] = x
            system_state[f"ph_calibration_HIGH"]["timestamp"] = int(time.time())
            #print(f"Updated the pH values from complex reading using {SEQUENCE_FILE} sequence.")
            save_system_state(system_state)
            return x
    except FileNotFoundError:
        print(f"Calibration file {CALIBRATION_FILE} not found. Using default calibration factor of 1.0.")
        return 1.0
    except Exception as e:
        print(f"Error loading calibration factor: {e}")
        return 1.0

def calibrate_ph(calibration_type):
    """
    Calibrate the pH sensor using a known calibration solution.

    Args:
        calibration_type (str): "LOW" for pH 4 or "HIGH" for pH 9 calibration.

    Returns:
        float: The calculated calibration factor.
    """
    if calibration_type not in ["LOW", "HIGH"]:
        print("Error: Invalid calibration type. Use 'LOW' or 'HIGH'.")
        return None

    # Define the target pH value based on calibration type
    target_ph = 4.0 if calibration_type == "LOW" else 9.0

    print(f"Starting pH calibration for {calibration_type} solution (Target pH: {target_ph})...")

    # Read solution temperature
    #solution_temperature = read_solution_temperature(ser)
    #if solution_temperature is None:
    #    print("Error: Failed to read solution temperature.")
    #    return None

    #try:
    #    solution_temperature = float(solution_temperature)
    #except ValueError:
    #    print(f"Error: Invalid temperature value '{solution_temperature}' received, cannot convert to float.")
    #    return None

    #print(f"Solution temperature: {solution_temperature}°C")

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
            print(f"***********Raw pH value {raw_ph_value}")
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
    #if solution_temperature != 25:
    #    corrected_ph_value = estimated_ph_value / (1 + 0.02 * (solution_temperature - 25))
    #    print(f"Corrected pH value at 25°C: {corrected_ph_value}")
    #else:
    #    corrected_ph_value = estimated_ph_value

    # Calculate the calibration factor
    #print(f"***********Target pH value {target_ph}")
    #calibration_factor =  corrected_ph_value / target_ph 
    #print(f"Calculated calibration factor: {calibration_factor}")


    # Save the calibration factor to the calibration file
    try:
        with open(CALIBRATION_FILE, "r") as file:
            calibration_data = json.load(file)
    except FileNotFoundError:
        calibration_data = {}
    except Exception as e:
        print(f"Error reading calibration file: {e}")
        calibration_data = {}

    #calibration_data["pH_calibration_factor"] = calibration_factor
    calibration_data[f"pH_calibration_{calibration_type}"] = estimated_ph_value
    
    system_state[f"ph_calibration_{calibration_type}"]["value"] = estimated_ph_value
    system_state[f"ph_calibration_{calibration_type}"]["timestamp"] = int(time.time())
    save_system_state(system_state)
    try:
        with open(CALIBRATION_FILE, "w") as file:
            json.dump(calibration_data, file, indent=4)
        print(f"Calibration factor saved to {CALIBRATION_FILE}.")
    except Exception as e:
        print(f"Error saving calibration factor: {e}")

    return estimated_ph_value



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
        #system_state[f"ph_calibration_{calibration_type}"]["value"] = readings
        #system_state[f"ph_calibration_{calibration_type}"]["timestamp"] = int(time.time())
        print(f"Updated the pH values from complex reading using {SEQUENCE_FILE} sequence.")
        
        return readings

    except Exception as e:
        print(f"Error while retrieving pH readings: {e}")
        raise






def get_correct_ph():
    global ser
    #calibration_factor = get_ph_calibration_factor()
    low_ph = 4.0
    high_ph = 9.0
    low_raw_value = get_ph_calibration_factor_low()
    high_raw_value = get_ph_calibration_factor_high()


    num_readings = 10
    ph_values = []

    print("Collecting pH readings...")
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

        if 700 <= raw_ph_value <= 1024:
            ph_values.append(raw_ph_value)

    if len(ph_values) == 0:
        print("Error: No valid pH readings collected.")
        return None

    estimated_ph_value = statistics.median(ph_values)
    print(f"Estimated pH value (median of valid readings): {estimated_ph_value}")
#######################



    

    # Calculate the slope (m) of the line connecting the two calibration points
    slope = (high_ph - low_ph) / (high_raw_value - low_raw_value)

    # Calculate the intercept (b) of the line
    intercept = low_ph - slope * low_raw_value

    # Apply the linear equation to calculate the pH value
    estimated_ph_value = slope * raw_ph_value + intercept




#######################
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

    if solution_temperature != 25:
        corrected_ph_value = estimated_ph_value / (1 + 0.02 * (solution_temperature - 25))
        print(f"Corrected pH value at 25°C: {corrected_ph_value}")
    else:
        corrected_ph_value = estimated_ph_value
    
    #corrected_ph_value =  corrected_ph_value / calibration_factor
    print(f"Final corrected pH value after applying calibration factor is: {corrected_ph_value}")

    corrected_ph_value = round(corrected_ph_value, 2)

    system_state["ph"]["value"] = corrected_ph_value
    system_state["ph"]["timestamp"] = int(time.time())

    return corrected_ph_value



def perform_ph_test(test_type):
    global SEQUENCE_DIR
    """
    Retrieve pH readings by executing the sequence defined in the configuration.

    Returns:
        dict: The readings from the sequence execution.

    
    """
    if test_type == "solution":
        sequence = load_config("pH_solution_test_sequence")
    else:
        sequence = load_config("pH_baseline_test_sequence")

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
        readings = execute_sequence(SEQUENCE_FILE, flow_rates, get_ph_and_ec)
        # Example of processing the returned data
        data = readings  
        ec_value, ph_value = data.split("!")

        # Convert to proper types
        ec_value = int(ec_value)  # Convert EC to integer
        ph_value = float(ph_value)  # Convert pH to float

        print(f"EC: {ec_value}, pH: {ph_value}")
        # Ensure readings are returned or handle case where no readings are received
        if not readings:
            print("Error: No readings returned from the sequence.")
            readings = {}
        
        print(f"**********TEST TYPE IS {test_type}")
     
        # Update the system state with the pH readings
        if test_type == "solution":
            system_state[f"ph_solution"]["value"] = ph_value
            system_state[f"ph_solution"]["timestamp"] = int(time.time())
            print(f"Updated the pH Solution values from complex reading using {SEQUENCE_FILE} sequence.")
            save_system_state(system_state)
            history_log("pH", ph_value)
            ###############ec############
            system_state["ec"]["value"] = ec_value
            system_state["ec"]["timestamp"] = int(time.time())
        
            system_state["ec_solution"]["value"] = ec_value
            system_state["ec_solution"]["timestamp"] = int(time.time())
            history_log("EC", ec_value)
        
            save_system_state(system_state)




        else:
            system_state[f"ph_baseline"]["value"] = ph_value
            system_state[f"ph_baseline"]["timestamp"] = int(time.time())
            print(f"Updated the pH Baseline values from complex reading using {SEQUENCE_FILE} sequence.")
            save_system_state(system_state)
            history_log("pH_baseline", ph_value)


                    # Update the system state with the EC readings
            system_state["ec_baseline"]["value"] = ec_value
            system_state["ec_baseline"]["timestamp"] = int(time.time())
            print(f"Updated the EC baseline using {SEQUENCE_FILE} sequence.")
            history_log("EC_baseline", ec_value)


        return readings

    except Exception as e:
        print(f"Error while retrieving pH readings: {e}")
        raise



