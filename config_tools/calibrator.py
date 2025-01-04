import json
import time
import os

# File paths
FLOW_RATES_FILE = '../data/flow_rates.json'
PUMP_COMMANDS_FILE = '../data/relay_names.json'
EC_SEQUENCE_FILE = '../sequences/pH_calibration.json'

def load_flow_rates():
    """
    Load flow rates from the flow_rates.json file.
    """
    if not os.path.exists(FLOW_RATES_FILE):
        print(f"Error: {FLOW_RATES_FILE} not found.")
        return {}
    with open(FLOW_RATES_FILE, 'r') as file:
        return json.load(file)

def load_pump_commands():
    """
    Load pump commands from the relay_names.json file.
    """
    if not os.path.exists(PUMP_COMMANDS_FILE):
        print(f"Error: {PUMP_COMMANDS_FILE} not found.")
        return {}
    with open(PUMP_COMMANDS_FILE, 'r') as file:
        return json.load(file)

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
    
    # Simulate sending the command (Replace with actual serial communication)
    time.sleep(duration)  # Simulating the command execution
    print(f"Command '{arduino_command}' executed successfully.")
    return True

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

def calibrate_ec_sensor():
    """
    Calibrate the EC sensor by executing the calibration sequence.
    """
    print("Starting EC sensor calibration...")

    # Load flow rates
    flow_rates = load_flow_rates()
    if not flow_rates:
        print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
        return

    # Load pump commands
    PUMP_COMMANDS = load_pump_commands()
    if not PUMP_COMMANDS:
        print("Error: Pump commands not loaded. Ensure the relay_names.json file exists and is valid.")
        return

    # Execute the calibration sequence with both flow_rates and PUMP_COMMANDS
    execute_sequence(EC_SEQUENCE_FILE, flow_rates, PUMP_COMMANDS)
    print("EC sensor calibration complete.")

def main():
    """
    Main function to handle the calibration menu.
    """
    while True:
        print("\n--- Calibration Menu ---")
        print("1. Calibrate EC Sensor")
        print("2. Exit")
        choice = input("Select an option: ")

        if choice == "1":
            calibrate_ec_sensor()
        elif choice == "2":
            print("Exiting calibration tool. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
