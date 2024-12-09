import json
import time
from datetime import datetime
# import serial

# Serial configuration (commented out for testing purposes)
# serial_port = '/dev/ttyACM0'  # Update with your port
# baud_rate = 9600
# ser = serial.Serial(serial_port, baud_rate, timeout=1)
# time.sleep(2)

# Load desired parameters from JSON file
def load_desired_parameters(filename="data/desired_parameters.json"):
    try:
        with open(filename, "r") as file:
            params = json.load(file)
            return {
                key: float(value) if isinstance(value, (int, float)) else value
                for key, value in params.items()
            }
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
            return json.load(file)
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
        delta = (datetime.now() - reading_time).total_seconds()
        return delta <= freshness_threshold
    except ValueError:
        print(f"Invalid timestamp format: {timestamp}")
        return False

# Function to send commands to Arduino to control pumps
def control_pin(pin, state):
    try:
        command = f"{pin}{state}".encode()  # Create command
        # ser.write(command)  # Send command to Arduino (commented out for testing)
        time.sleep(0.1)  # Short delay for Arduino to process
        # response = ser.readline().decode('utf-8').strip()  # Read response
        # return response
        return f"Command sent: {command.decode()}"  # Simulated response
    except Exception as e:
        print(f"Error controlling pin {pin}: {e}")
        return str(e)

# Map sensor names to Arduino pins
def get_corresponding_pin(sensor):
    sensor_to_pin = {
        "temperature": "t",
        "nitrogen": "a",
        "potassium": "b",
        "phosphorus": "c",
        "ph": "d",
        "water_level": "l"
    }
    return sensor_to_pin.get(sensor)

# Regulator function that checks sensor data against desired values
def regulate():
    desired_params = load_desired_parameters()

    while True:
        sensor_data = load_sensor_data()
        print(f"Sensor Data: {sensor_data}")

        # Validate freshness
        if "timestamp" not in sensor_data or not is_fresh(sensor_data["timestamp"]):
            print("Sensor data is outdated or invalid. Skipping regulation.")
            time.sleep(5)
            continue

        # Compare current sensor readings with desired values
        for key, desired_value in desired_params.items():
            if key in sensor_data:
                if "time" in key.lower():
                    continue  # Skip timestamp-related keys

                try:
                    current_value = float(sensor_data[key])
                    print(f"Comparing {key}: Current Value = {current_value}, Desired Value = {desired_value}")

                    if current_value < desired_value:
                        pin = get_corresponding_pin(key)
                        if pin:
                            control_pin(pin, 'o')  # Activate pump
                    elif current_value > desired_value:
                        pin = get_corresponding_pin(key)
                        if pin:
                            control_pin(pin, 'f')  # Deactivate pump

                except ValueError:
                    print(f"Error converting sensor value for {key}: {sensor_data[key]}")
                    continue

        time.sleep(5)  # Adjust as needed

# Function to generate nutrient adjustment script
def action_script_make(
    sensor_file="data/sensor_data.json",
    target_file="data/desired_parameters.json",
    flow_rate_file="data/flow_rates.json",
    output_file="data/nutrient_adjustments.json"
):
    try:
        sensor_data = load_sensor_data(sensor_file)
        desired_params = load_desired_parameters(target_file)

        with open(flow_rate_file, "r") as file:
            flow_rates = json.load(file)

        adjustments = []

        for key, desired_value in desired_params.items():
            if key in sensor_data and "time" not in key.lower():
                try:
                    current_value = float(sensor_data[key])
                    difference = desired_value - current_value

                    if difference != 0:
                        flow_rate = float(flow_rates.get(key, 1))  # Default flow rate to avoid division by zero
                        pump_time_ms = abs(difference) / flow_rate * 1000  # Convert to milliseconds

                        adjustments.append({
                            "timestamp": datetime.now().isoformat(),
                            "nutrient": key,
                            "current_value": current_value,
                            "desired_value": desired_value,
                            "difference": difference,
                            "pump_time_ms": round(pump_time_ms, 2),
                        })
                except ValueError:
                    print(f"Error converting sensor value for {key}: {sensor_data[key]}")

        with open(output_file, "w") as file:
            json.dump(adjustments, file, indent=4)

        print(f"Adjustments recorded in {output_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    action_script_make()
