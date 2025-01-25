import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from control_libs.arduino import connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state
from control_libs.app_core import load_config
from config_tools.sequencer import execute_sequence
from config_tools.calibrator import get_correct_EC





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
    """
    Retrieve EC readings by executing the sequence defined in the configuration.

    Returns:
        dict: The readings from the sequence execution.
    """
    try:
        # Load the EC testing sequence from the configuration
        sequence = load_config("ec_testing_sequence")

        # Get the correct EC flow rates (assumes get_correct_EC is implemented elsewhere)
        flow_rates = get_correct_EC()

        # Execute the sequence and return the readings
        readings = execute_sequence(sequence, flow_rates, calibration_callback=None)
        
         ##########################################################
    
        system_state["ec"]["value"] = readings
        system_state["ec"]["timestamp"] = int(time.time())
        print(f"Updated the EC values from complex reading using a {sequence} sequence.")
    
    ##########################################################
        
        return readings
    except Exception as e:
        print(f"Error while retrieving EC readings: {e}")
        raise