import json
import time
import serial
import os

# File paths
PUMP_COMMANDS_FILE = '../data/relay_names.json'  # Path to the JSON file
SEQUENCE_FILE = '../sequences/EC_calibration.json'

# Serial configuration
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600

def load_pump_commands():
    """Load pump commands from the JSON file."""
    if not os.path.exists(PUMP_COMMANDS_FILE):
        print(f"Error: {PUMP_COMMANDS_FILE} not found.")
        return {}
    with open(PUMP_COMMANDS_FILE, 'r') as file:
        return json.load(file)

def load_flow_rates():
    """Load flow rates from the JSON file."""
    FLOW_RATES_FILE = '../data/flow_rates.json'
    if not os.path.exists(FLOW_RATES_FILE):
        print(f"Error: {FLOW_RATES_FILE} not found.")
        return {}
    with open(FLOW_RATES_FILE, 'r') as file:
        return json.load(file)

def send_command_with_heartbeat(command, duration):
    # Example implementation
    print(f"Sending command {command} for {duration} seconds to Arduino.")
    # Simulate the command sending here
    time.sleep(duration)
    return True

def execute_command(command, weight, flow_rates, PUMP_COMMANDS):
    """
    Execute the given command for a specific weight using flow rates.
    """
    print(f"Executing command: {command} for {weight}g")
    
    if command not in flow_rates:
        print(f"Error: Flow rate for '{command}' not found in flow rates file.")
        return False

    if command not in PUMP_COMMANDS:
        print(f"Error: Command '{command}' not recognized in PUMP_COMMANDS.")
        return False

    # Translate the logical command to the Arduino command
    arduino_command = PUMP_COMMANDS[command]

    # Calculate duration based on flow rate
    flow_rate = flow_rates[command]
    duration = weight / flow_rate
    
    print(f"Debug: Command '{command}' translated to '{arduino_command}', Weight {weight}g, Flow rate {flow_rate} g/s, Duration {duration:.2f}s")
    
    print(f"Debug: Sending command '{arduino_command}' to Arduino with duration {duration:.2f}s.")

    # Send the translated command to Arduino
    return send_command_with_heartbeat(arduino_command, duration)

def execute_sequence(sequence_file, flow_rates, PUMP_COMMANDS):
    """
    Read the sequence from a JSON file and execute the actions.
    """
    try:
        with open(sequence_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: {sequence_file} not found.")
        return

    for action in data["sequence"]:
        command = action["command"]
        weight = action["weight"]

        # Check for calibration actions
        if "calibration" in action and action["calibration"]:
            print(f"Calibration step detected. Waiting for calibration...")
            input(f"Calibration needed for {command}. Press Enter when calibration is complete.")
        
        # Execute the command after calibration (if applicable)
        if not execute_command(command, weight, flow_rates, PUMP_COMMANDS):
            print(f"Error: Failed to execute command {command}.")
            break

        time.sleep(1)  # Small delay to prevent overwhelming the system

    print("Sequence complete.")

if __name__ == "__main__":
    # Load flow rates from the JSON file
    flow_rates = load_flow_rates()
    print(f"Debug: Loaded flow rates: {flow_rates}")
    
    if flow_rates:
        # Load pump commands directly from the JSON file
        PUMP_COMMANDS = load_pump_commands()
        print(f"Debug: Loaded PUMP_COMMANDS: {PUMP_COMMANDS}")
        
        # Proceed to execute the sequence
        execute_sequence(SEQUENCE_FILE, flow_rates, PUMP_COMMANDS)
    else:
        print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
