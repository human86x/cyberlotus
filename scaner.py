import json
from datetime import datetime
from pymodbus.client import ModbusSerialClient as ModbusClient
import serial  # For communicating with the Arduino

# Configure Modbus client
client = ModbusClient(
    method='rtu',
    port='/dev/ttyUSB0',  # Update to your actual port
    baudrate=4800,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=2
)

# Configure Serial communication for Arduino
arduino_port = '/dev/ttyACM0'  # Update to your actual port
arduino_baudrate = 9600
arduino_timeout = 2

arduino_serial = serial.Serial(
    port=arduino_port,
    baudrate=arduino_baudrate,
    timeout=arduino_timeout
)

# Paths for JSON files
data_file = "data/sensor_data.json"
goal_file = "data/desired_parametrs.json"

def write_to_json(file_path, data):
    """Write data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def read_from_json(file_path):
    """Read data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_tank_weight():
    """Fetch the tank level (weight) from Arduino via Serial."""
    try:
        # Send "W" command to Arduino
        arduino_serial.write(b'W')
        # Read the response
        response = arduino_serial.readline().decode().strip()
        # Parse the response as a float
        return float(response)
    except Exception as e:
        print(f"Error reading tank weight: {e}")
        return None

# Initialize tank weight structure
tanks = {
    "tank_1": {
        "current_weight": None,  # Placeholder for the actual weight (kg)
        "min_weight": 5.0,       # Minimum acceptable weight (kg)
        "max_weight": 10.0       # Maximum acceptable weight (kg)
    }
}

# Connect to the client
if client.connect():
    try:
        # Read multiple registers (humidity, temperature, conductivity, pH, N, P, K)
        result = client.read_holding_registers(address=0, count=7, slave=1)
        if result.isError():
            print(f"Error reading registers: {result}")
        else:
            # Parse results
            data = result.registers
            current_data = {
                "timestamp": datetime.now().isoformat(),  # Add a timestamp
                "humidity": data[0] * 0.1,  # Convert to %
                "temperature": data[1] * 0.1,  # Convert to °C
                "conductivity": data[2],  # μS/cm
                "pH": data[3] * 0.1,  # Convert to actual pH
                "nitrogen": data[4],  # mg/kg
                "phosphorus": data[5],  # mg/kg
                "potassium": data[6],  # mg/kg,
                "tanks": tanks  # Include tanks' weight data
            }

            # Fetch the weight for tank_1
            weight = get_tank_weight()
            if weight is not None:
                current_data["tanks"]["tank_1"]["current_weight"] = weight
                print(f"Tank 1 weight: {weight} kg")
            else:
                print("Failed to fetch tank weight")

            # Write current measurements to JSON file
            write_to_json(data_file, current_data)
            print("Current measurements saved to JSON.")

            # Print data for confirmation
            print(json.dumps(current_data, indent=4))

            # Check for and display target values from the goal JSON file
            goal_data = read_from_json(goal_file)
            if goal_data:
                print("\nTarget measurements from goal file:")
                print(json.dumps(goal_data, indent=4))
            else:
                print("\nNo goal measurements found. Please set target values in the goal JSON file.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        arduino_serial.close()
else:
    print("Unable to connect to the Modbus device")
