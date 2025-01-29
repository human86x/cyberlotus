import json
import os
import time
from control_libs.arduino import get_serial_connection, close_serial_connection, connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(base_dir, '../data/tanks.json')

def load_tanks():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r') as file:
            x = json.load(file)
            print(f"****LOADED DATA FROM  TANKS FILE {DATA_PATH} DATA= {x}")
            return x
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

# test_tanks():
#    #global ser 
#    results = {}
#    tanks = load_tanks()
#    global ser
#    ser = get_serial_connection()
#    serial_conn = ser#connect_to_arduino()
#    time.sleep(2)

#    for name, info in tanks.items():
        
#        command = info['arduino_code']
#        command = command.encode()
#        send_command_and_get_response(serial_conn, command)
#        time.sleep(0.5)
#        if serial_conn.in_waiting:
#            response = serial_conn.readline().decode().strip()
#            try:
#                distance = float(response)
#                fill_percentage = max(0, min(100, ((info['empty_cm'] - distance) /
#                                  (info['empty_cm'] - info['full_cm'])) * 100))
#                current_volume = (fill_percentage / 100) * info['total_volume']
#                
#                results[name] = {
#                    'distance': distance,
#                    'fill_percentage': round(fill_percentage, 2),
#                    'current_volume': round(current_volume, 2),
#                    'arduino_code': info['arduino_code'],
#                    'total_volume': info['total_volume'],
#                    'full_cm': info['full_cm'],
#                    'empty_cm': info['empty_cm']
#                    
#                }
#            except ValueError:
#                results[name] = {'error': f"Invalid sensor response: {response}"}
#        else:
#            results[name] = {'error': "No response from sensor."}
#    return results
def test_tanks(tanks = None, serial_conn = None):
    """Test tanks by reading sensor data and calculating fill percentage."""
    test_results = {}
    tanks = load_tanks()
    serial_conn = get_serial_connection()
    print(f"************TANKS LOADED - {tanks}")
    for name, info in tanks.items():
        try:
            # Debugging: Log the start of the process
            print(f"[DEBUG] Sending code {info['arduino_code']} to Arduino for {name}...")
            code = info['arduino_code']
            # Send the command and wait for a response
            code_bytes = code.encode()  # Converts 'L1' to b'L1'
            
            print(f"[DEBUG] Sending code {code_bytes} to Arduino for {name}...")
            
            response = send_command_and_get_response(serial_conn, code_bytes)
            print(f"***value recieved response={response}")
            # Attempt to parse the response as a float
            distance = float(response)#.strip()  # Strip any extra whitespace or newline characters
            
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
            print(f"******test results of the pump {name} - are : {test_results[name]}")
            print(f"########test_results[]:{test_results}")
            ############################################

            system_state[f"{name}_tank"]["value"] = test_results[name]["fill_percentage"]
            system_state[f"{name}_tank"]["timestamp"] = int(time.time())

            #system_state[f"solution_tank"]["value"] = response
            #system_state[f"solution_tank"]["timestamp"] = int(time.time())

            #system_state[f"waste_tank"]["value"] = response
            #system_state[f"waste_tank"]["timestamp"] = int(time.time())


            ############################################
        except ValueError as e:
            # Handle case where the response is not a valid float
            print(f"[ERROR] Invalid response for {name}: {response}. Error: {e}")
            test_results[name] = {'error': f'Invalid response: {response}'}
        
        except Exception as e:
            # Handle any other unexpected errors
            print(f"[ERROR] An exception occurred for {name}: {e}")
            test_results[name] = {'error': str(e)}
    
    return test_results
