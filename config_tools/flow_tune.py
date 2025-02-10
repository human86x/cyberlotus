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
        print(f"Error: {PUMP_COMMANDS_FILE} not found.")
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
        print(f"Error: {FLOW_RATES_FILE} not found.")
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
    If duration is provided, the command assumes a timed operation (e.g., dosing).
    Includes reconnection attempts if the serial port is not open.
    """
    time.sleep(2)
    # Try to connect to Arduino if the port is not open
    if not ser.is_open:
        print("Arduino port not open. Attempting to reconnect...")
        ser = connect_to_arduino()
        if not ser:
            print("Error: Unable to connect to Arduino. Aborting command.")
            return False

    print(f"Preparing to send command '{command}' to Arduino...")

    # Simulate heartbeat verification (this could be uncommented if you have a heartbeat check function)
    # if not wait_for_heartbeat():
    #     print("Error: No heartbeat detected. Arduino may not be responding.")
    #     return False

    #print("Heartbeat verified. Sending command to Arduino...")
    #ser.write(f"{command}".encode(),"o")  # Turn on the pump
    safe_serial_write(command,"o")

    if duration:
        start_time = time.time()
        while time.time() - start_time < duration:
            time_elapsed = time.time() - start_time
            progress = min(int((time_elapsed / duration) * 100), 100)  # Ensure max progress is 100%
            print(f"Operation in progress... {progress}% complete.", end="\r")

            # Simulate heartbeat check during operation (uncomment if needed)
            # if not wait_for_heartbeat(timeout=1):
            #     print("\nWarning: Arduino heartbeat delay detected during operation!")
            #     break

            time.sleep(0.1)  # Small delay to avoid excessive CPU usage

        safe_serial_write(command,"f")  # Turn off the pump
        print("\nOperation complete.")

    return True

def calibrate_pump(pump_name):
    """Calibrate the pump by determining its flow rate."""
    flow_rates = load_flow_rates()
    if pump_name not in PUMP_COMMANDS:
        print(f"Error: Invalid pump name '{pump_name}'")
        return

    print(f"Calibrating pump '{pump_name}'.")
    input("Place the container on the scale and press Enter to start calibration.")
    print("Pumping for 10 seconds...")
    if not send_command_with_heartbeat(PUMP_COMMANDS[pump_name], duration=10):  # Set calibration duration to 10 seconds
        print("Error: Calibration failed due to Arduino communication issue.")
        return

    weight = float(input("Enter the weight of liquid pumped (in grams): "))
    flow_rate = weight / 10  # Calculate flow rate (grams per second), adjusted for 10 seconds
    print(f"Calibration complete. Flow rate for '{pump_name}' is {flow_rate:.3f} g/s.")
    flow_rates[pump_name] = flow_rate
    save_flow_rates(flow_rates)
    print(f"Updated flow rates saved to {FLOW_RATES_FILE}.")

def test_pump(pump_name, weight):
    """Test pump accuracy by dispensing a specific weight of liquid."""
    flow_rates = load_flow_rates()
    if pump_name not in flow_rates:
        print(f"Error: Flow rate for '{pump_name}' not found.")
        return
    if pump_name not in PUMP_COMMANDS:
        print(f"Error: Invalid pump name '{pump_name}'")
        return

    flow_rate = flow_rates[pump_name]
    duration = weight / flow_rate

    print(f"Activating pump '{pump_name}' for {duration:.2f} seconds to dispense {weight} grams.")
    if not send_command_with_heartbeat(PUMP_COMMANDS[pump_name], duration=duration):
        print(f"Error: Failed to complete operation for pump '{pump_name}'.")

# Example usage
if __name__ == "__main__":
    while True:
        print("\nOptions:")
        print("1. Calibrate pump")
        print("2. Test pump")
        print("3. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            pump = input("Enter pump name (e.g., NPK, pH_plus): ")
            calibrate_pump(pump)
        elif choice == "2":
            pump = input("Enter pump name (e.g., NPK, pH_plus): ")
            weight = float(input("Enter desired weight (grams): "))
            test_pump(pump, weight)
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")
