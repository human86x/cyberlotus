from config_tools.flow_tune import load_flow_rates, load_pump_commands
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.arduino import send_command_and_get_response,safe_serial_write, get_serial_connection
import time
#from app import adjust_tank_level
pump_progress = {}



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





###################