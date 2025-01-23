import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from control_libs.arduino import connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state

def read_solution_temperature(ser):
    print(f"Trying to obain temperature of the solution through-> {ser}")
    response = send_command_and_get_response(ser, b'T')
    print(f"Result-> {response}")
    #system_state["temperature"] = response
    #system_state["timestamp"] = response
    
    system_state["temperature"]["value"] = response
    system_state["temperature"]["timestamp"] = int(time.time())
    if response is not None:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading temperature: {response}")
    return None