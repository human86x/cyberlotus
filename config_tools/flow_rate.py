import json
import time
import serial

# Serial port settings
SERIAL_PORT = "/dev/ttyACM0"  # Use Linux serial port
BAUD_RATE = 9600

# JSON file path
FLOW_RATES_FILE = "data/flow_rates.json"

# Mapping of pump names to Arduino commands
PUMP_COMMANDS = {
    "NPK": "a",
    "pH_plus": "b",
    "pH_minus": "c",
    "pH_cal_high": "d",
    "pH_cal_low": "e",
    "EC_cal": "f",
    "fresh_water_speed": "g",
    "draining_speed": "h"
}

# Initialize serial communication
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

def load_flow_rates():
    """Load flow rates from JSON file."""
    try:
        with open(FLOW_RATES_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_flow_rates(flow_rates):
    """Save flow rates to JSON file."""
    with open(FLOW_RATES_FILE, "w") as file:
        json.dump(flow_rates, file, indent=4)

def calibrate_pump(pump_name, duration):
    """Calibrate a pump by measuring flow rate."""
    if pump_name not in PUMP_COMMANDS:
        print(f"Error: Invalid pump name '{pump_name}'")
        return None

    print(f"Activating pump '{pump_name}' for {duration} seconds.")
    ser.write(f"{PUMP_COMMANDS[pump_name]}o".encode())  # Turn on the pump
    time.sleep(duration)
    ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())  # Turn off the pump

    print("Enter the weight of the liquid pumped (in grams):")
    weight = float(input("Weight (grams): "))
    flow_rate = weight / duration
    print(f"Calculated flow rate for {pump_name}: {flow_rate:.3f} g/s")
    return flow_rate

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
    ser.write(f"{PUMP_COMMANDS[pump_name]}o".encode())  # Turn on the pump
    time.sleep(duration)
    ser.write(f"{PUMP_COMMANDS[pump_name]}f".encode())  # Turn off the pump
    print("Test complete.")

def main():
    flow_rates = load_flow_rates()

    while True:
        print("\nOptions:")
        print("1. Calibrate pump")
        print("2. Test pump")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            pump_name = input("Enter pump name (e.g., NPK, pH_plus): ")
            duration = float(input("Enter activation duration (seconds): "))
            flow_rate = calibrate_pump(pump_name, duration)
            if flow_rate is not None:
                flow_rates[pump_name] = flow_rate
                save_flow_rates(flow_rates)
        elif choice == "2":
            pump_name = input("Enter pump name (e.g., NPK, pH_plus): ")
            weight = float(input("Enter desired weight (grams): "))
            test_pump(pump_name, weight)
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
