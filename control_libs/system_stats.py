import json
import os
from control_libs.app_core import SYSTEM_STATE_FILE
global system_state
system_state = {
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

    "target_NPK": {"value": None, "timestamp": None},
    "target_pH": {"value": None, "timestamp": None},
    "target_temp": {"value": None, "timestamp": None},
    "target_solution": {"value": None, "timestamp": None},

    
    "solution_tank": {"value": None, "timestamp": None},
    "fresh_tank": {"value": None, "timestamp": None},
    "waste_tank": {"value": None, "timestamp": None},
    "sensor_chamber": {"value": None, "timestamp": None},
    
    
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
    print(f"Loading sys_state from file name:{SYSTEM_STATE_FILE}")
    if not os.path.exists(SYSTEM_STATE_FILE):
        print(f"Path does not exist")
        return None  # Indicate that no previous state exists
    #load_ec_baseline()    
    with open(SYSTEM_STATE_FILE, "r") as f:
        x = json.load(f)
        system_state = x
        print(f"Loaded data:{x}")
        return x


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
    
    print(f"Logged {data_type}: {value}")

# Example usage
#history_log("ec", 1.23)
#history_log("ph", 7.1)
#history_log("temperature", 25.4)




# Example Usage
# save_system_state(system_state)
# loaded_state = load_system_state()
