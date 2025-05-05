import sys
import os
import json
from control_libs.system_stats import append_console_message
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
base_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE_PATH = 'data/app_config.json'
CALIBRATION_FILE = os.path.join(base_dir, '../data/calibration.json')
SEQUENCE_DIR = "sequences/"

SYSTEM_STATE_FILE = "data/system_state.json"


def save_config(key, value):
    # Define the path to the calibration JSON file
    calibration_file = 'data/app_config.json'

    # Ensure the directory exists
    os.makedirs(os.path.dirname(calibration_file), exist_ok=True)

    # Load the current calibration data if it exists, otherwise create an empty dictionary
    if os.path.exists(calibration_file):
        with open(calibration_file, 'r') as file:
            calibration_data = json.load(file)
    else:
        calibration_data = {}

    # Update the EC_baseline value
    calibration_data[key] = value

    # Save the updated calibration data back to the JSON file
    with open(calibration_file, 'w') as file:
        json.dump(calibration_data, file, indent=4)

    append_console_message(f"App configuration has been updated:{key} = {value} in {calibration_file}")





def load_config(key=None):
    """
    Load the application configuration from the JSON file.
    
    Args:
        key (str, optional): The specific key to retrieve. If None, returns the entire configuration.

    Returns:
        dict or any: The full configuration if key is None, or the specific setting value.
    Raises:
        KeyError: If the specified key is not found in the configuration.
        Exception: If the file cannot be read or parsed.
    """
    try:
        with open(CONFIG_FILE_PATH, 'r') as config_file:
            config = json.load(config_file)

        if key:
            if key in config:
                return config[key]
            else:
                raise KeyError(f"Key '{key}' not found in the configuration.")
        return config
    except Exception as e:
        raise e
