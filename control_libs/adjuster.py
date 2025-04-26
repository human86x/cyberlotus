from config_tools.flow_tune import load_flow_rates, send_command_with_heartbeat, load_pump_commands, PUMP_COMMANDS
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.arduino import send_command_and_get_response,safe_serial_write, get_serial_connection
from config_tools.sequencer import execute_sequence

import time
import os
import sys
import json
import statistics
#script_dir = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(script_dir, "config_tools"))

#from app import adjust_tank_level
pump_progress = {}

ser = get_serial_connection()







#import time
import statistics





def circulate_solution():
    while True:  # Continuously loop
        target_plant_pot_level = load_config("target_plant_pot_level")
        system_state["plant_pot_target_level"]["value"] = plant_level
        system_state["plant_pot_target_level"]["timestamp"] = int(time.time())
        pump_up = "plant_up"
        pump_down = "plant_down"
        print("Starting circulation – both pumps ON to stabilize")
        #send_command_with_heartbeat(PUMP_COMMANDS[pump_up], 0)
        #send_command_with_heartbeat(PUMP_COMMANDS[pump_down], 0)

        # Retrieve the current plant pot solution level with median filtering
        readings = []
        for _ in range(3):  # Take 3 readings
            plant_level = send_command_and_get_response(ser, b'C')
            system_state["plant_pot_level"]["value"] = plant_level
            system_state["plant_pot_level"]["timestamp"] = int(time.time())
            
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

        print(f"✅ Retrieved valid plant pot solution level: {plant_level} (median of 3 readings)")

        # Update system state
        system_state["plant_pot_level"]["value"] = plant_level
        system_state["plant_pot_level"]["timestamp"] = int(time.time())

        print(f"Plant pot current water level is {plant_level} and target level is {target_plant_pot_level}")

        # Define the acceptable margin
        LEVEL_MARGIN = 0.2

        # Control logic based on the level with margin
        level_difference = plant_level - target_plant_pot_level

        if abs(level_difference) <= LEVEL_MARGIN:
            print("Within acceptable range - both pumps ON to maintain circulation")
            send_command_with_heartbeat(PUMP_COMMANDS[pump_up], 0)  # Adjust these values as needed for circulation
            send_command_with_heartbeat(PUMP_COMMANDS[pump_down], 0)
            return
        elif level_difference < -LEVEL_MARGIN:
            print("Draining the plant pot...")
            send_command_with_heartbeat(PUMP_COMMANDS[pump_up], -1)
            send_command_with_heartbeat(PUMP_COMMANDS[pump_down], 0)
        else:  # level_difference > LEVEL_MARGIN
            print("Adding more solution to the pot...")
            send_command_with_heartbeat(PUMP_COMMANDS[pump_up], 0)
            send_command_with_heartbeat(PUMP_COMMANDS[pump_down], -1)
        #time.sleep(5)  # Wait before checking again


def get_ppm(baseline, ec):
    global system_state
    
    #load_ec_baseline()
    #ec = system_state["ec_solution"]["value"]
    #baseline = system_state["ec_baseline"]["value"]
    ppm = float(ec) - float(baseline)
    print(f"*****PPM:{ppm}")
    return ppm


def check_chamber_humidity():
    global SEQUENCE_DIR  # Ensure SEQUENCE_DIR is defined globally
    
    sequence = "sensors_drain.json"
    SEQUENCE_FILE = SEQUENCE_DIR + sequence
    flow_rates = load_flow_rates()  # This loads the flow rates as intended
    
    if not flow_rates:
        print("Error: Flow rates not loaded.")
        return {}
    
    start_time = time.time()  # Record the start time
    time_limit = 60  # Set the time limit to 60 seconds

    while True:  # Use a loop to retry instead of `goto`
        # Check if the time limit has been exceeded
        if time.time() - start_time > time_limit:
            print("Time limit exceeded. Assuming humidity value is 0.")
            system_state["sensor_chamber"]["value"] = 0
            system_state["sensor_chamber"]["timestamp"] = int(time.time())
            print("Updated the Sensor chambers humidity data to 0.")
            return 0  # Exit the function with a humidity value of 0

        num_readings = 3
        ph_values = []

        print("Collecting Humidity Readings from Sensor Chambers...")
        for _ in range(num_readings):
            time.sleep(1)
            raw_ph_value = send_command_and_get_response(ser, b'Q')
            print(f"Retrieved Humidity value: '{raw_ph_value}'")

            if raw_ph_value is None:
                print("Error: Invalid Humidity value read from the sensor.")
                continue

            try:
                raw_ph_value = float(raw_ph_value)
            except ValueError:
                print(f"Error: Invalid Humidity value '{raw_ph_value}' received, cannot convert to float.")
                continue

            if 0 <= raw_ph_value <= 100:
                ph_values.append(raw_ph_value)

        if len(ph_values) == 0:
            print("Error: No valid Humidity readings collected.")
            continue  # Retry the loop if no valid readings

        estimated_ph_value = statistics.median(ph_values)
        print(f"Estimated Humidity value (median of valid readings): {estimated_ph_value}")
        response = estimated_ph_value

        # Update system state with the sensor data
        system_state["sensor_chamber"]["value"] = response
        system_state["sensor_chamber"]["timestamp"] = int(time.time())
        print("Updated the Sensor chambers humidity data.")

        if response > 0:
            print("Humidity is high, turning on the device.")
            safe_serial_write("m", "o")  # Turn on the device
            safe_serial_write("l", "o")  # Turn on the device
            # Continuously monitor humidity until it drops below 57
            while True:
                # Check if the time limit has been exceeded
                if time.time() - start_time > time_limit:
                    print("Time limit exceeded. Assuming humidity value is 0.")
                    safe_serial_write("m", "f")  # Turn off the device
                    safe_serial_write("l", "f")  # Turn off the device
                    system_state["sensor_chamber"]["value"] = 0
                    system_state["sensor_chamber"]["timestamp"] = int(time.time())
                    print("Updated the Sensor chambers humidity data to 0.")
                    return 0  # Exit the function with a humidity value of 0

                time.sleep(5)  # Wait for 5 seconds before taking the next reading
                raw_ph_value = send_command_and_get_response(ser, b'Q')
                if raw_ph_value is None:
                    print("Error: Invalid Humidity value read from the sensor.")
                    continue

                try:
                    raw_ph_value = float(raw_ph_value)
                except ValueError:
                    print(f"Error: Invalid Humidity value '{raw_ph_value}' received, cannot convert to float.")
                    continue

                if raw_ph_value < 57:
                    print("Humidity is now below threshold, turning off the device.")
                    safe_serial_write("m", "f")  # Turn off the device
                    safe_serial_write("l", "f")  # Turn off the device
                    break  # Exit the inner loop
                else:
                    safe_serial_write("m", "o")  # Turn on the device
                    safe_serial_write("l", "o")  # Turn on the device
            break  # Exit the outer loop after the device is turned off
        else:
            print("Chambers are dry, proceeding with the test.")
            break  # Exit the loop if humidity is <= 0


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
    # Validate inputs
    for var_name, var in zip(
        ["target_NPK", "NPK", "target_pH", "pH", "target_temp", "temp", "target_solution", "solution", "current_volume", "tank_capacity"],
        [target_NPK, NPK, target_pH, pH, target_temp, temp, target_solution, solution, current_volume, tank_capacity]
    ):
        if var is None:
            raise TypeError(f"Expected numeric value for {var_name}, got None")
        if not isinstance(var, (int, float)):
            raise TypeError(f"Expected numeric value for {var_name}, got {type(var)}: {var}")
    
    multiplyers = load_config()
    base_ec = float(multiplyers["EC_baseline"])
    cur_ppm = get_ppm(base_ec, NPK)
    target_ppm = base_ec + target_NPK
    
    print(f"base_ec = {base_ec}  cur_ppm = {cur_ppm} cur_ec = {NPK} target_ppm = {target_NPK} target_ec = {target_ppm}")

    # Calculate adjustments
    NPK_adj = target_NPK - cur_ppm
    pH_adj = target_pH - pH
    temp_adj = target_temp - temp
    solution_adj = target_solution - solution
    NPK_margin = 20
    pH_margin = 1
    solution_margin = 5
    ##########################
    if NPK >= 1000:
        NPK_adj = 0
        print(f"!!!!!!!!!!TDS Sensor reached its maximum measurment value, NO FURTHER FERTILIZER WILL BE ADDED TO THE SYSTEM!!!!!!!!")



    ##########################
    if NPK_adj <= NPK_margin:
        NPK_adj = 0
    if pH_adj <= pH_margin:
        pH_adj = 0
    if abs(solution_adj) <= solution_margin:
        solution_adj = 0


    # Initialize single and multi commands
    single_commands = {}
    multi_commands = {}

    

    NPK_mult = float(multiplyers["NPK_mult"])
    pH_plus_mult = float(multiplyers["pH_plus_mult"])
    pH_minus_mult = float(multiplyers["pH_minus_mult"])
    drop_mult = float(multiplyers["drop_mult"])
    
    print(f"********Loaded multiplyers {NPK_mult} --  {pH_minus_mult}  --  {pH_plus_mult} drop mult - {drop_mult}")

    history_log("solution_adj", solution_adj)
    history_log("NPK_adj", NPK_adj)
    history_log("pH_adj", pH_adj)
    


    # Handle solution level adjustment
    if solution_adj > 0:
        # Add fresh water first
        sol_adj = solution_adj * 30
        print(f"Solution adjustment weight - {sol_adj}")
        single_commands["fresh_solution"] = sol_adj
        # Update the current volume after adding fresh water
        final_volume = current_volume + solution_adj
    else:
        # Add fresh water first
        sol_adj = solution_adj * 30
        print(f"Solution adjustment weight - {sol_adj}")
        single_commands["solution_waste"] = abs(sol_adj)
        # Update the current volume after adding fresh water
        final_volume = current_volume + solution_adj

    # Debugging: Print values and types
    print(f"target_NPK: {target_NPK}, type: {type(target_NPK)}")
    print(f"final_volume: {final_volume}, type: {type(final_volume)}")
    print(f"NPK: {NPK}, type: {type(NPK)}")
    print(f"current_volume: {current_volume}, type: {type(current_volume)}")

    print(f"NPK_mult: {NPK_mult}, type: {type(NPK_mult)}")
    print(f"drop_mult: {drop_mult}, type: {type(drop_mult)}")
    print(f"ph_min_mult: {pH_minus_mult}, type: {type(pH_minus_mult)}")
    print(f"ph_mlus_mult: {pH_plus_mult}, type: {type(pH_plus_mult)}")



    # Handle NPK adjustment (compensate for dilution)
    if NPK_adj != 0:
        # Calculate the required NPK weight to achieve the target concentration in the final volume
        #required_NPK = ((target_NPK * final_volume) - (NPK * current_volume)) / 100
        required_NPK = NPK_adj#target_NPK - NPK 
        
        print(f"required_NPK: {required_NPK}, type: {type(required_NPK)}")
        if required_NPK > 0:
            z = required_NPK * NPK_mult
            print(f"NPK adjustment weight - {z}")
            single_commands["NPK"] = z
        elif required_NPK < 0:
            print(f"drop_mult = {drop_mult}     required_NPK = {required_NPK}")
            # If NPK is too high, use solution_waste to remove excess and fresh_solution to dilute
            single_commands["solution_waste"] = abs(float(required_NPK)) * drop_mult
            #
            single_commands["fresh_solution"] = abs(float(required_NPK)) * drop_mult
            #W = 0.2
            #Z = 100
            #single_commands["solution_waste"] = re * Z
            #single_commands["fresh_solution"] = W * Z


    # Handle pH adjustment (compensate for dilution)
    if pH_adj != 0:
        # Calculate the required pH chemical weight to achieve the target pH in the final volume
        #required_pH = ((target_pH * final_volume) - (pH * current_volume)) / 100
        required_pH = target_pH - pH
        print(f"Required adjustment pH - {required_pH}")
        if pH_adj < 0:
            x = abs(required_pH) * pH_minus_mult
            print(f"administring pH down - {x}")
            single_commands["pH_minus"] = x
        elif pH_adj > 0:
            y = required_pH * pH_plus_mult
            print(f"administring pH up - {y}")
            single_commands["pH_plus"] = y

    # Always mix the solution at the end
    single_commands["mixer_1"] = 2

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

    #system_state = load_system_state()
    

    target_NPK = system_state["target_NPK"]["value"]
    #system_state["target_NPK"]["timestamp"] = int(time.time())
        
    target_temp = system_state["target_temp"]["value"]
    #system_state["target_temp"]["timestamp"] = int(time.time())
        
    target_pH = system_state["target_pH"]["value"] 
    #system_state["target_pH"]["timestamp"] = int(time.time())
        
    target_solution = system_state["target_solution"]["value"]
    #system_state["target_solution"]["timestamp"] = int(time.time())

    print(f"################target_NPK = {target_NPK}")
    NPK = system_state["ec_solution"]["value"]
    print(f"################ec_solution from system state = {NPK}")
    print(f"################system state dump = {system_state}")

    NPK = system_state["ec_solution"]["value"]
    NPK_time = system_state["ec_solution"]["timestamp"]
        
    temp = system_state["temperature"]["value"]
    temp_time = system_state["temperature"]["timestamp"] 
        
    pH = system_state["ph_solution"]["value"] 
    pH_time = system_state["ph_solution"]["timestamp"]
        
    solution = system_state["solution_tank"]["value"]
    solution_time = system_state["solution_tank"]["timestamp"] 

    #NPK_adj = target_NPK - NPK
    #pH_adj = target_pH - pH
    #temp_adj = target_temp - temp
    #solution_adj = target_solution - solution
    
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
    global system_state  # Declare system_state as global
    SYSTEM_STATE_FILE = "data/desired_parameters.json"
    """Loads the system_state dictionary from a JSON file. If the file does not exist, returns an empty default structure."""
    print(f"Loading sys_state from file name:{SYSTEM_STATE_FILE}")
    if not os.path.exists(SYSTEM_STATE_FILE):
        print(f"Path does not exist")
        return None  # Indicate that no previous state exists
    with open(SYSTEM_STATE_FILE, "r") as f:
        x = json.load(f)
        print(f"Loaded data:{x}")

        target_NPK = x.get('EC')  # Extract the 'value' field
        target_temp = x.get('temperature')  # Extract the 'value' field
        target_pH = x.get('pH')  # Extract the 'value' field
        target_solution = x.get('solution')  # Extract the 'value' field
        target_air_humidity = x.get('air_humidity')  # Extract the 'value' field
        target_air_temperature = x.get('air_temperature')  # Extract the 'value' field
        # Update system_state
        system_state["target_NPK"]["value"] = target_NPK
        system_state["target_NPK"]["timestamp"] = int(time.time())
        
        system_state["target_temp"]["value"] = target_temp
        system_state["target_temp"]["timestamp"] = int(time.time())
        
        system_state["target_pH"]["value"] = target_pH
        system_state["target_pH"]["timestamp"] = int(time.time())
        
        system_state["target_solution"]["value"] = target_solution
        system_state["target_solution"]["timestamp"] = int(time.time())

        #system_state["target_"]["value"] = target_solution
        #system_state["target_solution"]["timestamp"] = int(time.time())

        system_state["plant_chamber_target_humidity"]["value"] = target_air_humidity
        system_state["plant_chamber_target_humidity"]["timestamp"] = int(time.time())
        
        system_state["plant_chamber_target_temperature"]["value"] = target_air_temperature
        system_state["plant_chamber_target_temperature"]["timestamp"] = int(time.time())
        


        print("Updated Target Values.")
    return None