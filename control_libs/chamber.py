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

import time







def light_control(light, state):
    """Control lights based on the specified light and desired state.
    
    Args:
        light (str): Type of light to control ('yellow', 'white', 'grow', or 'all')
        state (str): Desired state ('ON' or 'OFF')
    """
    # Define light constants
    LIGHT_COMMANDS = {
        "yellow": "light_yellow",
        "grow": "light_grow",  # Note: Fixed typo from your original 'grow' vs 'grow'
        "white": "light_white"
    }
    
    # Validate inputs
    if light.lower() not in (*LIGHT_COMMANDS.keys(), "all"):
        raise ValueError(f"Invalid light type: {light}. Must be 'yellow', 'white', 'grow', or 'all'")
    
    if state.upper() not in ("ON", "OFF"):
        raise ValueError(f"Invalid state: {state}. Must be 'ON' or 'OFF'")
    
    # Determine the command value (0 for ON, -1 for OFF)
    command_value = 0 if state.upper() == "ON" else -1
    
    # Handle the light control
    if light.lower() == "all":
        for light_cmd in LIGHT_COMMANDS.values():
            send_command_with_heartbeat(PUMP_COMMANDS[light_cmd], command_value)
    else:
        light_cmd = LIGHT_COMMANDS[light.lower()]
        send_command_with_heartbeat(PUMP_COMMANDS[light_cmd], command_value)




        

def chamber_ambiance():
    #MODIFY FOR TEMP AND HUMIDITY CONTROL
    load_target_values()
    
    target_plant_temp = system_state["target_temp"]["value"]
    #target_chamber_temp = system_state["plant_chamber_target_temperature"]["value"]
    target_chamber_hum = system_state["plant_chamber_target_humidity"]["value"]
    
    target_chamber_temp = system_state["plant_chamber_target_temperature"]["value"]
    
    #target_chambe_humidity = system_state["plant_chamber_target_humidity"]["value"]
    
    while True:  # Continuously loop
        #target_plant_pot_level = load_config("target_plant_pot_level")
        humidifyer = "humidifyer"
        air_heater = "chamber_heater"
        water_heater = "plant_heater"
        #print("Starting circulation – both pumps ON to stabilize")
        #send_command_with_heartbeat(PUMP_COMMANDS[pump_up], 0)
        #send_command_with_heartbeat(PUMP_COMMANDS[pump_down], 0)

        # Retrieve the current plant pot solution level with median filtering
        readings = []
        for _ in range(3):  # Take 3 readings
            
            plant_temp = get_plant_temp()
            chamber_temp = get_chamber_temp()
            chamber_hum = get_chamber_humidity()
            
            
            system_state["plant_temperature"]["value"] = plant_temp
            system_state["plant_temperature"]["timestamp"] = int(time.time())
            
            system_state["chamber_humidity"]["value"] = chamber_hum
            system_state["chamber_humidity"]["timestamp"] = int(time.time())

            system_state["chamber_temperature"]["value"] = chamber_temp
            system_state["chamber_temperature"]["timestamp"] = int(time.time())            
            # Validate the reading
            #try:
            #    plant_level = int(plant_level)
            #    if 1 <= plant_level <= 50:
            #        readings.append(plant_level)
            #    else:
            #        print(f"⚠️ Invalid plant level (out of range): {plant_level}. Retrying...")
            #except (ValueError, TypeError):
            #    print(f"⚠️ Invalid plant level (non-numeric): {plant_level}. Retrying...")
            
            #time.sleep(1)  # Delay between readings

        #if readings:
        #    plant_level = int(statistics.median(readings))  # Use median value
        #else:
        #    print("⚠️ Failed to get valid readings. Retrying...")
        #    continue  # Restart the loop

        print(f"✅ Retrieved : Plant pot temperature: {plant_temp} Chamber temperature: {chamber_temp} Chamber Humidity: {chamber_hum}")

        # Update system state
        #system_state["plant_pot_level"]["value"] = plant_level
        #system_state["plant_pot_level"]["timestamp"] = int(time.time())

        #print(f"Plant pot current water level is {plant_temp} and target level is {target_plant_temp}")

        # Define the acceptable margin
        LEVEL_MARGIN = 0.2
######################   PLAN POT TEMPERATURE    ########################
        # Control logic based on the level with margin
        level_difference = plant_temp - target_plant_temp

        if abs(level_difference) <= LEVEL_MARGIN:
            print("Within acceptable range - water heater is off")
            send_command_with_heartbeat(PUMP_COMMANDS[water_heater], -1)  # Adjust these values as needed for circulation

        elif level_difference < -LEVEL_MARGIN:
            print("Turning water heating...")
            send_command_with_heartbeat(PUMP_COMMANDS[water_heater], 0)
          
        else:  # level_difference > LEVEL_MARGIN
            print("Water heating is OFF...")
            send_command_with_heartbeat(PUMP_COMMANDS[water_heater], -1)
        #time.sleep(5)  # Wait before checking again

######################   CHAMBER TEMPERATURE     #######################
        level_difference = chamber_temp - target_chamber_temp
        print(f"level_difference->{level_difference}  chamber_temp->{chamber_temp} target_temp->{target_chamber_temp}")
        if abs(level_difference) <= LEVEL_MARGIN:
            print("Within acceptable range - air heater is off")
            send_command_with_heartbeat(PUMP_COMMANDS[air_heater], -1)  # Adjust these values as needed for circulation

        elif level_difference < -LEVEL_MARGIN:
            print("Turning air heating...")
            send_command_with_heartbeat(PUMP_COMMANDS[air_heater], 0)
          
        else:  # level_difference > LEVEL_MARGIN
            print("Air heating is OFF...")
            send_command_with_heartbeat(PUMP_COMMANDS[air_heater], -1)
        #time.sleep(5)  # Wait before checking again

########################   HUMIDITY   ############################        
        level_difference = chamber_hum - target_chamber_hum

        if abs(level_difference) <= LEVEL_MARGIN:
            print("Within acceptable range - HUMIDIFYER is off")
            send_command_with_heartbeat(PUMP_COMMANDS[humidifyer], -1)  # Adjust these values as needed for circulation

        elif level_difference < -LEVEL_MARGIN:
            print("Turning HUIDIFYER ON!...")
            send_command_with_heartbeat(PUMP_COMMANDS[humidifyer], 0)
          
        else:  # level_difference > LEVEL_MARGIN
            print("HUMIDIFYER is OFF...")
            send_command_with_heartbeat(PUMP_COMMANDS[humidifyer], -1)
        #time.sleep(5)  # Wait before checking again


















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