import json
import time
import serial

# Serial configuration
serial_port = '/dev/ttyACM0'  # Update with your port
baud_rate = 9600
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)

# Load desired parameters from JSON file
# Function to load the desired parameters from a JSON file
def load_desired_parameters(filename="data/desired_params.json"):
    with open(filename, "r") as file:
        params = json.load(file)
        # Ensure all values are converted to float
        return {key: float(value) for key, value in params.items()}

# Read temperature and other sensor data
def read_temperature():
    ser.write(b'R')  # Send a read command to Arduino
    line = ser.readline().decode('utf-8').strip()
    return line

def read_sensors():
    return {
        "temperature": read_temperature(),
        # Add other sensors here...
    }

# Function to send commands to Arduino to control pumps
def control_pin(pin, state):
    try:
        command = f"{pin}{state}".encode()  # Create command
        ser.write(command)  # Send command
        time.sleep(0.1)  # Short delay for Arduino to process
        response = ser.readline().decode('utf-8').strip()  # Read response
        return response
    except Exception as e:
        return str(e)

# Regulator function that checks sensor data against desired values
def regulate():
    desired_params = load_desired_parameters()
    while True:
        sensor_data = read_sensors()
        print(f"Sensor Data: {sensor_data}")  # Optional: Print the data to the console

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
                    # Turn on the pump (example: Nitrogen)
                    pin = get_corresponding_pin(key)
                    control_pin(pin, 'o')
                elif current_value > desired_value:
                    # Turn off the pump (example: Nitrogen)
                    pin = get_corresponding_pin(key)
                    control_pin(pin, 'f')

        time.sleep(5)  # Adjust the interval as needed

def get_corresponding_pin(sensor):
    # Map sensor names to Arduino pins
    sensor_to_pin = {
        "nitrogen": "a",
        "potassium": "b",
        "phosphorus": "c",
        "ph": "d",
        "water_level": "l"
    }
    return sensor_to_pin.get(sensor)

if __name__ == "__main__":
    regulate()
