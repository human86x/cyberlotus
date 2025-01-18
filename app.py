from flask import Flask, render_template, request, redirect, url_for, jsonify
from config_tools.tank_manager import load_tanks, add_tank, test_tanks

from flask import flash
from config_tools.flow_tune import calibrate_pump, test_pump, load_pump_commands

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

###################################

from flask import jsonify
import threading
import time
import os
import sys
import json
from control_libs.arduino import get_serial_connection, close_serial_connection ,connect_to_arduino, send_command_and_get_response
from control_libs.electric_conductivity import get_ec
from control_libs.temperature import read_solution_temperature

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "config_tools"))
from config_tools.sequencer import execute_sequence
from config_tools.calibrator import get_correct_EC
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands

# Store progress globally
pump_progress = {}

#ser = connect_to_arduino()

time.sleep(2)  # Allow Arduino to initialize
global PUMP_COMMANDS



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
        drain_volume_liters = 3.5  # Drain 1 liter
        weight_to_drain = drain_volume_liters * 100  # Convert liters to pump units

        # Activate the pump
        test_pump_with_progress(waste_pump, weight_to_drain)

        return jsonify({"status": "success", "pump_used": waste_pump})

    except Exception as e:
        print(f"Error during waste drain: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500





@app.route('/adjust_solution_tank', methods=['POST'])
def adjust_solution_tank():
    return adjust_tank_level('solution')

def adjust_tank_level(tank_name):
    global PUMP_COMMANDS
    print(f"Adjusting tank level for {tank_name}...")

    try:
        # Load configuration from app_config.json
        with open('data/app_config.json', 'r') as file:
            app_config = json.load(file)
        
        # Retrieve the pumps to be used for fill or drain actions
        fill_pump = app_config.get('fill_pump', 'fresh_solution')
        drain_pump = app_config.get('drain_pump', 'solution_waste')
        solution_level = float(app_config.get('solution_level', 50))  # Default 50 if not found
        
        # Fetch the tank levels from `tank_manager.py`
        tank_results = test_tanks()  # This function will give you the current levels
        print(f"Tank data fetched****{tank_results}")
        
        # Get the data for the specific tank
        tank_data = tank_results.get(tank_name)
        
        if not tank_data:
            print(f"Tank {tank_name} not found in the results.")
            return jsonify({"status": "error", "message": f"Tank {tank_name} not found"}), 400

        current_volume = tank_data['current_volume']
        total_volume = tank_data['total_volume']

        # Calculate the volume to add or drain
        stored_volume = (solution_level / 100) * total_volume
        volume_difference = current_volume - stored_volume
        print(f"Volume Difference {volume_difference}...")
        if volume_difference > 0:
            # Need to drain liquid
            print(f"Draining {volume_difference:.2f} L of solution from {tank_name}.")
            weight_to_drain = volume_difference * 1000  # Convert to weight (multiply by 100)
            print(f"Weight to drain {weight_to_drain}...")
            test_pump_with_progress(drain_pump, weight_to_drain)
        elif volume_difference < 0:
            # Need to add liquid
            print(f"Adding {-volume_difference:.2f} L of solution to {tank_name}.")
            weight_to_add = -volume_difference * 1000  # Convert to weight (multiply by 100)
            print(f"Weight_to_add {weight_to_add}...")
            test_pump_with_progress(fill_pump, weight_to_add)
        else:
            print(f"Tank {tank_name} is already at the correct level.")

        return jsonify({"status": "success", "message": f"Tank {tank_name} adjusted successfully"})

    except Exception as e:
        print(f"Error adjusting tank level: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500




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
        attempt += 1
        print(f"Reconnection attemp N: {attemp}")

        return jsonify({'status': 'error', 'message': 'Emergency Stop failed.'}), 500




def safe_serial_write_emergency():
    global ser
    ser = get_serial_connection()
    """Safely send the emergency stop command to Arduino with verification."""
    max_retries = 3  # Number of retry attempts
    attempt = 0

    while attempt < max_retries:
        try:
            if ser and ser.is_open:
                ser.write(b'X')
                ser.flush()
                print(f"[ALERT] 🚨 Emergency Stop command 'X' sent to Arduino. Attempt {attempt + 1}")

                # Wait for Arduino response
                response = ser.readline().decode().strip()
                print(f"[INFO] Arduino response: {response}")

                if response == "All pumps turned OFF":
                    print("[SUCCESS] ✅ Arduino confirmed: All pumps are OFF.")
                    return  # Exit function if successful
                else:
                    print("[WARNING] ⚠️ Unexpected response. Reconnecting and retrying...")

            else:
                print("[ERROR] Serial port is not open. Attempting to reconnect...")

            # Reconnect and retry
            connect_to_arduino()
            attempt += 1

        except ser.SerialException as e:
            print(f"[ERROR] Serial write failed during Emergency Stop: {e}. Reconnecting and retrying...")
            connect_to_arduino()
            attempt += 1

        except Exception as e:
            print(f"[ERROR] Unexpected error during Emergency Stop: {e}. Reconnecting and retrying...")
            connect_to_arduino()
            attempt += 1

    print("[FAILURE] ❌ Emergency Stop failed after multiple attempts. Manual intervention may be required.")


import time

def safe_serial_write(pump_name, state, retries=1, timeout=2):
    global ser
    ser = get_serial_connection()
    """
    Safely write a pump control command to the serial port and verify Arduino response.

    Args:
        pump_name (str): Name of the pump (must be in PUMP_COMMANDS).
        state (str): 'o' to turn ON, 'f' to turn OFF.
        retries (int): Number of retries if no valid response is received.
        timeout (int): Time in seconds to wait for Arduino response.
    """
    try:
        if pump_name not in PUMP_COMMANDS:
            print(f"[ERROR] Invalid pump name: {pump_name}")
            return

        if state not in ['o', 'f']:
            print(f"[ERROR] Invalid pump state: {state}")
            return

        command = f"{PUMP_COMMANDS[pump_name]}{state}"
        expected_response = f"{'ON' if state == 'o' else 'OFF'}_{PUMP_COMMANDS[pump_name]}"
        
        attempt = 0

        while attempt <= retries:
            if ser and ser.is_open:
                ser.reset_input_buffer()  # Clear any previous data
                ser.write(command.encode())
                ser.flush()
                print(f"[INFO] Sent command: {command}, waiting for response...")

                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        print(f"[INFO] Received response: {response}")

                        if response == expected_response:
                            print(f"[SUCCESS] Arduino confirmed action: {response}")
                            return  # Exit after successful confirmation
                        else:
                            print(f"[WARNING] Unexpected response: {response}")
                    
                    time.sleep(0.1)  # Small delay to avoid CPU overuse

                # If no valid response, retry
                print(f"[ERROR] No valid response. Retrying... (Attempt {attempt + 1}/{retries})")
                attempt += 1

            else:
                print("[ERROR] Serial port is not open. Cannot send command.")
                return

        # After retries fail
        print("[ERROR] Failed to confirm command after retries. Attempting emergency stop.")
        emergency_stop(pump_name)

    except ser.SerialException as e:
        print(f"[ERROR] Serial write failed for {pump_name}: {e}")
        emergency_stop(pump_name)
    except Exception as e:
        print(f"[ERROR] Unexpected error while writing to serial: {e}")
        emergency_stop(pump_name)



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




def emergency_stop(pump_name):
    global ser
    ser = get_serial_connection()
    """Immediately stop the specified pump in case of error."""
    try:
        print(f"[EMERGENCY] Stopping {pump_name} immediately!")
        if ser and ser.is_open:
            ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())
            ser.flush()
        else:
            print("[ERROR] Serial port is not open. Attempting reconnection...")
            reconnect_arduino()
            ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())
    except Exception as e:
        print(f"[CRITICAL] Failed to stop {pump_name}: {e}")


def test_pump_with_progress(pump_name, weight):
    #global PUMP_COMMANDS  # Ensure global access
    global PUMP_COMMANDS  # Ensure global access
    PUMP_COMMANDS = load_pump_commands()
    #pump_names = list(PUMP_COMMANDS.keys())
    global ser
    ser = get_serial_connection()
    """Test the pump with progress updates."""
    
    flow_rates = load_flow_rates()
    print(f"******pump_name======={pump_name}")
    if pump_name not in flow_rates or pump_name not in PUMP_COMMANDS:
        pump_progress[pump_name] = -1  # Error state
        return

    flow_rate = flow_rates[pump_name]
    duration = weight / flow_rate

    #ser.write(f"{PUMP_COMMANDS[pump_name]}o".encode())
    safe_serial_write(pump_name, 'o')  # Turn ON
    for i in range(int(duration * 10)):
        pump_progress[pump_name] = int((i / (duration * 10)) * 100)
        time.sleep(0.1)

    #ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())
    safe_serial_write(pump_name, 'f')  # Turn ON
    pump_progress[pump_name] = 100  # Complete





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
    return render_template('ph.html')
@app.route('/ecosystem')
def ecosystem():
    return render_template('ecsystem.html')






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

@app.route('/tanks/test', methods=['GET'])
def test_tanks_route():
    results = test_tanks()
    return jsonify(results)

if __name__ == '__main__':
    app.jinja_env.cache = {}
    app.run(host='0.0.0.0', port=5000, debug=True)
