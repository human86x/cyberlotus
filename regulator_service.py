import json
import time
from datetime import datetime
import serial

# Serial configuration
serial_port = '/dev/ttyACM0'  # Update with your port
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)

# Load desired parameters from JSON file
def load_desired_parameters(filename="data/desired_parameters.json"):
    try:
        with open(filename, "r") as file:
            params = json.load(file)
            # Ensure all values are converted to float
            return {key: float(value) for key, value in params.items()}
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please create the file with desired parameters.")
        exit(1)
    except ValueError as e:
        print(f"Error parsing {filename}: {e}")
        exit(1)

# Load sensor data from JSON file
def load_sensor_data(filename="data/sensor_data.json"):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please ensure the sensor service is running.")
        return {}
    except ValueError as e:
        print(f"Error parsing {filename}: {e}")
        return {}

# Check if the sensor data is fresh
def is_fresh(timestamp, freshness_threshold=10):
    try:
        reading_time = datetime.fromisoformat(timestamp)
        current_time = datetime.now()
        delta = (current_time - reading_time).total_seconds()
        return delta <= freshness_threshold  # True if data is within the threshold
    except ValueError:
        print(f"Invalid timestamp format: {timestamp}")
        return False

# Function to send commands to Arduino to control pumps
def control_pin(pin, state):
    try:
        command = f"{pin}{state}".encode()  # Create command
        ser.write(command)  # Send command
        time.sleep(0.1)  # Short delay for Arduino to process
        response = ser.readline().decode('utf-8').strip()  # Read response
        return response
    except Exception as e:
        print(f"Error controlling pin {pin}: {e}")
        return str(e)

# Regulator function that checks sensor data against desired values
def regulate():
    desired_params = load_desired_parameters()
    while True:
        sensor_data = load_sensor_data()
        print(f"Sensor Data: {sensor_data}")  # Optional: Print the data to the console

        # Validate freshness
        if "timestamp" not in sensor_data or not is_fresh(sensor_data["timestamp"]):
            print("Sensor data is outdated or invalid. Skipping regulation.")
            time.sleep(5)
            continue

        # Compare current sensor readings with desired values
        for key, desired_value in desired_params.items():
            if key in sensor_data:
                try:
                    current_value = float(sensor_data[key])  # Ensure conversion to float
                    print(f"Comparing {key}: Current Value = {current_value}, Desired Value = {desired_value}")
                except ValueError:
                    print(f"Error converting {sensor_data[key]} to float for {key}")
                    continue  # Skip if there's an issue with the data
                
                if current_value < desired_value:
                    # Turn on the pump
                    pin = get_corresponding_pin(key)
                    if pin:
                        control_pin(pin, 'o')
                elif current_value > desired_value:
                    # Turn off the pump
                    pin = get_corresponding_pin(key)
                    if pin:
                        control_pin(pin, 'f')

        time.sleep(5)  # Adjust the interval as needed

def get_corresponding_pin(sensor):
    # Map sensor names to Arduino pins
    sensor_to_pin = {
        "temperature": "t",  # Add mapping for temperature
        "nitrogen": "a",
        "potassium": "b",
        "phosphorus": "c",
        "ph": "d",
        "water_level": "l"
    }
    return sensor_to_pin.get(sensor)

if __name__ == "__main__":
    regulate()
