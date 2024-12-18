import json
import time
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
goal_file = "data/desired_parameters.json"

def write_to_json(file_path, data):
    """Write data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

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

# Continuous data fetching and JSON update loop
try:
    if client.connect():
        print("Connected to Modbus device. Starting data collection...")
        while True:
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
                    }

                    # Fetch the current weight for tank_1
                    weight = get_tank_weight()
                    if weight is not None:
                        current_data["tank_1_weight"] = weight  # Store only the current weight
                        print(f"Tank 1 weight: {weight} kg")
                    else:
                        print("Failed to fetch tank weight")
                        current_data["tank_1_weight"] = None

                    # Write the updated data to the JSON file
                    write_to_json(data_file, current_data)
                    print("Updated sensor data saved to JSON.")

                    # Print the current data for confirmation
                    print(json.dumps(current_data, indent=4))

            except Exception as e:
                print(f"Error during data update: {e}")

            # Sleep before the next update (e.g., 5 seconds)
            time.sleep(5)

    else:
        print("Unable to connect to the Modbus device")

except KeyboardInterrupt:
    print("\nData collection stopped by user.")

finally:
    client.close()
    arduino_serial.close()
    print("Connections closed.")
