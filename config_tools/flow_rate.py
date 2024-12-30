import serial
import time
import json
import os

# Serial configuration
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
HEARTBEAT_TIMEOUT = 2  # Maximum time (seconds) to wait for a heartbeat
PUMP_COMMANDS = {
    "NPK": 'a',
    "pH_plus": 'b',
    "pH_minus": 'c',
    "pH_cal_high": 'd',
    "pH_cal_low": 'e',
    "EC_cal": 'f',
    "fresh_water": 'g',
    "drain": 'h'
}

# File paths
FLOW_RATES_FILE = '../data/flow_rates.json'

# Initialize serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

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

def send_command_with_heartbeat(command, duration=None):
    """
    Send a command to Arduino with heartbeat checks before and during operation.
    If duration is provided, the command assumes a timed operation (e.g., dosing).
    """
    print(f"Preparing to send command '{command}' to Arduino...")
    if not wait_for_heartbeat():
        print("Error: No heartbeat detected. Arduino may not be responding.")
        return False

    print("Heartbeat verified. Sending command to Arduino...")
    ser.write(f"{command}o".encode())  # Turn on the pump
    if duration:
        start_time = time.time()
        while time.time() - start_time < duration:
            time_elapsed = time.time() - start_time
            progress = int((time_elapsed / duration) * 100)
            print(f"Operation in progress... {progress}% complete.", end="\r")

            # Check for heartbeat during operation
            if not wait_for_heartbeat(timeout=1):
                print("\nWarning: Arduino heartbeat delay detected during operation!")
                break
            time.sleep(0.1)  # Small delay to avoid excessive CPU usage
        ser.write(f"{command}f".encode())  # Turn off the pump
        print("\nOperation complete.")
    return True

def load_flow_rates():
    """Load flow rates from JSON file."""
    if not os.path.exists(FLOW_RATES_FILE):
        print(f"Error: {FLOW_RATES_FILE} not found.")
        return {}
    with open(FLOW_RATES_FILE, 'r') as file:
        return json.load(file)

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
        print("1. Test pump")
        print("2. Exit")
        choice = input("Enter your choice: ")
        if choice == "1":
            pump = input("Enter pump name (e.g., NPK, pH_plus): ")
            weight = float(input("Enter desired weight (grams): "))
            test_pump(pump, weight)
        elif choice == "2":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")
