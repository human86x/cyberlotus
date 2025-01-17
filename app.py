from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from config_tools.tank_manager import load_tanks, add_tank, test_tanks
from config_tools.flow_tune import calibrate_pump, test_pump, load_pump_commands

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

###################################

import threading
import time
import os
import sys
from control_libs.arduino import connect_to_arduino, send_command_and_get_response
from control_libs.electric_conductivity import get_ec
from control_libs.temperature import read_solution_temperature

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, "config_tools"))
from config_tools.sequencer import execute_sequence
from config_tools.calibrator import get_correct_EC
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands

# Store progress globally
pump_progress = {}

ser = connect_to_arduino()
time.sleep(2)  # Allow Arduino to initialize
global PUMP_COMMANDS

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
        return jsonify({'status': 'error', 'message': 'Emergency Stop failed.'}), 500

def safe_serial_write_emergency():
    """Safely send the emergency stop command to Arduino."""
    try:
        if ser and ser.is_open:
            ser.write(b'X')
            ser.flush()
            print("[ALERT] 🚨 Emergency Stop command 'X' sent to Arduino.")
        else:
            print("[ERROR] Serial port is not open. Cannot send Emergency Stop.")
    except serial.SerialException as e:
        print(f"[ERROR] Serial write failed during Emergency Stop: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error during Emergency Stop: {e}")

def safe_serial_write(pump_name, state):
    """
    Safely write a pump control command to the serial port.

    Args:
        pump_name (str): Name of the pump (must be in PUMP_COMMANDS).
        state (str): 'o' to turn ON, 'f' to turn OFF.
    """
    try:
        if pump_name not in PUMP_COMMANDS:
            print(f"[ERROR] Invalid pump name: {pump_name}")
            return

        if state not in ['o', 'f']:
            print(f"[ERROR] Invalid pump state: {state}")
            return

        command = f"{PUMP_COMMANDS[pump_name]}{state}"
        
        if ser and ser.is_open:
            ser.write(command.encode())
            ser.flush()
            print(f"[INFO] Sent command: {command}")
        else:
            print("[ERROR] Serial port is not open. Cannot send command.")

    except serial.SerialException as e:
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

@app.route('/fill_tank', methods=['POST'])
def fill_tank():
    tank_name = request.form['tank_name']
    pump_name = request.form['pump_name']

    if not tank_name or not pump_name:
        flash("Tank name or Pump name not provided.", "error")
        return redirect(url_for('dashboard'))

    # Start filling the tank
    safe_serial_write(pump_name, 'o')  # Turn ON pump
    flash(f"Filling {tank_name} with pump {pump_name} started.", "success")

    # Run a function to monitor fill progress and stop when the tank is full
    def monitor_fill():
        # Simulate monitoring the tank fill progress
        time.sleep(10)  # Simulate fill time
        safe_serial_write(pump_name, 'f')  # Turn OFF pump
        flash(f"Filling of {tank_name} completed.", "success")

    threading.Thread(target=monitor_fill).start()

    return redirect(url_for('dashboard'))

@app.route('/drain_tank', methods=['POST'])
def drain_tank():
    tank_name = request.form['tank_name']
    pump_name = request.form['pump_name']

    if not tank_name or not pump_name:
        flash("Tank name or Pump name not provided.", "error")
        return redirect(url_for('dashboard'))

    # Start draining the tank
    safe_serial_write(pump_name, 'o')  # Turn ON pump
    flash(f"Draining {tank_name} with pump {pump_name} started.", "success")

    # Run a function to monitor drain progress and stop when the tank is empty
    def monitor_drain():
        # Simulate monitoring the tank drain progress
        time.sleep(10)  # Simulate drain time
        safe_serial_write(pump_name, 'f')  # Turn OFF pump
        flash(f"Draining of {tank_name} completed.", "success")

    threading.Thread(target=monitor_drain).start()

    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.jinja_env.cache = {}
    app.run(host='0.0.0.0', port=5000, debug=True)
