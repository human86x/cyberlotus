import json
import time
import serial
import os
from config_tools.flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from config_tools.flow_tune import PUMP_COMMANDS
from control_libs.arduino import safe_serial_write_precise
# Serial configuration (commented out for now)
#SERIAL_PORT = '/dev/ttyACM0'
#BAUD_RATE = 9600
FLOW_RATES = load_flow_rates()
# Load pump commands
PUMP_COMMANDS = load_pump_commands()

# File paths (updated to load from the chosen sequence file)
SEQUENCE_DIRECTORY = 'sequences/'

def execute_commands(commands, weights, flow_rates):
    """
    Execute multiple commands for specific weights using flow rates.
    Turn ON all pumps sequentially, wait for the duration, then turn OFF all pumps sequentially.

    Parameters:
        commands (list or str): Command(s) to execute. Can be a single string or a list of strings.
        weights (float, int, or list): Weight(s) corresponding to each command. Can be a single value or a list.
        flow_rates (dict): Dictionary containing the flow rates for each pump command.

    Returns:
        bool: True if all commands were executed successfully, False otherwise.
    """
    print(f"Executing commands: {commands} for weights {weights}")

    arduino_commands = []
    durations = []

    # Convert single command or weight to list for consistent processing
    if isinstance(commands, str):
        commands = [commands]
    if isinstance(weights, (int, float)):
        weights = [weights] * len(commands)

    # Validate commands and weights alignment
    if len(commands) != len(weights):
        print("Error: Number of commands and weights do not match.")
        return False

    # Debugging outputs
    print(f"Final Commands: {commands}")
    print(f"Final Weights: {weights}")

    for command, weight in zip(commands, weights):
        # Check for missing flow rates
        if command not in flow_rates:
            print(f"Error: Flow rate for '{command}' not found in flow rates file.")
            return False

        # Check for invalid pump commands
        if command not in PUMP_COMMANDS:
            print(f"Error: Command '{command}' not recognized in PUMP_COMMANDS.")
            return False

        # Translate logical command to Arduino command
        arduino_command = PUMP_COMMANDS[command]

        # Calculate duration based on flow rate
        flow_rate = flow_rates[command]
        if flow_rate == 0:
            print(f"Error: Flow rate for '{command}' is zero, cannot calculate duration.")
            return False

        duration = weight / flow_rate
        arduino_commands.append(arduino_command)
        durations.append(duration)

        # Debugging: Show command translation and execution details
        print(f"Debug: Command '{command}' translated to '{arduino_command}', "
              f"Weight {weight}g, Flow rate {flow_rate} g/s, Duration {duration:.2f}s")

    # Ensure all durations are the same (required for simultaneous operation)
    if len(set(durations)) != 1:
        print("Error: Durations must be the same for simultaneous pump operation.")
        return False

    duration = durations[0]  # All durations are the same
    duration_ms = int(round(duration * 1000))

    if duration_ms <= 0:
        print(f"Error: Invalid duration value {duration:.2f}s. Duration must be positive.")
        return False

    # Turn ON all pumps sequentially
    for arduino_command in arduino_commands:
        print(f"Debug: Turning ON '{arduino_command}'.")
        if not send_command_with_heartbeat(arduino_command, duration=0):  # Turn ON without waiting
            print(f"Error: Failed to turn ON '{arduino_command}'.")
            return False

    # Wait for the required duration
    print(f"Debug: Waiting for {duration:.2f}s.")
    #print(f"Pump '{command}' turned ON. Waiting for {duration:.2f}s...")

    start_time = time.time()
    while time.time() - start_time < duration:
        time_elapsed = time.time() - start_time
        progress = min(int((time_elapsed / duration) * 100), 100)  # Ensure max progress is 100%
        print(f"Operation in progress... {progress}% complete.", end="\r")
        time.sleep(0.1)  # Small delay to avoid excessive CPU usage

    #time.sleep(duration)

    # Turn OFF all pumps sequentially
    for arduino_command in arduino_commands:
        print(f"Debug: Turning OFF '{arduino_command}'.")
        if not send_command_with_heartbeat(arduino_command, duration=-1):  # Turn OFF
            print(f"Error: Failed to turn OFF '{arduino_command}'.")
            return False

    return True

def execute_sequence(sequence_file, flow_rates=None, calibration_callback=None):
    """
    Read the sequence from a JSON file and execute the actions.

    Parameters:
        sequence_file (str): Path to the JSON file containing the sequence.
        flow_rates (dict): Dictionary containing flow rates for each pump.
        calibration_callback (function): Optional callback for calibration steps.
    """
    print("SEQUENCE FUNCTION    ENTRY POINT")
    #sequence_file = "sequences/" + sequence_file 
    readings = None
    if flow_rates is None:
        flow_rates = FLOW_RATES

    try:
        with open(sequence_file, 'r') as file:
            data = json.load(file)
            print(f"SEQUENCE FUNCTION {sequence_file} file LOADED data={data}")
    except FileNotFoundError:
        print(f"Error: {sequence_file} not found.")
        return
    print("SEQUENCE FUNCTION IS ACTIVATED AND SEQUENCE FILE FOUND")
    for action in data["sequence"]:
        # Handle the case where multiple commands (pumps) are given
        if "commands" in action and "weights" in action:
            commands = action["commands"]
            weights = action["weights"]

            # Execute the commands simultaneously
            print(f"Executing {commands} simultaneously.")
            if not execute_commands(commands, weights, flow_rates):
                print(f"Error: Failed to execute commands {commands}.")
                break

            # Check for calibration actions after execution
            if "calibration" in action and action["calibration"]:
                print(f"Calibration step detected for {commands}.")
                if calibration_callback:
                    readings = calibration_callback()  # Call the calibration function
                else:
                    print("Debug: Calibration callback executed.")

        else:
            # Handle the case of a single command
            command = action["command"]
            weight = action["weight"]

            # Execute the command
            print(f"Executing {command}.")
            if not execute_commands(command, weight, flow_rates):
                print(f"Error: Failed to execute command {command}.")
                break

            # Check for calibration actions after execution
            if "calibration" in action and action["calibration"]:
                print(f"Calibration step detected for {command}.")
                if calibration_callback:
                    calibration_callback()  # Call the calibration function
                else:
                    print("Debug: Calibration callback executed.")

        time.sleep(1)  # Small delay to prevent overwhelming the system

    print("Sequence complete.")
    return readings

def list_sequence_files():
    """
    List all sequence files available in the SEQUENCE_DIRECTORY.
    """
    try:
        files = os.listdir(SEQUENCE_DIRECTORY)
        sequence_files = [f for f in files if f.endswith('.json')]
        if not sequence_files:
            print("No sequence files found.")
            return None
        print("Available sequence files:")
        for idx, filename in enumerate(sequence_files, start=1):
            print(f"{idx}. {filename}")
        return sequence_files
    except FileNotFoundError:
        print(f"Error: {SEQUENCE_DIRECTORY} not found.")
        return None

def choose_sequence_file():
    """
    Allow the user to choose a sequence file from the available ones.
    """
    sequence_files = list_sequence_files()
    if not sequence_files:
        return None
    try:
        choice = int(input("Enter the number of the sequence file you want to run: "))
        if 1 <= choice <= len(sequence_files):
            return os.path.join(SEQUENCE_DIRECTORY, sequence_files[choice - 1])
        else:
            print("Invalid choice.")
            return None
    except ValueError:
        print("Invalid input.")
        return None

if __name__ == "__main__":
    # Load flow rates from the JSON file
    flow_rates = load_flow_rates()
    print(f"Debug: Loaded flow rates: {flow_rates}")
    
    if flow_rates:
        # Ask user to choose a sequence file
        sequence_file = choose_sequence_file()
        if sequence_file:
            print(f"Running sequence from file: {sequence_file}")
            execute_sequence(sequence_file, flow_rates)
        else:
            print("No valid sequence file chosen. Exiting.")
    else:
        print("Error: Flow rates not loaded. Ensure the flow_rates.json file exists and is valid.")
