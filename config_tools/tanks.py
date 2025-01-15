import json
import time
import os
import sys
import statistics
from sequencer import execute_sequence
from flow_tune import send_command_with_heartbeat, load_flow_rates
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from control_libs.electric_conductivity import get_ec
from control_libs.temperature import read_solution_temperature
from control_libs.arduino import connect_to_arduino, send_command_and_get_response

base_dir = os.path.dirname(os.path.abspath(__file__))

# Use absolute paths for file locations
EC_SEQUENCE_FILE = os.path.join(base_dir, '../sequences/EC_calibration.json')
EC_BASELINE_FILE = os.path.join(base_dir, '../sequences/EC_baseline.json')
CALIBRATION_FILE = os.path.join(base_dir, '../data/calibration.json')

global ser
#ser = connect_to_arduino()

DATA_PATH = '../data/tanks.json'

class TankManager:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=9600):
        self.serial_conn = connect_to_arduino()
        time.sleep(2)
        self.tanks = self.load_tanks()

    def load_tanks(self):
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, 'r') as file:
                return json.load(file)
        return {}

    def save_tanks(self):
        with open(DATA_PATH, 'w') as file:
            json.dump(self.tanks, file, indent=4)

    def create_tank(self):
        name = input("Enter tank name: ")
        code = input("Enter Arduino code (L1, L2, L3): ")
        total_volume = float(input("Enter total volume in liters: "))
        full_cm = float(input("Enter sensor value (cm) for 100% fill: "))
        
        self.tanks[name] = {
            'arduino_code': code,
            'total_volume': total_volume,
            'full_cm': full_cm
        }
        self.save_tanks()
        print(f"Tank '{name}' added successfully!")

    def test_tanks(self):
        for name, info in self.tanks.items():
            self.serial_conn.write(info['arduino_code'].encode())
            time.sleep(0.5)
            if self.serial_conn.in_waiting:
                distance = float(self.serial_conn.readline().decode().strip())
                fill_percentage = max(0, min(100, ((info['full_cm'] - distance) / info['full_cm']) * 100))
                current_volume = (fill_percentage / 100) * info['total_volume']
                print(f"{name}: {current_volume:.2f}L ({fill_percentage:.2f}% full)")
            else:
                print(f"No response from {name} sensor.")

if __name__ == "__main__":
    mode = input("Select mode: [1] Create Tank [2] Test Tanks: ")
    manager = TankManager()
    if mode == '1':
        manager.create_tank()
    elif mode == '2':
        manager.test_tanks()
    else:
        print("Invalid mode selected.")
