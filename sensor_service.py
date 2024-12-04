import time
import json
import random
from datetime import datetime

# Simulating temperature sensor (replace with actual sensor code)
def read_temperature():
    # Example: Replace with your actual sensor code for reading temperature
    return round(random.uniform(22.0, 30.0), 2)  # Random temp between 22-30°C

# Simulating other sensors
def read_nitrogen():
    return round(random.uniform(60.0, 100.0), 2)  # ppm

def read_potassium():
    return round(random.uniform(50.0, 90.0), 2)  # ppm

def read_phosphorus():
    return round(random.uniform(40.0, 80.0), 2)  # ppm

def read_ph():
    return round(random.uniform(5.5, 7.0), 2)  # pH between 5.5 and 7.0

def read_fresh_water():
    return round(random.uniform(300.0, 500.0), 2)  # mL

# Function to read all sensor data
def read_sensors():
    return {
        "temperature": read_temperature(),
        "nitrogen": read_nitrogen(),
        "potassium": read_potassium(),
        "phosphorus": read_phosphorus(),
        "ph": read_ph(),
        "fresh_water": read_fresh_water(),
        "timestamp": datetime.now().isoformat()  # Add timestamp to track data
    }

# Function to save sensor data to JSON file
def save_sensor_data(data, filename="data/sensor_data.json"):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Main loop to keep reading sensors
def run_sensor_service():
    while True:
        sensor_data = read_sensors()
        print(f"Sensor Data: {sensor_data}")  # Optional: Print the data to the console
        save_sensor_data(sensor_data)
        time.sleep(5)  # Wait for 5 seconds before taking another reading (adjust as needed)

if __name__ == "__main__":
    run_sensor_service()
