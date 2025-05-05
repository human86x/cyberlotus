import serial
import time
import json
import os
import sys
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from device_connections import connect_to_arduino  # Import after modifying the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from control_libs.electric_conductivity import get_ec
#from control_libs.temperature import read_solution_temperature
from control_libs.arduino import connect_to_arduino, get_serial_connection , safe_serial_write, send_command_and_get_response
from control_libs.system_stats import append_console_message
# Serial configuration
#SERIAL_PORT = '/dev/ttyACM0'
#BAUD_RATE = 9600
HEARTBEAT_TIMEOUT = 2  # Maximum time (seconds) to wait for a heartbeat

# File paths
# Get the absolute path of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define file paths relative to this script's location
PUMP_COMMANDS_FILE = os.path.join(current_dir, '../data/relay_names.json')
FLOW_RATES_FILE = os.path.join(current_dir, '../data/flow_rates.json')

# Initialize serial connection
ser = connect_to_arduino()#get_serial_connection() #serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

def load_pump_commands():
    """Load pump commands from JSON file."""
    if not os.path.exists(PUMP_COMMANDS_FILE):
        append_console_message(f"Error: {PUMP_COMMANDS_FILE} not found.")
        return {}
    with open(PUMP_COMMANDS_FILE, 'r') as file:
        return json.load(file)

# Load PUMP_COMMANDS from the JSON file
PUMP_COMMANDS = load_pump_commands()

def wait_for_heartbeat(timeout=HEARTBEAT_TIMEOUT):
    """Wait for the heartbeat signal from Arduino."""
    start_time = time.time()
    heartbeat_count = 0

    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            if line == "HEARTBEAT":
                heartbeat_count += 1
                if heartbeat_count >= 2:  # Require 2 heartbeats
                    return True
    return False

def load_flow_rates():
    """Load flow rates from JSON file."""
    if not os.path.exists(FLOW_RATES_FILE):
        append_console_message(f"Error: {FLOW_RATES_FILE} not found.")
        return {}
    with open(FLOW_RATES_FILE, 'r') as file:
        return json.load(file)

def save_flow_rates(flow_rates):
    """Save updated flow rates to JSON file."""
    with open(FLOW_RATES_FILE, 'w') as file:
        json.dump(flow_rates, file, indent=4)


def send_command_with_heartbeat(command, duration=None):
    global ser
    """
    Send a command to Arduino with heartbeat checks before and during operation.

    Parameters:
        command (str): The command to send (e.g., pump name).
        duration (float or int): Duration in seconds.
            - If duration == 0: Turn ON the pump and exit immediately.
            - If duration == -1: Turn OFF the pump and exit immediately.
            - If duration > 0: Turn ON the pump, wait for the duration, then turn OFF the pump.
    """
    time.sleep(2)
    # Try to connect to Arduino if the port is not open
    if not ser.is_open:
        append_console_message("Arduino port not open. Attempting to reconnect...")
        ser = connect_to_arduino()
        if not ser:
            append_console_message("Error: Unable to connect to Arduino. Aborting command.")
            return False

    append_console_message(f"Preparing to send command '{command}' to Arduino...")

    if duration == 0:
        # Turn ON the pump and exit immediately
        safe_serial_write(command, "o")  # "o" for ON
        append_console_message(f"Pump '{command}' turned ON.")
        return True
    elif duration == -1:
        # Turn OFF the pump and exit immediately
        safe_serial_write(command, "f")  # "f" for OFF
        append_console_message(f"Pump '{command}' turned OFF.")
        return True
    elif duration > 0:
        # Turn ON the pump, wait for the duration, then turn OFF the pump
        safe_serial_write(command, "o")  # "o" for ON
        append_console_message(f"Pump '{command}' turned ON. Waiting for {duration:.2f}s...")

        start_time = time.time()
        while time.time() - start_time < duration:
            time_elapsed = time.time() - start_time
            progress = min(int((time_elapsed / duration) * 100), 100)  # Ensure max progress is 100%
            append_console_message(f"Operation in progress... {progress}% complete.", end="\r")
            time.sleep(0.1)  # Small delay to avoid excessive CPU usage

        safe_serial_write(command, "f")  # "f" for OFF
        append_console_message(f"\nPump '{command}' turned OFF.")
        return True
    else:
        append_console_message(f"Error: Invalid duration value {duration}. Duration must be 0, -1, or a positive number.")
        return False

def calibrate_pump(pump_name):
    """Calibrate the pump by determining its flow rate."""
    flow_rates = load_flow_rates()
    if pump_name not in PUMP_COMMANDS:
        append_console_message(f"Error: Invalid pump name '{pump_name}'")
        return

    append_console_message(f"Calibrating pump '{pump_name}'.")
    input("Place the container on the scale and press Enter to start calibration.")
    append_console_message("Pumping for 10 seconds...")
    if not send_command_with_heartbeat(PUMP_COMMANDS[pump_name], duration=10):  # Set calibration duration to 10 seconds
        append_console_message("Error: Calibration failed due to Arduino communication issue.")
        return

    weight = float(input("Enter the weight of liquid pumped (in grams): "))
    flow_rate = weight / 10  # Calculate flow rate (grams per second), adjusted for 10 seconds
    append_console_message(f"Calibration complete. Flow rate for '{pump_name}' is {flow_rate:.3f} g/s.")
    flow_rates[pump_name] = flow_rate
    save_flow_rates(flow_rates)
    append_console_message(f"Updated flow rates saved to {FLOW_RATES_FILE}.")

def test_pump(pump_name, weight):
    """Test pump accuracy by dispensing a specific weight of liquid."""
    flow_rates = load_flow_rates()
    if pump_name not in flow_rates:
        append_console_message(f"Error: Flow rate for '{pump_name}' not found.")
        return
    if pump_name not in PUMP_COMMANDS:
        append_console_message(f"Error: Invalid pump name '{pump_name}'")
        return

    flow_rate = flow_rates[pump_name]
    duration = weight / flow_rate

    append_console_message(f"Activating pump '{pump_name}' for {duration:.2f} seconds to dispense {weight} grams.")
    if not send_command_with_heartbeat(PUMP_COMMANDS[pump_name], duration=duration):
        append_console_message(f"Error: Failed to complete operation for pump '{pump_name}'.")


pump_progress ={}

def test_pump_with_progress(pump_name, weight):
    #global PUMP_COMMANDS  # Ensure global access
    global PUMP_COMMANDS  # Ensure global access
    PUMP_COMMANDS = load_pump_commands()
    #pump_names = list(PUMP_COMMANDS.keys())
    global ser
    ser = get_serial_connection()
    """Test the pump with progress updates."""
    
    flow_rates = load_flow_rates()
    append_console_message(f"******pump_name======={pump_name}")
    if pump_name not in flow_rates or pump_name not in PUMP_COMMANDS:
        pump_progress[pump_name] = -1  # Error state
        return

    flow_rate = flow_rates[pump_name]
    duration = weight / flow_rate

    #ser.write(f"{PUMP_COMMANDS[pump_name]}o".encode())
    safe_serial_write(PUMP_COMMANDS[pump_name], 'o')  # Turn ON
    for i in range(int(duration * 10)):
        pump_progress[pump_name] = int((i / (duration * 10)) * 100)
        time.sleep(0.1)
        append_console_message(f"Adjustment process - {pump_progress[pump_name]}")

    #ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())
    safe_serial_write(PUMP_COMMANDS[pump_name], 'f')  # Turn Off
    pump_progress[pump_name] = 100  # Complete








# Example usage
if __name__ == "__main__":
    while True:
        append_console_message("\nOptions:")
        append_console_message("1. Calibrate pump")
        append_console_message("2. Test pump")
        append_console_message("3. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            pump = input("Enter pump name (e.g., NPK, pH_plus): ")
            calibrate_pump(pump)
        elif choice == "2":
            pump = input("Enter pump name (e.g., NPK, pH_plus): ")
            weight = float(input("Enter desired weight (grams): "))
            test_pump(pump, weight)
        elif choice == "3":
            append_console_message("Exiting...")
            break
        else:
            append_console_message("Invalid choice. Try again.")
