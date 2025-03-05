import json
import os
import time
from control_libs.arduino import get_serial_connection, close_serial_connection, connect_to_arduino, send_command_and_get_response
from control_libs.system_stats import system_state
from config_tools.flow_tune import test_pump_with_progress
from flask import jsonify


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


def adjust_tank_level(tank_name):
    global PUMP_COMMANDS
    print(f"Adjusting tank level for {tank_name}...")

    try:
        # Load configuration from app_config.json
        with open('data/app_config.json', 'r') as file:
            app_config = json.load(file)
        
        # Retrieve the pumps to be used for fill or drain actions
        fill_pump = app_config.get('fill_pump', 'fresh_solution')
        drain_pump = app_config.get('drain_pump', 'solution_waste')
        solution_level = float(app_config.get('solution_level', 50))  # Default 50 if not found
        
        # Fetch the tank levels from `tank_manager.py`
        tank_results = test_tanks()  # This function will give you the current levels
        print(f"Tank data fetched****{tank_results}")
        
        # Get the data for the specific tank
        tank_data = load_tanks()
        
        if not tank_data:
            print(f"Tank {tank_name} not found in the results.")
            return jsonify({"status": "error", "message": f"Tank {tank_name} not found"}), 400

        current_volume = tank_results[tank_name]['current_volume']
        total_volume = tank_data[tank_name]['total_volume']

        # Calculate the volume to add or drain
        stored_volume = (solution_level / 100) * total_volume
        volume_difference = current_volume - stored_volume
        print(f"Volume Difference {volume_difference}...")
        if volume_difference > 0:
            # Need to drain liquid
            print(f"Draining {volume_difference:.2f} L of solution from {tank_name}.")
            weight_to_drain = volume_difference * 1000  # Convert to weight (multiply by 100)
            print(f"Weight to drain {weight_to_drain}...")
            test_pump_with_progress(drain_pump, weight_to_drain)
        elif volume_difference < 0:
            # Need to add liquid
            print(f"Adding {-volume_difference:.2f} L of solution to {tank_name}.")
            weight_to_add = -volume_difference * 1000  # Convert to weight (multiply by 100)
            print(f"Weight_to_add {weight_to_add}...")
            test_pump_with_progress(fill_pump, weight_to_add)
        else:
            print(f"Tank {tank_name} is already at the correct level.")

        return jsonify({"status": "success", "message": f"Tank {tank_name} adjusted successfully"})

    except Exception as e:
        print(f"Error adjusting tank level: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


