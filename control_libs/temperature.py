import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from control_libs.arduino import connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state



def read_solution_temperature(ser, max_retries=3, min_temp=1, max_temp=30):
    """
    Retrieve temperature of the solution and ensure it's within the valid range.

    Parameters:
        ser: Serial connection object to communicate with the device.
        max_retries (int): The maximum number of retries if the reading is out of range or invalid.
        min_temp (float): Minimum valid temperature (in °C).
        max_temp (float): Maximum valid temperature (in °C).
    
    Returns:
        float: Valid temperature reading if successful, or None if invalid after retries.
    """
    retries = 0
    while retries < max_retries:
        print(f"Trying to obtain temperature of the solution through -> {ser}")
        response = send_command_and_get_response(ser, b'T')
        print(f"Result -> {response}")
        
        # Validate the response before proceeding
        if response is not None:
            try:
                temperature = float(response)
                
                # Check if temperature is within the valid range
                if min_temp <= temperature <= max_temp:
                    # Update system state with the valid temperature
                    system_state["temperature"]["value"] = temperature
                    system_state["temperature"]["timestamp"] = int(time.time())
                    return temperature
                else:
                    print(f"Error: Temperature {temperature}°C out of range. Retrying...")
            except ValueError:
                print(f"Error: Invalid temperature reading '{response}'. Retrying...")
        
        retries += 1
        time.sleep(1)  # Wait before retrying
    
    print("Error: Failed to obtain a valid temperature after retries.")
    return None
