import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from control_libs.arduino import connect_to_arduino, send_command_and_get_response


def read_solution_temperature(ser):
    print(f"Trying to obain temperature of the solution through-> {ser}")
    response = send_command_and_get_response(ser, b'T')
    print(f"Result-> {response}")
    
    if response is not None:
        try:
            return float(response)
        except ValueError:
            print(f"Error reading temperature: {response}")
    return None