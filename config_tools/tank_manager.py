import json
import os
import time
from control_libs.arduino import connect_to_arduino, send_command_and_get_response

base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(base_dir, '../data/tanks.json')

def load_tanks():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r') as file:
            return json.load(file)
    return {}

def save_tanks(tanks):
    with open(DATA_PATH, 'w') as file:
        json.dump(tanks, file, indent=4)

def add_tank(name, code, total_volume, full_cm, empty_cm):
    tanks = load_tanks()
    tanks[name] = {
        'arduino_code': code,
        'total_volume': total_volume,
        'full_cm': full_cm,
        'empty_cm': empty_cm
    }
    save_tanks(tanks)

def test_tanks():
    global ser 
    results = {}
    tanks = load_tanks()
    serial_conn = ser#connect_to_arduino()
    time.sleep(2)

    for name, info in tanks.items():
        send_command_and_get_response(serial_conn, info['arduino_code'])
        time.sleep(0.5)
        if serial_conn.in_waiting:
            response = serial_conn.readline().decode().strip()
            try:
                distance = float(response)
                fill_percentage = max(0, min(100, ((info['empty_cm'] - distance) /
                                  (info['empty_cm'] - info['full_cm'])) * 100))
                current_volume = (fill_percentage / 100) * info['total_volume']
                results[name] = {
                    'distance': distance,
                    'fill_percentage': round(fill_percentage, 2),
                    'current_volume': round(current_volume, 2)
                }
            except ValueError:
                results[name] = {'error': f"Invalid sensor response: {response}"}
        else:
            results[name] = {'error': "No response from sensor."}
    return results
