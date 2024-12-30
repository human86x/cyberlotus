import json
import time
import serial

# Path to the flow rates JSON file
FLOW_RATES_FILE = "data/flow_rates.json"

# Initialize serial communication with Arduino
ser = serial.Serial('COM3', 9600, timeout=1)  # Adjust COM port as needed
time.sleep(2)  # Allow time for serial connection to initialize

def load_flow_rates():
    """Load flow rates from the JSON file."""
    try:
        with open(FLOW_RATES_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_flow_rates(flow_rates):
    """Save flow rates to the JSON file."""
    with open(FLOW_RATES_FILE, 'w') as file:
        json.dump(flow_rates, file, indent=4)

def control_pump(pump, duration):
    """Send command to Arduino to activate a pump for a specified duration."""
    command = f"{pump}o"  # Turn pump on
    ser.write(command.encode())
    time.sleep(duration)
    ser.write(f"{pump}f".encode())  # Turn pump off
    
    print(f"Pump {pump} activated for {duration} seconds.")

def calibrate_pump():
    """Calibrate flow rate for a pump."""
    pump = input("Enter pump ID (a-e): ")
    duration = float(input("Enter activation duration in seconds: "))

    print("Activate the pump and measure the weight of the liquid...")
    control_pump(pump, duration)

    weight = float(input("Enter the weight of liquid pumped (grams): "))
    flow_rate = weight / duration

    flow_rates = load_flow_rates()
    pump_name = input("Enter the name of the liquid (e.g., NPK, pH_plus): ")
    flow_rates[pump_name] = flow_rate
    save_flow_rates(flow_rates)

    print(f"Flow rate for {pump_name} updated: {flow_rate} g/s")

def test_pump():
    """Test the pump to deliver a specific weight of liquid."""
    pump_name = input("Enter the name of the liquid to test (e.g., NPK, pH_plus): ")
    weight = float(input("Enter the desired weight of liquid (grams): "))

    flow_rates = load_flow_rates()
    if pump_name not in flow_rates:
        print(f"Flow rate for {pump_name} not found. Please calibrate first.")
        return

    flow_rate = flow_rates[pump_name]
    duration = weight / flow_rate

    pump = input("Enter pump ID (a-e): ")
    print(f"Activating pump {pump} to deliver {weight} grams...")
    control_pump(pump, duration)

    print(f"Pump {pump} ran for {duration:.2f} seconds to deliver {weight} grams.")

def main():
    """Main menu for the script."""
    while True:
        print("\nPump Calibration and Testing System")
        print("1. Calibrate Pump")
        print("2. Test Pump")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            calibrate_pump()
        elif choice == '2':
            test_pump()
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
