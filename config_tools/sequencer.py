import json
import time
import serial
import os
from flow_tune import send_command_with_heartbeat, load_flow_rates, load_pump_commands
from flow_tune import PUMP_COMMANDS

# Serial configuration (commented out for now)
#SERIAL_PORT = '/dev/ttyACM0'
#BAUD_RATE = 9600

# Load pump commands
PUMP_COMMANDS = load_pump_commands()

# File paths (updated to load from the chosen sequence file)
SEQUENCE_DIRECTORY = '../sequences/'

import threading

def execute_commands(commands, weights, flow_rates):
    """
    Execute multiple commands for specific weights using flow rates simultaneously.
    """
    print(f"Executing commands: {commands} for weights {weights}")
    
    arduino_commands = []
    durations = []

    print(f"Commands: {commands}")
    print(f"Weights: {weights}")

    
    for command, weight in zip(commands, weights):
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
        
        arduino_commands.append(arduino_command)
        durations.append(duration)
        
        print(f"Debug: Command '{command}' translated to '{arduino_command}', Weight {weight}g, Flow rate {flow_rate} g/s, Duration {duration:.2f}s")
    
    # Define a function to send commands to Arduino
    def send_to_arduino(command, duration):
        print(f"Debug: Sending command '{command}' to Arduino with duration {duration:.2f}s.")
        if not send_command_with_heartbeat(command, duration):
            print(f"Error: Failed to send command '{command}'.")
    
    # Start threads for simultaneous execution
    threads = []
    for arduino_command, duration in zip(arduino_commands, durations):
        thread = threading.Thread(target=send_to_arduino, args=(arduino_command, duration))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return True


import json
import time

def execute_sequence(sequence_file, flow_rates, calibration_callback=None):
    """
    Read the sequence from a JSON file and execute the actions.

    Parameters:
        sequence_file (str): Path to the JSON file containing the sequence.
        flow_rates (dict): Dictionary containing flow rates for each pump.
        calibration_callback (function): Optional callback for calibration steps.
    """
    try:
        with open(sequence_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Error: {sequence_file} not found.")
        return

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
                    calibration_callback()  # Call the calibration function
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
