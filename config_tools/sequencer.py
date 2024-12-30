import json
import time
from flow_rate import send_command_with_heartbeat, load_flow_rates

# File paths
CALIBRATION_FILE = 'pH_calibration.json'

# Function to execute a single command in the sequence
def execute_command(command, weight):
    """Execute the given command for a specific weight."""
    print(f"Executing command: {command} for {weight}g")
    if command not in PUMP_COMMANDS:
        print(f"Error: Invalid command '{command}'")
        return False
    return send_command_with_heartbeat(PUMP_COMMANDS[command], duration=weight / load_flow_rates()[command])

# Function to execute the sequence from the JSON file
def execute_sequence(sequence_file):
    """Read the sequence from a JSON file and execute the actions."""
    with open(sequence_file, 'r') as file:
        data = json.load(file)

    for action in data["sequence"]:
        command = action["command"]
        weight = action["weight"]

        # Check for calibration actions
        if "calibration" in action and action["calibration"]:
            print(f"Calibration step detected. Waiting for calibration...")
            # Here we simulate the calibration waiting logic (replace with actual calibration function in the future)
            input(f"Calibration needed for {command}. Press Enter when calibration is complete.")
        
        # Execute the command after calibration (if applicable)
        if not execute_command(command, weight):
            print(f"Error: Failed to execute command {command}.")
            break

        time.sleep(1)  # Small delay to prevent overwhelming the system

    print("Sequence complete.")

# Example usage
if __name__ == "__main__":
    execute_sequence(CALIBRATION_FILE)
