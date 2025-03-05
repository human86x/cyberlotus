from config_tools.flow_tune import load_flow_rates, load_pump_commands
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.arduino import send_command_and_get_response,safe_serial_write, get_serial_connection
import time
import os
import sys
import json

#script_dir = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(script_dir, "config_tools"))

#from app import adjust_tank_level
pump_progress = {}

ser = get_serial_connection()

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

    print(f"NPK TO ADJUST:{NPK_adj}   pH TO ADJUST:{pH_adj}    Temperature TO ADJUST:{temp_adj}          SOLUTION LEVEL TO ADJUST:{solution_adj}")

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
