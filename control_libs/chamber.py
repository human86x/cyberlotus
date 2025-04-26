from control_libs.arduino import send_command_and_get_response, get_serial_connection
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.temperature import read_solution_temperature
from config_tools.flow_tune import load_flow_rates, PUMP_COMMANDS, send_command_with_heartbeat
from config_tools.sequencer import execute_sequence, execute_commands
from control_libs.electric_conductivity import get_correct_EC, save_ec_baseline, load_ec_baseline, get_ppm
from control_libs.adjuster import check_chamber_humidity, load_target_values
from config_tools.tank_manager import test_tanks
import time
import json
import statistics

ser = get_serial_connection()

import datetime
import math






def light_control(light, state):
    """Control lights based on the specified light and desired state and update system state.
    
    Args:
        light (str): Type of light to control ('yellow', 'white', 'grow', or 'all')
        state (str): Desired state ('ON' or 'OFF')
        system_state (dict): Dictionary tracking the state of all system components
    """
    # Define light constants
    LIGHT_COMMANDS = {
        "yellow": "light_yellow",
        "grow": "light_grow",
        "white": "light_white"
    }
    
    # Validate inputs
    if light.lower() not in (*LIGHT_COMMANDS.keys(), "all"):
        raise ValueError(f"Invalid light type: {light}. Must be 'yellow', 'white', 'grow', or 'all'")
    
    if state.upper() not in ("ON", "OFF"):
        raise ValueError(f"Invalid state: {state}. Must be 'ON' or 'OFF'")
    
    # Determine the command value (0 for ON, -1 for OFF)
    command_value = 0 if state.upper() == "ON" else -1
    new_state = "ON" if command_value == 0 else "OFF"
    #current_time = datetime.datetime.utcnow().isoformat() + "Z"  # Adds Z for UTC time
    current_time = int(time.time())
    # Handle the light control and state tracking
    if light.lower() == "all":
        for light_name, light_cmd in LIGHT_COMMANDS.items():
            send_command_with_heartbeat(PUMP_COMMANDS[light_cmd], command_value)
            system_state[light_cmd]["state"] = new_state
            system_state[light_cmd]["timestamp"] = current_time
    else:
        light_cmd = LIGHT_COMMANDS[light.lower()]
        send_command_with_heartbeat(PUMP_COMMANDS[light_cmd], command_value)
        system_state[light_cmd]["state"] = new_state
        system_state[light_cmd]["timestamp"] = current_time
    
    return system_state
        
def chamber_ambiance():
    #MODIFY FOR TEMP AND HUMIDITY CONTROL
    load_target_values()
    
    target_plant_temp = system_state["target_temp"]["value"]
    target_chamber_hum = system_state["plant_chamber_target_humidity"]["value"]
    target_chamber_temp = system_state["plant_chamber_target_temperature"]["value"]
    
    while True:  # Continuously loop
        humidifyer = "humidifyer"
        air_heater = "chamber_heater"
        water_heater = "plant_heater"
        current_time = int(time.time())
        
        try:
            # Get sensor readings with error handling
            plant_temp = get_plant_temp()
            chamber_temp = get_chamber_temp()
            chamber_hum = get_chamber_humidity()
            
            # Validate readings
            if any(math.isnan(x) or x is None for x in [plant_temp, chamber_temp, chamber_hum]):
                raise ValueError("One or more sensor readings are NaN/None")
                
            # Log valid readings
            history_log("plant_temp", plant_temp)
            history_log("chamber_temp", chamber_temp)
            history_log("chamber_humidity", chamber_hum)

            # Update system state
            system_state["plant_temperature"]["value"] = plant_temp
            system_state["plant_temperature"]["timestamp"] = current_time
            system_state["chamber_humidity"]["value"] = chamber_hum
            system_state["chamber_humidity"]["timestamp"] = current_time
            system_state["chamber_temperature"]["value"] = chamber_temp
            system_state["chamber_temperature"]["timestamp"] = current_time
            
            print(f"✅ Retrieved: Plant temp: {plant_temp}°C, Chamber temp: {chamber_temp}°C, Humidity: {chamber_hum}%")

            # Define the acceptable margin
            LEVEL_MARGIN = 0.2
            
            # Always turn lights on (assuming this is safe)
            light_control("all","ON")

            ###################### PLAN POT TEMPERATURE ########################
            if not math.isnan(plant_temp):
                level_difference = plant_temp - target_plant_temp

                if abs(level_difference) <= LEVEL_MARGIN:
                    print("Within acceptable range - water heater is off")
                    send_command_with_heartbeat(PUMP_COMMANDS[water_heater], -1)
                    system_state["water_heater"]["state"] = "OFF"
                    system_state["water_heater"]["timestamp"] = current_time
                elif level_difference < -LEVEL_MARGIN:
                    print("Turning water heating ON...")
                    send_command_with_heartbeat(PUMP_COMMANDS[water_heater], 0)
                    system_state["water_heater"]["state"] = "ON"
                    system_state["water_heater"]["timestamp"] = current_time
                else:
                    print("Water heating is OFF...")
                    send_command_with_heartbeat(PUMP_COMMANDS[water_heater], -1)
                    system_state["water_heater"]["state"] = "OFF"
                    system_state["water_heater"]["timestamp"] = current_time
            else:
                print("⚠️ Invalid plant temperature reading, skipping water heater control")

            ###################### CHAMBER TEMPERATURE #######################
            if not math.isnan(chamber_temp):
                level_difference = chamber_temp - target_chamber_temp
                print(f"Temp diff: {level_difference}°C (Current: {chamber_temp}°C, Target: {target_chamber_temp}°C)")
                
                if abs(level_difference) <= LEVEL_MARGIN:
                    print("Within acceptable range - air heater is off")
                    send_command_with_heartbeat(PUMP_COMMANDS[air_heater], -1)
                    system_state["air_heater"]["state"] = "OFF"
                    system_state["air_heater"]["timestamp"] = current_time
                elif level_difference < -LEVEL_MARGIN:
                    print("Turning air heating ON...")
                    send_command_with_heartbeat(PUMP_COMMANDS[air_heater], 0)
                    system_state["air_heater"]["state"] = "ON"
                    system_state["air_heater"]["timestamp"] = current_time
                else:
                    print("Air heating is OFF...")
                    send_command_with_heartbeat(PUMP_COMMANDS[air_heater], -1)
                    system_state["air_heater"]["state"] = "OFF"
                    system_state["air_heater"]["timestamp"] = current_time
            else:
                print("⚠️ Invalid chamber temperature reading, skipping air heater control")

            ######################## HUMIDITY ############################        
            if not math.isnan(chamber_hum):
                level_difference = chamber_hum - target_chamber_hum

                if abs(level_difference) <= LEVEL_MARGIN:
                    print("Within acceptable range - HUMIDIFIER is off")
                    send_command_with_heartbeat(PUMP_COMMANDS[humidifyer], -1)
                    system_state["air_humidifyer"]["state"] = "OFF"
                    system_state["air_humidifyer"]["timestamp"] = current_time
                elif level_difference < -LEVEL_MARGIN:
                    print("Turning HUMIDIFIER ON...")
                    send_command_with_heartbeat(PUMP_COMMANDS[humidifyer], 0)
                    system_state["air_humidifyer"]["state"] = "ON"
                    system_state["air_humidifyer"]["timestamp"] = current_time
                else:
                    print("HUMIDIFIER is OFF...")
                    send_command_with_heartbeat(PUMP_COMMANDS[humidifyer], -1)
                    system_state["air_humidifyer"]["state"] = "OFF"
                    system_state["air_humidifyer"]["timestamp"] = current_time
            else:
                print("⚠️ Invalid humidity reading, skipping humidifier control")

        except Exception as e:
            print(f"⚠️ Error in chamber ambiance control: {str(e)}")
            # Optionally log the full traceback for debugging:
            # import traceback
            # traceback.print_exc()
            
        # Wait before next iteration
        time.sleep(5)  # Adjust as needed

















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
    return response


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
    return response



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
    return response