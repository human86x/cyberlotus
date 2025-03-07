from config_tools.flow_tune import load_flow_rates, load_pump_commands, PUMP_COMMANDS
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.arduino import send_command_and_get_response,safe_serial_write, get_serial_connection
from config_tools.sequencer import execute_sequence
import time
import os
import sys
import json

#script_dir = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(script_dir, "config_tools"))

#from app import adjust_tank_level
pump_progress = {}

ser = get_serial_connection()




def check_chamber_humidity():
    

    print("Chambers are dry, proceeding with the test.")








def generate_adjustment_sequence(target_NPK, NPK, target_pH, pH, target_temp, temp, target_solution, solution, current_volume=4.0, tank_capacity=6.0):
    """
    Generates a sequence of commands based on adjustments needed for NPK, pH, temperature, and solution level.
    Compensates for the dilution effect of adding fresh water.

    Parameters:
        target_NPK (float): Target NPK value.
        NPK (float): Current NPK value.
        target_pH (float): Target pH value.
        pH (float): Current pH value.
        target_temp (float): Target temperature value.
        temp (float): Current temperature value.
        target_solution (float): Target solution level.
        solution (float): Current solution level.
        current_volume (float): Current volume of the solution in the tank (default: 4.0 liters).
        tank_capacity (float): Total capacity of the tank (default: 6.0 liters).

    Returns:
        dict: A dictionary containing the sequence of commands.
    """
    # Calculate adjustments
    NPK_adj = target_NPK - NPK
    pH_adj = target_pH - pH
    temp_adj = target_temp - temp
    solution_adj = target_solution - solution

    # Initialize single and multi commands
    single_commands = {}
    multi_commands = {}

    # Handle solution level adjustment
    if solution_adj > 0:
        # Add fresh water first
        single_commands["fresh_solution"] = solution_adj
        # Update the current volume after adding fresh water
        final_volume = current_volume + solution_adj
    else:
        final_volume = current_volume

    # Handle NPK adjustment (compensate for dilution)
    if NPK_adj != 0:
        # Calculate the required NPK weight to achieve the target concentration in the final volume
        required_NPK = ((target_NPK * final_volume) - (NPK * current_volume)) / 100
        if required_NPK > 0:
            single_commands["NPK"] = required_NPK
        elif required_NPK < 0:
            # If NPK is too high, use solution_waste to remove excess and fresh_solution to dilute
            single_commands["solution_waste"] = abs(required_NPK)
            single_commands["fresh_solution"] = abs(required_NPK)

    # Handle pH adjustment (compensate for dilution)
    if pH_adj != 0:
        # Calculate the required pH chemical weight to achieve the target pH in the final volume
        required_pH = ((target_pH * final_volume) - (pH * current_volume))/100
        if pH_adj < 0:
            single_commands["pH_minus"] = abs(required_pH)
        elif pH_adj > 0:
            single_commands["pH_plus"] = required_pH

    # Always mix the solution at the end
    single_commands["mixer_1"] = 1

    # Generate the sequence file
    compile_sequence_to_file(
        'adjuster_todo.json',
        single_commands=single_commands,
        multi_commands=multi_commands
    )



def compile_sequence_to_file(file_path, single_commands=None, multi_commands=None):
    """
    Compiles a sequence based on input parameters and writes it to a JSON file.

    Parameters:
        file_path (str): Path to the output JSON file.
        single_commands (dict): Dictionary of single commands and their weights.
                               Example: {"NPK": 3, "pH_plus": 1, "mixer_1": 3}
        multi_commands (dict): Dictionary of multiple commands and their weights.
                              Example: {("drain_pH", "solenoid"): 10.1}
    """
    file_path = "sequences/" + file_path
    sequence = []

    # Handle single commands
    if single_commands:
        for command, weight in single_commands.items():
            sequence.append({
                "command": command,
                "weight": float(weight)
            })

    # Handle multiple commands
    if multi_commands:
        for commands, weight in multi_commands.items():
            sequence.append({
                "commands": list(commands),
                "weights": [float(weight)] * len(commands),  # Assign the same weight to all commands
                "calibration": False  # Default calibration flag
            })

    # Create the final sequence_data dictionary
    sequence_data = {
        "sequence": sequence
    }

    # Write the dictionary to a JSON file
    with open(file_path, 'w') as file:
        json.dump(sequence_data, file, indent=4)

    print(f"Sequence file written to {file_path}")

# Example usage





def ph_up(weight):
    print(f"______________weight - {weight}")
    adjust_chemistry("pH_plus", weight)

def ph_down(weight):

    adjust_chemistry("pH_minus", weight)

def nutrients_up(weight):

    adjust_chemistry("NPK", weight)

def nutrients_down(weight):

    #adjust_tank_level(tank_name)
    return None
def temperature_up(weight):

    #adjust_tank_level(tank_name)
    return None

def adjust_chemistry(pump_name, weight):
    #global PUMP_COMMANDS  # Ensure global access
    global PUMP_COMMANDS  # Ensure global access
    PUMP_COMMANDS = load_pump_commands()
    #pump_names = list(PUMP_COMMANDS.keys())
    global ser
    ser = get_serial_connection()
    """Adjusting the chemical balance."""
   
    flow_rates = load_flow_rates()
    print(f"******pump_name======={pump_name}")
    if pump_name not in flow_rates or pump_name not in PUMP_COMMANDS:
        pump_progress[pump_name] = -1  # Error state
        return

    flow_rate = flow_rates[pump_name]
    duration = weight / flow_rate

    #ser.write(f"{PUMP_COMMANDS[pump_name]}o".encode())
    safe_serial_write(PUMP_COMMANDS[pump_name], 'o')  # Turn ON
    for i in range(int(duration * 10)):
        pump_progress[pump_name] = int((i / (duration * 10)) * 100)
        time.sleep(0.1)
        print(f"Adjustment process - {pump_progress[pump_name]}")

    #ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())
    safe_serial_write(PUMP_COMMANDS[pump_name], 'f')  # Turn Off
    pump_progress[pump_name] = 100  # Complete

def condition_monitor():
    global SEQUENCE_DIR  # Ensure SEQUENCE_DIR is defined globally
    
    sequence = "adjuster_todo.json"
    SEQUENCE_FILE = SEQUENCE_DIR + sequence
    flow_rates = load_flow_rates()  # This loads the flow rates as intended
    
        

    if not flow_rates:
        print("Error: Flow rates not loaded.")
        return {}
    global system_state

    target_NPK = system_state["target_NPK"]["value"]
    #system_state["target_NPK"]["timestamp"] = int(time.time())
        
    target_temp = system_state["target_temp"]["value"]
    #system_state["target_temp"]["timestamp"] = int(time.time())
        
    target_pH = system_state["target_pH"]["value"] 
    #system_state["target_pH"]["timestamp"] = int(time.time())
        
    target_solution = system_state["target_solution"]["value"]
    #system_state["target_solution"]["timestamp"] = int(time.time())


    NPK = system_state["ec_solution"]["value"]
    NPK_time = system_state["ec_solution"]["timestamp"]
        
    temp = system_state["temperature"]["value"]
    temp_time = system_state["temperature"]["timestamp"] 
        
    pH = system_state["ph_solution"]["value"] 
    pH_time = system_state["ph_solution"]["timestamp"]
        
    solution = system_state["solution_tank"]["value"]
    solution_time = system_state["solution_tank"]["timestamp"] 

    NPK_adj = target_NPK - NPK
    pH_adj = target_pH - pH
    temp_adj = target_temp - temp
    solution_adj = target_solution - solution
    
    #compile_sequence_to_file('adjuster_todo.json',single_commands={"NPK": NPK_adj,"pH_plus": pH_adj,"mixer_1": 1},multi_commands={("drain_pH", "solenoid"): 10.1})
    # Example usage
    generate_adjustment_sequence(target_NPK, NPK,target_pH, pH,target_temp, temp, target_solution, solution, current_volume=4.0, tank_capacity=6.0)

    execute_sequence(SEQUENCE_FILE, flow_rates)#, 

    #print(f"NPK TO ADJUST:{NPK_adj}   pH TO ADJUST:{pH_adj}    Temperature TO ADJUST:{temp_adj}          SOLUTION LEVEL TO ADJUST:{solution_adj}")

from control_libs.temperature import read_solution_temperature

def temperature_control():
    global system_state
    global PUMP_COMMANDS
    global ser
    pump_name = "heater_1"
    solution_temperature = read_solution_temperature(ser)
    target_temp = system_state["target_temp"]["value"]
    



    if solution_temperature < target_temp:
        print("Heating Up the Solution")
        safe_serial_write(PUMP_COMMANDS[pump_name], 'o')  # Turn ON
    else:
        print("Cooling Off the Solution")
        safe_serial_write(PUMP_COMMANDS[pump_name], 'f')  # Turn OFF

    return None
###################

def load_target_values():
    SYSTEM_STATE_FILE = "data/desired_parameters.json"
    """Loads the system_state dictionary from a JSON file. If the file does not exist, returns an empty default structure."""
    print(f"Loading sys_state from file name:{SYSTEM_STATE_FILE}")
    if not os.path.exists(SYSTEM_STATE_FILE):
        print(f"Path does not exist")
        return None  # Indicate that no previous state exists
    #load_ec_baseline()    
    with open(SYSTEM_STATE_FILE, "r") as f:
        x = json.load(f)
        print(f"Loaded data:{x}")

        target_NPK = x.get('EC')  # Extract the 'value' field
        target_temp = x.get('temperature')  # Extract the 'value' field
        target_pH = x.get('pH')  # Extract the 'value' field
        target_solution = x.get('solution')  # Extract the 'value' field

        system_state["target_NPK"]["value"] = target_NPK
        system_state["target_NPK"]["timestamp"] = int(time.time())
        
        system_state["target_temp"]["value"] = target_temp
        system_state["target_temp"]["timestamp"] = int(time.time())
        
        system_state["target_pH"]["value"] = target_pH
        system_state["target_pH"]["timestamp"] = int(time.time())
        
        system_state["target_solution"]["value"] = target_solution
        system_state["target_solution"]["timestamp"] = int(time.time())
        
        print("Updated Target Values.")
    return None
