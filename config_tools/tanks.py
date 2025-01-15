import json
import time
import os
import sys

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from control_libs.arduino import connect_to_arduino, send_command_and_get_response

# Use absolute path for data file
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(base_dir, '../data/tanks.json')

def load_tanks():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r') as file:
            print("[DEBUG] Loaded existing tank data.")
            temp = json.load(file)
            print(f"Loaded JSON - {temp} cm")
            return temp
            
            #return json.load(file)
    print("[DEBUG] No existing tank data found. Starting fresh.")
    return {}

def save_tanks(tanks):
    with open(DATA_PATH, 'w') as file:
        json.dump(tanks, file, indent=4)
    print("[DEBUG] Saved tank data.")

def create_tank(tanks):
    name = input("Enter tank name: ")
    code = input("Enter Arduino code (L1, L2, L3): ")
    total_volume = float(input("Enter total volume in liters: "))
    full_cm = float(input("Enter sensor value (cm) for 100% fill: "))
    
    tanks[name] = {
        'arduino_code': code,
        'total_volume': total_volume,
        'full_cm': full_cm
    }
    save_tanks(tanks)
    print(f"[DEBUG] Tank '{name}' added with code {code}, volume {total_volume}L, full at {full_cm} cm.")

def test_tanks(tanks, serial_conn):
    for name, info in tanks.items():
        print(f"[DEBUG] Sending code {info['arduino_code']} to Arduino for {name}...")
        send_command_and_get_response(serial_conn, info['arduino_code'])
        time.sleep(0.5)
        if serial_conn.in_waiting:
            response = serial_conn.readline().decode().strip()
            print(f"[DEBUG] Received response: {response}")
            try:
                distance = float(response)
                print(f"[DEBUG] Sensor distance for {name}: {distance} cm")
                fill_percentage = max(0, min(100, ((info['full_cm'] - distance) / info['full_cm']) * 100))
                print(f"[DEBUG] Fill percentage for {name}: {fill_percentage}%")
                current_volume = (fill_percentage / 100) * info['total_volume'] 
                print(f"[DEBUG] Current volume for {name}: {current_volume}L")
            except ValueError:
                print(f"[ERROR] Invalid response for {name}: {response}")
        else:
            print(f"[ERROR] No response from {name} sensor.")

if __name__ == "__main__":
    mode = input("Select mode: [1] Create Tank [2] Test Tanks: ")
    tanks = load_tanks()
    serial_conn = connect_to_arduino()
    time.sleep(2)

    if mode == '1':
        create_tank(tanks)
    elif mode == '2':
        test_tanks(tanks, serial_conn)
    else:
        print("[ERROR] Invalid mode selected.")


#print("[DEBUG] Loaded existing tank data.")
            
 #           temp = json.load(file)
 #           print(f"Loaded JSON - {temp} cm")
 #           return temp