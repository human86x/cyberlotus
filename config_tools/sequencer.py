import json
import time
from flow_rate import send_command_with_heartbeat, load_flow_rates

# File paths
SEQUENCE_FILE = '../data/pH_calibration.json'

# Function to execute a single command in the sequence
def execute_command(command, weight, flow_rates):
    """Execute the given command for a specific weight using flow rates."""
    print(f"Executing command: {command} for {weight}g")
    
    if command not in flow_rates:
        print(f"Error: Flow rate for '{command}' not found in flow rates file.")
        return False

    # Calculate duration based on flow rate
    flow_rate = flow_rates[command]
    duration = weight / flow_rate  # Time in seconds to pump the given weight

    return send_command_with_heartbeat(command, duration)

# Function to execute the sequence from the JSON file
def execute_sequence(sequence_file, flow_rates):
    """Read the sequence from a JSON file and execute the actions."""
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
            # Simulate the calibration waiting logic (replace with actual calibration function if necessary)
            input(f"Calibration needed for {command}. Press Enter when calibration is complete.")
        
        # Execute the command after calibration (if applicable)
        if not execute_command(command, weight, flow_rates):
            print(f"Error: Failed to execute command {command}.")
            break

        time.sleep(1)  # Small delay to prevent overwhelming the system

    print("Sequence complete.")

# Example usage
if __name__ == "__main__":
    flow_rates = load_flow_rates()  # Load flow rates from the JSON file
    if flow_rates:
        execute_sequence(SEQUENCE_FILE, flow_rates)
