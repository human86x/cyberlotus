from flask import Flask, render_template, request, redirect, url_for, jsonify
from config_tools.tank_manager import load_tanks, add_tank, test_tanks, adjust_tank_level

from flask import flash
from config_tools.flow_tune import calibrate_pump, test_pump_with_progress, test_pump, load_pump_commands

from flask import Response
from queue import Queue

###################################

from flask import jsonify
import threading
import time
import os
import sys
import json
from control_libs.arduino import get_serial_connection, close_serial_connection ,connect_to_arduino, send_command_and_get_response
from control_libs.electric_conductivity import get_ec, get_complex_ec_reading,  get_correct_EC
from control_libs.temperature import read_solution_temperature
from control_libs.arduino import safe_serial_write, emergency_stop, safe_serial_write_emergency
from control_libs.app_core import load_config
from control_libs.chamber import chamber_ambiance, light_control
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "config_tools"))


from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands


from flask import Flask, request, send_from_directory
from config_tools.sequencer import execute_sequence, list_sequence_files

from control_libs.electric_conductivity import get_correct_EC,load_calibration_data, calibrate_ec_sensor, set_baseline_ec, get_fast_ec
from flask_socketio import SocketIO, emit
from control_libs.app_core import CONFIG_FILE_PATH
from control_libs.electric_conductivity import get_complex_ec_calibration, get_ec_baseline

from control_libs.system_stats import load_system_state
from control_libs.ph import get_correct_ph
from control_libs.adjuster import check_chamber_humidity, temperature_control, condition_monitor, load_target_values,ph_down, temperature_up, ph_up, nutrients_up, nutrients_down
APP_CONFIG_FILE = "data/app_config.json"
# Store progress globally
pump_progress = {}

app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Needed for flash messages
socketio = SocketIO(app)  # This is where you initialize socketio
#ser = connect_to_arduino()

#time.sleep(2)  # Allow Arduino to initialize
global PUMP_COMMANDS

#execute_sequence(EC_BASELINE_FILE, load_flow_rates(), set_baseline_ec)



DATA_DIRECTORY = "data"








@app.route('/light_switch', methods=['POST'])
def handle_light_switch():
    data = request.get_json()
    light = data.get('light')
    state = data.get('state')
    
    if not light or not state:
        return jsonify({'error': 'Missing light or state parameter'}), 400
    
    try:
        light_control(light, state)
        return jsonify({'status': 'success'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400











#check_chamber_humidity

@app.route('/check_chamber_humidity', methods=['POST'])
def check_chamber_humidity_route():
    data = request.json
    data = data.get('value')  # Extract the 'value' field

    check_chamber_humidity()
    return "Done"
 

@app.route('/ph_up', methods=['POST'])
def ph_up_route():
    data = request.json
    data = data.get('value')  # Extract the 'value' field

    ph_up(data)
    return None
 
@app.route('/ph_down', methods=['POST'])
def ph_down_route():
    data = request.json
    data = data.get('value')  # Extract the 'value' field
    ph_down(data)
    return None

@app.route('/npk_up', methods=['POST'])
def npk_up_route():
    data = request.json
    data = data.get('value')  # Extract the 'value' field
    nutrients_up(data)
    return None

@app.route('/npk_down', methods=['POST'])
def npk_down_route():
    data = request.json
    data = data.get('value')  # Extract the 'value' field
    nutrients_down(data)
    return None

@app.route('/temperature_up', methods=['POST'])
def temp_up_route():
    data = request.json
    data = data.get('value')  # Extract the 'value' field
    temperature_up(data)
    return None


@app.route('/load_target', methods=['POST'])
def load_target_route():
    #data = request.json
    #data = data.get('value')  # Extract the 'value' field
    load_target_values()
    return "Done"

@app.route('/chamber_autopilot', methods=['POST'])
def chamber_autopilot_route():
    #data = request.json
    #data = data.get('value')  # Extract the 'value' field
    chamber_ambiance()
    return "Done"


@app.route('/condition_monitor', methods=['POST'])
def condition_monitor_route():
    #data = request.json
    #data = data.get('value')  # Extract the 'value' field
    condition_monitor()
    return "Done"

@app.route('/temperature_control', methods=['POST'])
def temperature_control_route():
    #data = request.json
    #data = data.get('value')  # Extract the 'value' field
    temperature_control()
    return "Done"



################################RUNNING CHART###################


@app.route('/get_fast_ec')
def get_fast_ec_route():
    #global ser
    a = get_fast_ec()
    return str(a)  # Convert float to string
    

#####################EC#####################









def load_data():
    try:
        with open(f"{DATA_DIRECTORY}/readings_log.json", "r") as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

#@app.route('/')
#def index():
#    return render_template("chart.html")

@app.route('/data')
def get_data():
    print(f"#########trying to get data.....")
    data = load_data()  # Load your data from file or database
    filtered_data = {
        "timestamps": [],
        "temperature": [],
        "ec": [],
        "ph": [],
        "ppm": [],  # Add ppm data to the response
        "solution_adj": [],
        "NPK_adj": [],
        "pH_adj": []
    }
    
    for entry in data:
        timestamp = entry.get("timestamp")
        if timestamp:
            filtered_data["timestamps"].append(timestamp)
            
            # Append values if they exist
            filtered_data["temperature"].append(entry.get("Temperature", None))
            filtered_data["ec"].append(entry.get("EC", None))
            filtered_data["ph"].append(entry.get("pH", None))
            filtered_data["ppm"].append(entry.get("ppm", None))  # Add PPM value
            filtered_data["solution_adj"].append(entry.get("solution_adj", None))
            filtered_data["NPK_adj"].append(entry.get("NPK_adj", None))
            filtered_data["pH_adj"].append(entry.get("pH_adj", None))  # Add pH adjustment value
            
    return jsonify(filtered_data)





##################SYSTEM CURRENT READINGS AND PUMP STATES###############

from control_libs.system_stats import system_state



@app.route("/get_history")
def get_history():
    """ Serve the historical data from readings_log.json """
    file_path = "data/readings_log.json"
    if not os.path.exists(file_path):
        return jsonify([])
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    #print(f"History data: {data}")        
    return jsonify(data)




# Define a route that returns the readings dictionary as a JSON response
@app.route("/sys_state", methods=["GET"])
def get_system_state():

    #print(f"***********System state {system_state}")
    return jsonify(system_state)


@app.route("/load_sys_state", methods=["GET"])
def load_system_state_route():
    global system_state
    print("trying to load system state file......")
    loaded_state = load_system_state()
    #system_state = loaded_state
    return loaded_state


from control_libs.electric_conductivity import load_ec_baseline, get_ppm

@app.route("/ppm", methods=["GET"])
def load_ec_baseline_route():
    global system_state
    print("trying to load system state file......")
    load_ec_baseline
    ppm = get_ppm()
    return ppm

####################END OF SYSTEM READINGS AND PUMP STATES###############



circulation_status = "Off"

################################


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/sequences')
def sequences():
    return render_template('sequences.html')
@app.route('/ec')
def ec():
    return render_template('EC.html')
@app.route('/ph')
def ph():
    return render_template('pH.html')

@app.route('/ecosystem')
def ecosystem():
    return render_template('ecosystem.html')

@app.route('/relays')
def relays():
    return render_template('relays.html')

@app.route('/automatisation')
def automatisation():
    return render_template('automatisation.html')

@app.route('/plant_chamber')
def plant_chamber():
    sensor_data = {
        'air_humidity': 45.6,
        'air_temperature': 22.3,
        'light_intensity': 1200,
        'pot_water_temperature': 18.7,
        'water_level_current': 5.2,
        'water_level_target': 6.0,
    }

    # Example light control states (you would replace this with actual states)
    light_states = {
        'white_light': False,
        'yellow_light': True,
        'growing_light': False,
    }

    global circulation_status
    return render_template('plant_chamber.html', sensor_data=sensor_data, light_states=light_states, circulation_status=circulation_status)

@app.route('/set_water_level', methods=['GET'])
def set_water_level():
    new_target = float(request.form['water_level_target'])
    # Update the target water level (you would replace this with actual logic)
    print(f"New target water level set to: {new_target} L")
    return "True"#redirect(url_for('control_panel'))

@app.route('/start_circulation', methods=['GET'])
def start_circulation():
    global circulation_status
    circulation_status = not circulation_status  # Toggle circulation status
    print(f"Solution circulation is now {'on' if circulation_status else 'off'}")
    
    circulate_solution()

    return "True"#redirect(url_for('control_panel'))

from control_libs.chamber import get_chamber_humidity, get_chamber_temp, get_plant_temp

@app.route('/chamber_data_update', methods=['GET'])
def chamber_data_route():
    global circulation_status
    

    #circulation_status = not circulation_status  # Toggle circulation status
    print(f"Retriving data from the chamber...")
    
    get_chamber_humidity()
    get_chamber_temp()
    get_plant_temp()

    return "True"#redirect(url_for('control_panel'))
  
  

from control_libs.adjuster import circulate_solution

@app.route('/circulate', methods=['POST'])
def circulate_solution_route():
    circulate_solution()





# Function to load app configuration from the JSON file
def load_app_config():
    print("Loading app config to EC page")
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}  # Return empty dict if the file does not exist
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}

# Route to get the stored configuration
@app.route('/get_app_config', methods=['GET'])
def get_app_config():
    config = load_app_config()
    return jsonify(config)

# Function to save app configuration to the JSON file
def save_app_config(config):
    try:
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving config file: {e}")

# Route to save the configuration
@app.route('/save_app_config', methods=['POST'])
def save_configuration():
    data = request.json
    config = load_config()  # Load existing configuration
    config.update(data)  # Update the configuration with new data
    save_app_config(config)  # Save the updated configuration
    return jsonify({"status": "success", "message": "Configuration saved successfully"})

# Global variable to control the auto-pilot loop
auto_pilot_running = False


import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Global variables
auto_pilot_running = False
last_successful_task = None  # Track the last successful task

def auto_pilot_loop(pause_minutes):
    global auto_pilot_running, last_successful_task
    auto_pilot_running = True

    # Define the sequence of tasks
    tasks = [
        load_target_values,
        temperature_control,
        lambda: perform_ph_test("solution"),
        temperature_control,
        condition_monitor,
        temperature_control,
        lambda: perform_ph_test("solution")
    ]

    while auto_pilot_running:
        try:
            # Determine where to resume
            start_index = 0 if last_successful_task is None else tasks.index(last_successful_task) + 1
            if start_index == 7:
                start_index = 0
                last_successful_task = None
            print(f"start_index = {start_index}")
            print(f"tasks[start_index:] = {tasks[start_index:]}")
            if tasks[start_index:] == "":
                start_index = 0 
                last_successful_task = None
            print(f"auto_pilot_running = {auto_pilot_running}")
            




            # Execute tasks starting from the last successful one
            for task in tasks[start_index:]:
                if not auto_pilot_running:
                    break  # Exit if stop command is received
                print(f"task = {task}")
                logging.info(f"Executing task: {task.__name__}")
                task()  # Execute the task
                last_successful_task = task  # Update the last successful task

            # Calculate the countdown time
            pause_seconds = pause_minutes * 60
            logging.info(f"Waiting for {pause_minutes} minutes before the next iteration...")

            # Countdown loop
            for remaining in range(pause_seconds, 0, -1):
                if not auto_pilot_running:
                    break  # Exit if stop command is received
                logging.info(f"Time remaining until next iteration: {remaining} seconds")
                time.sleep(1)

            if not auto_pilot_running:
                break  # Exit the main loop if stop command is received

        except Exception as e:
            logging.error(f"Error occurred during task execution: {e}")
            logging.info("Attempting to resume after error...")
            time.sleep(5)  # Wait before retrying

    logging.info("Auto-pilot loop stopped.")

@app.route('/auto_pilot', methods=['POST'])
def auto_pilot_route():
    global auto_pilot_running

    data = request.json

    # Check if the request is to stop the auto-pilot
    if data.get("command") == "stop":
        auto_pilot_running = False
        return jsonify({"status": "success", "message": "Auto-pilot stopping..."})

    # Get the pause time in minutes from the request
    pause_minutes = data.get("pause_minutes")
    if not pause_minutes or pause_minutes <= 0:
        return jsonify({"status": "error", "message": "Invalid pause time provided."}), 400

    # Start the auto-pilot loop in a separate thread
    if not auto_pilot_running:
        threading.Thread(target=auto_pilot_loop, args=(pause_minutes,)).start()
        return jsonify({"status": "success", "message": "Auto-pilot started."})
    else:
        return jsonify({"status": "error", "message": "Auto-pilot is already running."}), 400





@app.route('/get_calibration_data', methods=['GET'])
def get_calibration_data():
    data = load_calibration_data()
    return jsonify({"status": "success", "data": data})




######################TEMPERATURE##############
@app.route('/get_temperature')
def get_temperature():
    try:
        # Initialize the serial connection here
        ser = connect_to_arduino()  # Adjust this based on your actual connection method
        
        # Read temperature using the function from temperature.py
        temperature = read_solution_temperature(ser)
        print(f"Flash temperature update****{temperature}")
        # Close the serial connection after reading
        ser.close()
        
        if temperature is not None:
            return jsonify({"status": "success", "temperature": temperature})
        else:
            return jsonify({"status": "error", "message": "Failed to read temperature"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
#####################EC#####################

# Get the corrected EC value
@app.route('/get_ec', methods=['GET'])
def get_ec_value():
    ec_value = get_correct_EC()
    if ec_value is not None:
        return jsonify({'status': 'success', 'ec_value': ec_value})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get EC value'})


  

@app.route('/get_complex_ec', methods=['GET'])
def get_complex_ec():
    """
    Flask route to retrieve complex EC readings.
    """
    try:
        # Get the readings from the helper function
        readings = get_complex_ec_reading()
        return jsonify({'readings': readings})
    except KeyError as e:
        return jsonify({'error': f"Configuration key missing: {str(e)}"}), 404
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500




@app.route('/get_ec_baseline', methods=['GET'])
def get_ec_baseline_route():
    """
    Flask route to retrieve complex EC readings.
    """
    try:
        # Get the readings from the helper function
        readings = get_ec_baseline()
        return jsonify({'readings': readings})
    except KeyError as e:
        return jsonify({'error': f"Configurations key missing: {str(e)}"}), 404
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500





@app.route('/calibrate_ec_sensor', methods=['POST'])
def calibrate_ec_sensor_route():
    """
    Flask route to calibrate the EC sensor.
    """
    try:
        # Call the calibration function
        get_complex_ec_calibration()
        return jsonify({'status': 'success', 'message': 'EC sensor calibration complete.'})
    except KeyError as e:
        return jsonify({'error': f"Configuration key missing: {str(e)}"}), 404
    except ValueError as e:
        return jsonify({'error': f"Value error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

########################pH################################


# Get the corrected EC value
@app.route('/get_ph', methods=['GET'])
def get_ph_value():
    ph_value = get_correct_ph()
    if ph_value is not None:
        return jsonify({'status': 'success', 'ph_value': ph_value})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get EC value'})


from control_libs.ph import perform_ph_calibration, get_ph,calibrate_ph, perform_ph_test
from control_libs.arduino import get_serial_connection

# Get the corrected EC value
@app.route('/get_raw_ph', methods=['GET'])
def get_raw_ph_value():
    ser = get_serial_connection()
    raw_ph_value = get_ph(ser)
    if raw_ph_value is not None:
        return jsonify({'status': 'success', 'raw_ph_value': raw_ph_value})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get EC value'})






# Get the corrected EC value
@app.route('/calibrate_ph_low', methods=['GET'])
def calibrate_ph_low_route():
    ph_factor = perform_ph_calibration("LOW")
    if ph_factor is not None:
        return jsonify({'status': 'success', 'ph_value': ph_factor})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get ph_factor'})

# Get the corrected EC value
@app.route('/simple_calibrate_ph_low', methods=['GET'])
def simple_calibrate_ph_low_route():
    ph_factor = calibrate_ph("LOW")
    if ph_factor is not None:
        return jsonify({'status': 'success', 'ph_value': ph_factor})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get ph_factor'})

# Get the corrected EC value
@app.route('/simple_calibrate_ph_high', methods=['GET'])
def simple_calibrate_ph_high_route():
    ph_factor = calibrate_ph("HIGH")
    if ph_factor is not None:
        return jsonify({'status': 'success', 'ph_value': ph_factor})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get ph_factor'})

@app.route('/ph_solution_test', methods=['GET'])
def ph_solution_test_route():
    ph_factor = perform_ph_test("solution")
    if ph_factor is not None:
        return jsonify({'status': 'success', 'ph_value': ph_factor})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get ph_factor'})

@app.route('/ph_baseline_test', methods=['GET'])
def ph_baseline_test_route():
    ph_factor = perform_ph_test("baseline")
    if ph_factor is not None:
        return jsonify({'status': 'success', 'ph_value': ph_factor})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get ph_factor'})






# Get the corrected EC value
@app.route('/calibrate_ph_high', methods=['GET'])
def calibrate_ph_high_route():
    ph_factor = perform_ph_calibration("HIGH")
    if ph_factor is not None:
        return jsonify({'status': 'success', 'ph_value': ph_factor})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to get ph_factor'})




















@app.route('/get_app_setting', methods=['GET'])
def get_app_setting():
    """
    Flask route to retrieve app configuration.
    """
    print("Reading the configuration file...")
    try:
        key = request.args.get('key')
        if key:
            return jsonify({key: load_config(key)})
        return jsonify(load_config())
    except KeyError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

















##################not using############
# Set EC baseline
@app.route('/set_baseline', methods=['POST'])
def set_baseline():
    try:
        set_baseline_ec()
        return jsonify({'status': 'success', 'message': 'EC baseline set successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@socketio.on('start_calibration')
def handle_start_calibration():
    calibrate_ec_sensor()

# Test sequence trigger (this is where you'd need to implement your test logic)
@app.route('/start_callback_sequence/<sequence>', methods=['GET'])
def start_callback_sequence(sequence):
    sequence = SEQUENCE_DIRECTORY + '/' + sequence

    try:
        # Here you can handle different test sequences
        print(f"Starting test sequence: {sequence}")
        execute_sequence(sequence, load_flow_rates(), trigger)
        return jsonify({'status': 'success', 'message': f'Started {sequence} test sequence'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})








############################################################










###################SEQUENCER########################

#app = Flask(__name__)




@app.route('/refresh_ec', methods=['GET'])
def refresh_EC():

    ec = get_correct_EC()
    #temperature = get_temperature()

    return ec



    data = request.json
    config = load_app_config()  # Load existing configuration
    config.update(data)  # Update the configuration with new data
    #save_app_config(config)  # Save the updated configuration
    return jsonify({"status": "success", "message": "Configuration saved successfully"})





SEQUENCE_DIRECTORY = 'sequences/'

@app.route('/list_sequences', methods=['GET'])
def list_sequences():
    """
    API to list all available sequence files.
    """
    sequence_files = list_sequence_files()
    if sequence_files:
        return jsonify({"status": "success", "files": sequence_files})
    return jsonify({"status": "error", "message": "No sequence files found."})

@app.route('/load_sequence', methods=['GET'])
def load_sequence():
    """
    API to load and return the content of a sequence file.
    """
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"status": "error", "message": "No filename provided."})
    filepath = SEQUENCE_DIRECTORY + '/' + filename
    print(f"Sequence dir is - {SEQUENCE_DIRECTORY}")
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        return jsonify({"status": "success", "content": content, "filename": filename})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found."})

@app.route('/save_sequence', methods=['POST'])
def save_sequence():
    """
    API to save or create a new sequence file.
    """
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    if not filename or not content:
        return jsonify({"status": "error", "message": "Filename or content not provided."})

    filepath = SEQUENCE_DIRECTORY + '/' + filename
    try:
        with open(filepath, 'w') as file:
            file.write(content)
        return jsonify({"status": "success", "message": f"Sequence saved to {filename}."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to save sequence: {str(e)}"})









@app.route('/create_sequence', methods=['POST'])
def create_sequence():
    """
    API to create a new sequence file.
    """
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    if not filename or not content:
        return jsonify({"status": "error", "message": "Filename or content not provided."})

    filepath = SEQUENCE_DIRECTORY + '/' + filename
    try:
        if os.path.exists(filepath):
            return jsonify({"status": "error", "message": f"File {filename} already exists."})
        with open(filepath, 'w') as file:
            file.write(content)
        return jsonify({"status": "success", "message": f"New sequence {filename} created."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to create sequence: {str(e)}"})

@app.route('/execute_sequence', methods=['POST'])
def execute_sequence_route():
    """
    API to execute a sequence file.
    """
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({"status": "error", "message": "No filename provided."})

    flow_rates = load_flow_rates()
    filepath = SEQUENCE_DIRECTORY + '/' + filename

    def run_sequence():
        execute_sequence(filepath, flow_rates)

    threading.Thread(target=run_sequence).start()
    return jsonify({"status": "success", "message": f"Sequence {filename} started."})






###########sequencer ends#################





@app.route('/load_relay_names', methods=['GET'])
def load_relay_names():
    """
    API to load and return the content of a sequence file.
    """
    filename = "relay_names.json"

    if not filename:
        return jsonify({"status": "error", "message": "No filename provided."})
    filepath = DATA_DIRECTORY + '/' + filename
    print(f"Data dir is - {DATA_DIRECTORY}")
    try:
        with open(filepath, 'r') as file:
            content = file.read()
        return jsonify({"status": "success", "content": content, "filename": filename})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found."})

@app.route('/save_relay_names', methods=['POST'])
def save_relay_names():
    """
    API to save or create a new sequence file.
    """
    data = request.json
    filename = "relay_names.json"
    content = data.get('content')
    if not filename or not content:
        return jsonify({"status": "error", "message": "Filename or content not provided."})

    filepath = DATA_DIRECTORY + '/' + filename
    try:
        # Convert the dictionary to a JSON string before writing
        with open(filepath, 'w') as file:
            json.dump(content, file, indent=4)  # Use json.dump for proper formatting
        return jsonify({"status": "success", "message": f"Sequence saved to {filename}."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to save sequence: {str(e)}"})


@app.route('/relay_direct', methods=['POST'])
def control_relay_directly():
    data = request.json
    letter = data.get('letter')  # The letter (e.g., 'a', 'b', 'g')
    state = data.get('state')    # The state ("on" or "off")
    
    if letter and state:
        # Send the letter and state separately to the serial write function
        safe_serial_write(letter, state)
        return jsonify({"status": "success", "message": f"Relay {letter} turned {'ON' if state == 'o' else 'OFF'}"})
    else:
        return jsonify({"status": "error", "message": "Invalid data. Both 'letter' and 'state' are required."})


@app.route('/drain_waste', methods=['POST'])
def drain_waste():
    try:
        # Load the pump configuration from app_config.json
        with open('data/app_config.json', 'r') as file:
            app_config = json.load(file)
            waste_pump = app_config.get('waste_pump')

        if not waste_pump:
            return jsonify({"status": "error", "message": "No waste pump configured."}), 400

        # Example drain volume, adjust as needed
        x = test_tanks()
        to_drain = x["waste"]["current_volume"]
        drain_volume_liters = to_drain  # Drain 1 liter
        print("to_drain and weight_to_drain:")
        print(to_drain)
        
        weight_to_drain = drain_volume_liters * 1000  # Convert liters to pump units
        print(weight_to_drain)
        # Activate the pump
        test_pump_with_progress(waste_pump, weight_to_drain)

        return jsonify({"status": "success", "pump_used": waste_pump})

    except Exception as e:
        print(f"Error during waste drain: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500





@app.route('/adjust_solution_tank', methods=['POST'])
def adjust_solution_tank():
    return adjust_tank_level('solution')



@app.route('/compare_solution_level', methods=['GET'])
def compare_solution_level():
    print("Compare solution level function started*************")
    try:
        # Load the current solution level
        with open('data/app_config.json', 'r') as file:
            app_config = json.load(file)
            # Ensure stored_level is a float
            stored_level = float(app_config.get('solution_level', 50))  # Default to 50 if not found

        # Fetch the tank levels from `tank_manager.py`
        tank_results = test_tanks()  # This function will give you the current levels
        print(f"Tank data fetched****{tank_results}")
        changes_needed = {}

        for tank, data in tank_results.items():
            current_volume = data['current_volume']
            total_volume = data['total_volume']
            print(f"Current volume - {current_volume}")
            print(f"Total volume - {total_volume}")
            
            # Calculate the difference between current volume and stored solution level
            stored_volume = (stored_level / 100) * total_volume
            print(f"Target volume - {stored_volume}")
            if current_volume > stored_volume:
                # Need to drain liquid
                volume_to_drain = current_volume - stored_volume
                changes_needed[tank] = {'action': 'drain', 'volume_liters': volume_to_drain}
            elif current_volume < stored_volume:
                # Need to add liquid
                volume_to_add = stored_volume - current_volume
                changes_needed[tank] = {'action': 'add', 'volume_liters': volume_to_add}
        
        return jsonify(changes_needed)

    except Exception as e:
        print(f"Error comparing solution levels: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def compare_and_calculate_difference(current_level, tank_name):
    # Load stored tanks data
    tanks = load_tanks()
    if tank_name not in tanks:
        return {"error": f"Tank '{tank_name}' not found."}

    tank_info = tanks[tank_name]
    total_volume = tank_info['total_volume']
    
    # Get the stored solution level (default to 50 if not found in config file)
    try:
        with open('data/app_config.json', 'r') as file:
            app_config = json.load(file)
            stored_solution_level = app_config.get('solution_level', 50)
    except Exception as e:
        return {"error": f"Error reading config file: {e}"}
    
    # Calculate the difference between current level and stored level
    if current_level > stored_solution_level:
        # Drain the solution
        difference = current_level - stored_solution_level
        volume_to_drain = (difference / 100) * total_volume
        action = "drain"
    else:
        # Add the solution
        difference = stored_solution_level - current_level
        volume_to_add = (difference / 100) * total_volume
        action = "add"
    
    return {
        "tank_name": tank_name,
        "current_level": current_level,
        "stored_solution_level": stored_solution_level,
        "difference": round(difference, 2),
        "action": action,
        "volume_to_adjust": round(volume_to_drain if action == "drain" else volume_to_add, 2)
    }









@app.route('/get_solution_level', methods=['GET'])
def get_solution_level():
    try:
        with open('data/app_config.json', 'r') as file:
            app_config = json.load(file)
            solution_level = app_config.get('solution_level', 50)  # Default to 50 if not found
        return jsonify({"solution_level": solution_level})
    except Exception as e:
        print(f"Error reading config file: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/save_solution_level', methods=['POST'])
def save_solution_level():
    data = request.get_json()
    solution_level = data.get('solution_level')
    print("***********************save_solution_level....")

    # Update the app_config.json file with the new solution level
    try:
        # Check if the file exists; if not, create it with a default structure
        try:
            with open('data/app_config.json', 'r+') as file:
                app_config = json.load(file)
        except FileNotFoundError:
            # If the file doesn't exist, create it with a default structure
            app_config = {"solution_level": 50}

        app_config['solution_level'] = solution_level
        print("***********************Writing to a config file....")
        with open('data/app_config.json', 'w') as file:
            json.dump(app_config, file, indent=4)

        return jsonify({"status": "success", "message": "Solution level saved successfully."})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/save_pump_assignment', methods=['POST'])
def save_pump_assignment():
    data = request.get_json()
    fill_pump = data.get('fill_pump')
    drain_pump = data.get('drain_pump')
    print("saving function***********")
    try:
        with open('data/app_config.json', 'r+') as file:
            app_config = json.load(file)

        # Update pump assignments in the config
        app_config['fill_pump'] = fill_pump
        app_config['drain_pump'] = drain_pump

        with open('data/app_config.json', 'w') as file:
            json.dump(app_config, file, indent=4)
            print("writing to a file***********")
        return jsonify({"status": "success", "message": "Pump assignments saved successfully."})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_saved_pumps', methods=['GET'])
def get_saved_pumps():
    print("Reading the assignment fle...")
    try:
        # Load the app configuration from your config file
        with open('data/app_config.json', 'r') as config_file:
            config = json.load(config_file)
        print("OK...")
    
        # Assuming 'fill_pump' and 'drain_pump' are stored in your config
        return jsonify({
            'fill_pump': config.get('fill_pump'),
            'drain_pump': config.get('drain_pump')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
  


@app.route('/tanks/delete/<tank_name>', methods=['DELETE'])
def delete_tank_route(tank_name):
    tanks = load_tanks()
    if tank_name in tanks:
        del tanks[tank_name]
        save_tanks(tanks)
        return jsonify({'status': 'success', 'message': f'Tank "{tank_name}" deleted successfully.'})
    else:
        return jsonify({'status': 'error', 'message': f'Tank "{tank_name}" not found.'}), 404




@app.route('/emergency_stop', methods=['POST'])
def emergency_stop_route():
    """Emergency stop for all pumps."""
    try:
        safe_serial_write_emergency()
        flash("🚨 Emergency Stop activated! All pumps stopped.", "error")
        return jsonify({'status': 'success', 'message': 'Emergency Stop activated!'})
    except Exception as e:
        print(f"[ERROR] Emergency Stop failed: {e}")
        connect_to_arduino()
        #attempt += 1
        #print(f"Reconnection attemp N: {attemp}")

        return jsonify({'status': 'error', 'message': 'Emergency Stop failed.'}), 500



@app.route('/pumps', methods=['GET', 'POST'])
def pumps():
    global PUMP_COMMANDS  # Ensure global access
    PUMP_COMMANDS = load_pump_commands()
    pump_names = list(PUMP_COMMANDS.keys())

    if request.method == 'POST':
        action = request.form.get('action')
        pump_name = request.form.get('pump_name')

        if action == 'calibrate':
            calibrate_pump(pump_name)
            flash(f"Calibration started for {pump_name}.", "success")

        elif action == 'test':
            weight = request.form.get('weight')
            if weight:
                try:
                    weight = float(weight)
                    test_pump(pump_name, weight)
                    flash(f"Test started for {pump_name} with {weight}g.", "success")
                except ValueError:
                    flash("Invalid weight input. Please enter a number.", "error")
            else:
                flash("Please enter a weight to test.", "error")

        return redirect(url_for('pumps'))

    return render_template('pumps.html', pump_names=pump_names)








@app.route('/start_pump_action', methods=['POST'])
def start_pump_action():
    global PUMP_COMMANDS  # Ensure global access
    data = request.get_json()
    pump_name = data.get('pump_name')
    action = data.get('action')
    weight = data.get('weight')

    if not pump_name:
        return jsonify({'status': 'error', 'message': 'Pump name not provided'})

    # Initialize progress
    pump_progress[pump_name] = 0

    # Run pump action in a separate thread to avoid blocking
    def run_pump():
        if action == 'calibrate':
            calibrate_pump_with_progress(pump_name)
        elif action == 'test' and weight:
            try:
                weight_value = float(weight)
                test_pump_with_progress(pump_name, weight_value)
            except ValueError:
                pump_progress[pump_name] = -1  # Error state

    threading.Thread(target=run_pump).start()

    return jsonify({'status': 'success'})

@app.route('/get_progress/<pump_name>')
def get_progress(pump_name):
    progress = pump_progress.get(pump_name, 0)
    return jsonify({'progress': progress})

def calibrate_pump_with_progress(pump_name):
    duration = 10  # Duration in seconds

    try:
        safe_serial_write(pump_name, 'o')  # Turn ON
        for i in range(duration * 10):
            pump_progress[pump_name] = int((i / (duration * 10)) * 100)
            time.sleep(0.1)
        safe_serial_write(pump_name, 'f')  # Turn OFF
        pump_progress[pump_name] = 100

    except Exception as e:
        print(f"[ERROR] Calibration failed for {pump_name}: {e}")
        emergency_stop(pump_name)
        pump_progress[pump_name] = -1








###################



@app.route('/tanks', methods=['GET', 'POST'])
def tanks():
    tanks_data = load_tanks()
    global PUMP_COMMANDS  # Ensure global access
    PUMP_COMMANDS = load_pump_commands()
    pump_names = list(PUMP_COMMANDS.keys())

    if request.method == 'POST':
        action = request.form.get('action')
        pump_name = request.form.get('pump_name')

        if action == 'calibrate':
            calibrate_pump(pump_name)
            flash(f"Calibration started for {pump_name}.", "success")

        elif action == 'test':
            weight = request.form.get('weight')
            if weight:
                try:
                    weight = float(weight)
                    test_pump(pump_name, weight)
                    flash(f"Test started for {pump_name} with {weight}g.", "success")
                except ValueError:
                    flash("Invalid weight input. Please enter a number.", "error")
            else:
                flash("Please enter a weight to test.", "error")

        return redirect(url_for('tanks'))

    #return render_template('pumps.html', pump_names=pump_names)

    return render_template('tanks.html', tanks=test_tanks(), pump_names=pump_names)
    #return render_template('tanks.html', tanks=tanks_data)

@app.route('/tanks/create', methods=['POST'])
def create_tank_route():
    name = request.form['name']
    code = request.form['code']
    total_volume = float(request.form['total_volume'])
    full_cm = float(request.form['full_cm'])
    empty_cm = float(request.form['empty_cm'])

    add_tank(name, code, total_volume, full_cm, empty_cm)
    return redirect(url_for('tanks'))

@app.route('/test_tanks_route', methods=['GET'])
def test_tanks_route():
    results = test_tanks()
    print(f"****************test_tanks_route - {results}")
    return jsonify(results)

if __name__ == '__main__':
    app.jinja_env.cache = {}
    app.run(host='0.0.0.0', port=5000, debug=True)
