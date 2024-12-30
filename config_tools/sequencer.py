import json
import time
from flow_tune import send_command_with_heartbeat, load_flow_rates




import serial

# Serial configuration
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
HEARTBEAT_TIMEOUT = 2  # Maximum time (seconds) to wait for a heartbeat
PUMP_COMMANDS = {
    "NPK": 'g',
    "pH_plus": 'h',
    "pH_minus": 'e',
    "pH_cal_high": 'c',
    "pH_cal_low": 'd',
    "EC_cal": 'f',
    "fresh": 'a',
    "drain": 'b'
}

# File paths
#FLOW_RATES_FILE = '../data/flow_rates.json'

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print('starting test fresh pump')
ser.write(b'ao')  # Turn on "fresh" pump
print('waiting 5')
time.sleep(5)
ser.write(b'af')  # Turn off "fresh" pump
print('test ended ')





# File paths
SEQUENCE_FILE = '../sequences/pH_calibration.json'

def execute_command(command, weight, flow_rates):
    """
    Execute the given command for a specific weight using flow rates.
    """
    print(f"Executing command: {command} for {weight}g")
    
    if command not in flow_rates:
        print(f"Error: Flow rate for '{command}' not found in flow rates file.")
        return False

    # Calculate duration based on flow rate
    flow_rate = flow_rates[command]
    duration = weight / flow_rate
    print(f"Debug: Command '{command}', Weight {weight}g, Flow rate {flow_rate} g/s, Duration {duration:.2f}s")
    
    # Send the command to Arduino
    return send_command_with_heartbeat(command, duration)

def execute_sequence(sequence_file, flow_rates):
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
        if not execute_command(command, weight, flow_rates):
            print(f"Error: Failed to execute command {command}.")
            break

        time.sleep(1)  # Small delay to prevent overwhelming the system

    print("Sequence complete.")

if __name__ == "__main__":
    # Load flow rates from the JSON file
    flow_rates = load_flow_rates()
    print(f"Debug: Loaded flow rates: {flow_rates}")
    
    if flow_rates:
        execute_sequence(SEQUENCE_FILE, flow_rates)
    else:
        print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
