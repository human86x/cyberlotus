import json
import os
import time
from control_libs.arduino import send_command_and_get_response, connect_to_arduino

# Use absolute path for data file
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(base_dir, 'data/tanks.json')

def load_tanks():
    """Load tanks data from JSON file."""
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r') as file:
            print("[DEBUG] Loaded existing tank data.")
            return json.load(file)
    print("[DEBUG] No existing tank data found. Starting fresh.")
    return {}

def save_tanks(tanks):
    """Save tanks data to JSON file."""
    with open(DATA_PATH, 'w') as file:
        json.dump(tanks, file, indent=4)
    print("[DEBUG] Saved tank data.")

def create_tank(tanks, name, code, total_volume, full_cm, empty_cm):
    """Create a new tank and save to JSON."""
    tanks[name] = {
        'arduino_code': code,
        'total_volume': total_volume,
        'full_cm': full_cm,
        'empty_cm': empty_cm
    }
    save_tanks(tanks)
    print(f"[DEBUG] Tank '{name}' added with code {code}, volume {total_volume}L, full at {full_cm} cm, empty at {empty_cm} cm.")

def test_tanks(tanks, serial_conn):
    """Test tanks by reading sensor data and calculating fill percentage."""
    test_results = {}
    print(f"************TANKS LOADED - {tanks}")
    for name, info in tanks.items():
        try:
            # Debugging: Log the start of the process
            print(f"[DEBUG] Sending code {info['arduino_code']} to Arduino for {name}...")
            
            # Send the command and wait for a response
            response = send_command_and_get_response(serial_conn, info['arduino_code'])
            
            # Attempt to parse the response as a float
            distance = float(response.strip())  # Strip any extra whitespace or newline characters
            
            print(f"[DEBUG] Distance received for {name}: {distance}")
            
            # Calculate fill percentage
            fill_percentage = max(0, min(100, ((info['empty_cm'] - distance) / 
                                              (info['empty_cm'] - info['full_cm'])) * 100))
            current_volume = (fill_percentage / 100) * info['total_volume']
            
            # Store results
            test_results[name] = {
                'distance': distance,
                'fill_percentage': round(fill_percentage, 2),
                'current_volume': round(current_volume, 2)
            }
        
        except ValueError as e:
            # Handle case where the response is not a valid float
            print(f"[ERROR] Invalid response for {name}: {response}. Error: {e}")
            test_results[name] = {'error': f'Invalid response: {response}'}
        
        except Exception as e:
            # Handle any other unexpected errors
            print(f"[ERROR] An exception occurred for {name}: {e}")
            test_results[name] = {'error': str(e)}
    
    return test_results
