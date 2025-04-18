from control_libs.arduino import send_command_and_get_response, get_serial_connection
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.temperature import read_solution_temperature
from config_tools.flow_tune import load_flow_rates
from config_tools.sequencer import execute_sequence, execute_commands
from control_libs.electric_conductivity import get_correct_EC, save_ec_baseline, load_ec_baseline, get_ppm
from control_libs.adjuster import check_chamber_humidity
from config_tools.tank_manager import test_tanks
import time
import json
import statistics

ser = get_serial_connection()

import time


def get_chamber_humidity():
    global ser

    response = send_command_and_get_response(ser, b'HH')

    system_state[f"chamber_humidity"]["value"] = response
    system_state[f"chamber_humidity"]["timestamp"] = int(time.time())

    if response is not None:
        try:
            return response
        except ValueError:
            print(f"Error reading Humidity: {response}")
    return None


def get_chamber_temp():
    global ser

    response = send_command_and_get_response(ser, b'HT')

    system_state[f"chamber_temperature"]["value"] = response
    system_state[f"chamber_temperature"]["timestamp"] = int(time.time())

    if response is not None:
        try:
            return response
        except ValueError:
            print(f"Error reading Humidity: {response}")
    return None



def get_plant_temp():
    global ser

    response = send_command_and_get_response(ser, b'PT')

    system_state[f"plant_temperature"]["value"] = response
    system_state[f"plant_temperature"]["timestamp"] = int(time.time())

    if response is not None:
        try:
            return response
        except ValueError:
            print(f"Error reading Humidity: {response}")
    return None