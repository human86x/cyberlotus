import time
import json
from datetime import datetime
import serial

# Serial configuration
serial_port = '/dev/ttyACM0'  # Update with your port
baud_rate = 9600

# Establish serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)  # Allow Arduino to initialize

# Function to read solution temperature from Dallas temperature sensor
def read_solution_temperature():
    ser.write(b'T')  # Command to read temperature from Arduino
    line = ser.readline().decode('utf-8').strip()
    try:
        return float(line)
    except ValueError:
        print(f"Error reading temperature: {line}")
        return None

# Function to read tank level from ultrasonic sensor
def read_tank_level():
    ser.write(b'L')  # Command to read level from Arduino
    line = ser.readline().decode('utf-8').strip()
    try:
        return float(line)
    except ValueError:
        print(f"Error reading tank level: {line}")
        return None

# Placeholder functions for future sensors
def read_ec():
    return None  # Placeholder for EC sensor

def read_ph():
    return None  # Placeholder for pH sensor

# Function to read all sensor data
def read_sensors():
    return {
        "solution_temperature": read_solution_temperature(),
        "tank_level": read_tank_level(),
        "ec": read_ec(),
        "ph": read_ph(),
        "timestamp": datetime.now().isoformat()
    }

# Function to save sensor data to JSON file
def save_sensor_data(data, filename="data/sensor_data.json"):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Main loop to keep reading sensors
def run_sensor_service():
    while True:
        sensor_data = read_sensors()
        print(f"Sensor Data: {sensor_data}")
        save_sensor_data(sensor_data)
        time.sleep(5)  # Adjust as needed

if __name__ == "__main__":
    run_sensor_service()
