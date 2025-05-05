import json
import os
from control_libs.app_core import SYSTEM_STATE_FILE
import time
#from control_libs.system_stats import append_console_message
global system_state
system_state = {

    "chamber_humidity": {"value": None, "timestamp": None},
    "chamber_temperature": {"value": None, "timestamp": None},
    "plant_temperature": {"value": None, "timestamp": None},

    "plant_chamber_target_humidity": {"value": None, "timestamp": None},
    "plant_chamber_target_temperature": {"value": None, "timestamp": None},
    "plant_pot_target_level": {"value": None, "timestamp": None},

    "ec": {"value": None, "timestamp": None},
    "ec_solution": {"value": None, "timestamp": None},
    "ec_calibration": {"value": None, "timestamp": None},
    "ec_baseline": {"value": None, "timestamp": None},
    "ppm":{"value": None, "timestamp": None},
    "ph": {"value": None, "timestamp": None},
    "ph_solution": {"value": None, "timestamp": None},
    "ph_baseline": {"value": None, "timestamp": None},
    "ph_calibration": {"value": None, "timestamp": None},
    "ph_calibration_LOW": {"value": None, "timestamp": None},
    "ph_calibration_HIGH": {"value": None, "timestamp": None},
    "ph_raw": {"value": None, "timestamp": None},

    "temperature": {"value": None, "timestamp": None},
    "solution_heater": {"value": None, "timestamp": None},
    "plant_pot_level": {"value": None, "timestamp": None},
    "target_NPK": {"value": None, "timestamp": None},
    "target_pH": {"value": None, "timestamp": None},
    "target_temp": {"value": None, "timestamp": None},
    "target_solution": {"value": None, "timestamp": None},

    
    "solution_tank": {"value": None, "timestamp": None},
    "fresh_tank": {"value": None, "timestamp": None},
    "waste_tank": {"value": None, "timestamp": None},
    "sensor_chamber": {"value": None, "timestamp": None},



    "air_heater": {"state": None, "timestamp": None},
    "water_heater": {"state": None, "timestamp": None},
    "air_humidifyer": {"state": None, "timestamp": None},

    "light_yellow": {"state": None, "timestamp": None},
    "light_white": {"state": None, "timestamp": None},
    "light_grow": {"state": None, "timestamp": None},
    "stop_all": {"state": None, "timestamp": None},
    #"console_output": {"state": None, "timestamp": None},
    "console_output": [],  # Change this to a list instead of dict
    "relay_states": {
        "relay_a": {"state": None, "timestamp": None},
        "relay_b": {"state": None, "timestamp": None},
        "relay_c": {"state": None, "timestamp": None},
        "relay_d": {"state": None, "timestamp": None},
        "relay_e": {"state": None, "timestamp": None},
        "relay_f": {"state": None, "timestamp": None},
        "relay_g": {"state": None, "timestamp": None},
        "relay_h": {"state": None, "timestamp": None},

        "relay_i": {"state": None, "timestamp": None},
        "relay_j": {"state": None, "timestamp": None},
        
        
        
        "relay_k": {"state": None, "timestamp": None},
        "relay_l": {"state": None, "timestamp": None},
        "relay_m": {"state": None, "timestamp": None},
        "relay_n": {"state": None, "timestamp": None},
        
        "relay_o": {"state": None, "timestamp": None},
        "relay_p": {"state": None, "timestamp": None},
        "relay_q": {"state": None, "timestamp": None},
        "relay_r": {"state": None, "timestamp": None},
        "relay_s": {"state": None, "timestamp": None},
        "relay_t": {"state": None, "timestamp": None},
        
        "relay_u": {"state": None, "timestamp": None},
        "relay_v": {"state": None, "timestamp": None},
        "relay_w": {"state": None, "timestamp": None},
        "relay_x": {"state": None, "timestamp": None},
        "relay_y": {"state": None, "timestamp": None},
        "relay_z": {"state": None, "timestamp": None},


         # // Add relay states for symbols
        "relay_!": {"state": None, "timestamp": None},
        "relay_@": {"state": None, "timestamp": None},
        "relay_#": {"state": None, "timestamp": None},
        "relay_$": {"state": None, "timestamp": None},
        "relay_%": {"state": None, "timestamp": None},
        "relay_^": {"state": None, "timestamp": None},
        "relay_&": {"state": None, "timestamp": None},
        "relay_*": {"state": None, "timestamp": None},
        "relay_(": {"state": None, "timestamp": None},
        "relay_)": {"state": None, "timestamp": None},
        "relay_-": {"state": None, "timestamp": None},
        "relay__": {"state": None, "timestamp": None}, # // Underscore
        "relay_=": {"state": None, "timestamp": None},
        "relay_+": {"state": None, "timestamp": None},
        "relay_[": {"state": None, "timestamp": None},
        "relay_]": {"state": None, "timestamp": None},
        "relay_{": {"state": None, "timestamp": None},
        "relay_}": {"state": None, "timestamp": None},
        "relay_;": {"state": None, "timestamp": None},
        "relay_:": {"state": None, "timestamp": None},
        "relay_,": {"state": None, "timestamp": None},
        "relay_.": {"state": None, "timestamp": None}
    }
}



def save_system_state(state):
    """Saves the system_state dictionary to a JSON file."""
    os.makedirs(os.path.dirname(SYSTEM_STATE_FILE), exist_ok=True)
    with open(SYSTEM_STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)



def load_system_state():
    global system_state
    """Loads the system_state dictionary from a JSON file. If the file does not exist, returns an empty default structure."""
    append_console_message(f"Loading sys_state from file name:{SYSTEM_STATE_FILE}")
    if not os.path.exists(SYSTEM_STATE_FILE):
        append_console_message(f"Path does not exist")
        return None  # Indicate that no previous state exists
    #load_ec_baseline()    
    with open(SYSTEM_STATE_FILE, "r") as f:
        x = json.load(f)
        #system_state = x
        update_dict(system_state, x)
        append_console_message(f"Loaded data:{system_state}")
        return x


def update_dict(original, new_data):
    """
    Recursively updates the original dictionary with new_data without deleting existing entries.
    """
    for key, value in new_data.items():
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            # If both original and new_data have nested dictionaries, recurse
            update_dict(original[key], value)
        else:
            # Update the value in the original dictionary
            original[key] = value
            # Add a timestamp for updated keys
            if isinstance(original[key], dict) and "value" in original[key]:
                original[key]["timestamp"] = int(time.time())




#import json
#import os
from datetime import datetime

def history_log(data_type, value, file_path="data/readings_log.json"):
    """
    Append a new sensor reading to the readings_log.json file.
    
    :param data_type: Type of data ("ec", "ph", "temperature")
    :param value: Sensor reading value
    :param file_path: Path to the JSON file
    """
    # Ensure the file exists
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump([], f)
    
    # Read existing data
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                data = []  # Reset if file content is corrupted
        except json.JSONDecodeError:
            data = []  # Reset if file is empty or invalid
    
    # Append new data
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        data_type: value
    }
    data.append(entry)
    
    # Keep only the last 100 entries to prevent excessive file size
    data = data[-100:]
    
    # Write back to file
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    
    append_console_message(f"Logged {data_type}: {value}")

# Example usage
#history_log("ec", 1.23)
#history_log("ph", 7.1)
#history_log("temperature", 25.4)

from threading import Lock



# Global system state with thread-safe console output
#system_state = {
#    "console_output": [],
    # ... your other system state variables ...
#}

# Lock for thread-safe console operations
console_lock = Lock()

def append_console_message(message):
    """Thread-safe function to add messages to console output"""
    print("Message from the console: ")
    print(message)
    timestamp = datetime.now().timestamp()
    with console_lock:
        # Keep only the last 100 messages to prevent memory issues
        if len(system_state["console_output"]) >= 100:
            system_state["console_output"].pop(0)
        system_state["console_output"].append({
            "message": message,
            "timestamp": timestamp
        })


# Example Usage
# save_system_state(system_state)
# loaded_state = load_system_state()
