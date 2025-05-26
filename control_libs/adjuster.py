from config_tools.flow_tune import load_flow_rates, send_command_with_heartbeat, load_pump_commands, PUMP_COMMANDS
from control_libs.app_core import load_config, CALIBRATION_FILE, SEQUENCE_DIR
from control_libs.system_stats import system_state, history_log ,save_system_state, load_system_state
from control_libs.arduino import send_command_and_get_response,safe_serial_write, get_serial_connection
from config_tools.sequencer import execute_sequence
from control_libs.system_stats import append_console_message
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
        flag = system_state["stop_all"]["state"]
        if flag == "STOP":
            print(f"EXETING THE FUNCTION flag = {flag}")
            return
        target_plant_pot_level = load_config("target_plant_pot_level")
        system_state["plant_pot_target_level"]["value"] = target_plant_pot_level
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
            if plant_level is None:
                print("⚠️ Failed to get plant level reading. Retrying...")
                append_console_message("⚠️ Failed to get plant level reading. Retrying...")
                continue  # Skip to next iteration to try again
            
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
        LEVEL_MARGIN = 1

        # Control logic based on the level with margin
        try:
            level_difference = plant_level - target_plant_pot_level
        
        except TypeError:
            print("⚠️ Invalid plant level reading (None). Attempting to get new readings...")
            append_console_message("⚠️ Invalid plant level reading (None). Attempting to get new readings...")
            
            continue  # This will make the loop try again

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
def get_water_level():
    print("Reading the water level")
    append_console_message("Reading the water level...")
    
    # Number of readings to take
    NUM_READINGS = 3
    readings = []
    
    for i in range(NUM_READINGS):
        try:
            level = send_command_and_get_response(ser, b'C')
            if level is not None:
                readings.append(float(level))
                print(f"Reading {i+1}/{NUM_READINGS}: {level}cm")
                append_console_message(f"Reading {i+1}/{NUM_READINGS}: {level}cm")
            else:
                print(f"⚠️ Empty reading {i+1}/{NUM_READINGS}")
                append_console_message(f"⚠️ Empty reading {i+1}/{NUM_READINGS}")
            
            # Small delay between readings if not the last one
            if i < NUM_READINGS - 1:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"⚠️ Error during reading {i+1}: {str(e)}")
            append_console_message(f"⚠️ Error during reading {i+1}: {str(e)}")
    
    # Calculate median if we got enough readings
    if len(readings) >= NUM_READINGS:
        readings_sorted = sorted(readings)
        median_index = NUM_READINGS // 2
        plant_level = readings_sorted[median_index]
        
        print(f"✅ Water level readings: {readings} | Median: {plant_level}cm")
        append_console_message(f"✅ Water level readings: {[f'{x}cm' for x in readings]} | Median: {plant_level}cm")
        
        system_state["plant_pot_level"]["value"] = plant_level
        system_state["plant_pot_level"]["timestamp"] = int(time.time())
        history_log("water_level", plant_level)
        
        return plant_level
    elif readings:  # If we got some readings but not enough
        average = sum(readings) / len(readings)
        print(f"⚠️ Only got {len(readings)} readings, using average: {average}cm")
        append_console_message(f"⚠️ Only got {len(readings)} readings, using average: {average}cm")
        
        system_state["plant_pot_level"]["value"] = average
        system_state["plant_pot_level"]["timestamp"] = int(time.time())
        history_log("water_level", average)
        
        return average
    else:
        print("❌ Failed to get any valid water level readings")
        append_console_message("❌ Failed to get any valid water level readings")
        return None

def set_water_level():
    target_plant_pot_level = load_config("target_plant_pot_level")
    system_state["plant_pot_target_level"]["value"] = target_plant_pot_level
    system_state["plant_pot_target_level"]["timestamp"] = int(time.time())
    pump_up = "plant_up"
    pump_down = "plant_down"
    
    print("Setting the water level")
    append_console_message("Adjusting water level..")
    
    # Constants
    LEVEL_MARGIN = 0.3  # cm acceptable margin
    MAX_ATTEMPTS = 200  # Maximum adjustment attempts before giving up
    READING_RETRIES = 3  # Number of reading attempts before considering it failed
    DELAY_BETWEEN_ACTIONS = 5  # seconds between adjustments
    NUM_READINGS = 3  # Number of readings to take for median calculation
    
    attempts = 0
    
    while attempts < MAX_ATTEMPTS:
        attempts += 1
        valid_readings = []
        
        # Take multiple readings to ensure accuracy
        for _ in range(READING_RETRIES):
            try:
                readings = []
                # Take NUM_READINGS measurements
                for _ in range(NUM_READINGS):
                    level = send_command_and_get_response(ser, b'C')
                    if level is not None:
                        readings.append(float(level))
                        time.sleep(0.5)  # Small delay between readings
                
                if len(readings) >= NUM_READINGS:
                    # Calculate median
                    readings_sorted = sorted(readings)
                    median_index = NUM_READINGS // 2
                    plant_level = readings_sorted[median_index]
                    valid_readings.append(plant_level)
                    break
                    
            except Exception as e:
                print(f"⚠️ Error reading water level: {str(e)}")
                append_console_message(f"⚠️ Error reading water level: {str(e)}")
                time.sleep(1)
        
        if not valid_readings:
            append_console_message("❌ Failed to get valid water level readings")
            return False
        
        # Use the median of the valid readings
        plant_level = valid_readings[len(valid_readings)//2]
        
        # Update system state with the reading
        system_state["plant_pot_level"]["value"] = plant_level
        system_state["plant_pot_level"]["timestamp"] = int(time.time())
        history_log("water_level", plant_level)
        
        append_console_message(f"✅ Current water distance: {plant_level}cm (median of {NUM_READINGS} readings) | Target: {target_plant_pot_level}cm")
        print(f"Current: {plant_level}cm | Target: {target_plant_pot_level}cm | Attempt {attempts}/{MAX_ATTEMPTS}")
        
        # Calculate difference
        level_difference = plant_level - target_plant_pot_level
        
        # Check if we're within acceptable range
        if abs(level_difference) <= LEVEL_MARGIN:
            print("✅ Water level within acceptable range")
            append_console_message("✅ Water level adjustment complete")
            
            # Turn off both pumps
            send_command_with_heartbeat(PUMP_COMMANDS[pump_up], -1)
            send_command_with_heartbeat(PUMP_COMMANDS[pump_down], -1)
            return True
        
        # Determine required action
        if level_difference < -LEVEL_MARGIN:  # Too low - need to add water
            print("Draining the plant pot...")
            append_console_message("🔽 Lowering water level...")
            
            # Turn on down pump (adding solution)
            send_command_with_heartbeat(PUMP_COMMANDS[pump_down], 0)
            # Turn off up pump
            send_command_with_heartbeat(PUMP_COMMANDS[pump_up], -1)
            
        else:  # Too high - need to drain
            print("Adding more solution to the pot...")
            append_console_message("🔼 Raising water level...")
            # Turn on up pump (draining)
            send_command_with_heartbeat(PUMP_COMMANDS[pump_up], 0)
            # Turn off down pump
            send_command_with_heartbeat(PUMP_COMMANDS[pump_down], -1)
        
        # Wait before checking again
        time.sleep(DELAY_BETWEEN_ACTIONS)
    
    # If we get here, we've exceeded max attempts
    print("❌ Failed to reach target water level after maximum attempts")
    append_console_message("❌ Water level adjustment failed after maximum attempts")
    
    # Turn off both pumps before exiting
    send_command_with_heartbeat(PUMP_COMMANDS[pump_up], -1)
    send_command_with_heartbeat(PUMP_COMMANDS[pump_down], -1)
    return False



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
    append_console_message("Initiating needed calculations to adjust the solution.")
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
    NPK_adj = (target_NPK - cur_ppm) * (solution / 1000)  # Adjusts based on liters (assuming solution is in ml)
    pH_adj = (target_pH - pH) * (solution / 5)  # More sensitive adjustment (halved base multiplier)
    temp_adj = target_temp - temp
    solution_adj = target_solution - solution
    NPK_margin = 0.5
    pH_margin = 0.02
    solution_margin = 5
    
    
    if solution_adj < 0: solution_adj=0

    ##########################
    if NPK >= 1000:
        NPK_adj = 0
        print(f"!!!!!!!!!!TDS Sensor reached its maximum measurment value, NO FURTHER FERTILIZER WILL BE ADDED TO THE SYSTEM!!!!!!!!")



    ##########################
    if abs(NPK_adj) <= NPK_margin:
        NPK_adj = 0
    if abs(pH_adj) <= pH_margin:
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
    
    
    


    # Handle solution level adjustment
    if solution_adj > 0:
        # Add fresh water first
        sol_adj = solution_adj * 30
        print(f"Solution adjustment weight - {sol_adj}")
        #single_commands["fresh_solution"] = sol_adj
        # Update the current volume after adding fresh water
        final_volume = current_volume + solution_adj
    else:
        # Add fresh water first
        sol_adj = solution_adj * 30
        print(f"Solution adjustment weight - {sol_adj}")
        #single_commands["solution_waste"] = abs(sol_adj)
        # Update the current volume after adding fresh water
        final_volume = current_volume + solution_adj

    # Debugging: print values and types
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
        append_console_message(f"✅ required_ph {required_pH} = target_ph {target_pH} - ph {pH}")

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
    ph_temp = (abs(required_pH) * pH_minus_mult ) + (required_pH * pH_plus_mult)
    z = required_NPK * NPK_mult
    append_console_message(f"NPK to add {z} (formula {target_NPK} - {cur_ppm} * {solution} / 1000)")
    append_console_message(f"pH+ to adjust {ph_temp} (formula {target_pH} - {pH} * {solution} / 500)")
    
    history_log("solution_adj", solution_adj)
    history_log("NPK_adj", z)
    history_log("pH_adj", ph_temp)




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