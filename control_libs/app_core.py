import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
base_dir = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE_PATH = 'data/app_config.json'
CALIBRATION_FILE = os.path.join(base_dir, '../data/calibration.json')



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
