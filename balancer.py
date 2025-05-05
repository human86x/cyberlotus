import serial
import json
import time

# Paths for JSON files
sensor_data_file = "data/sensor_data.json"
goal_file = "data/desired_parameters.json"
flowrate_file = "data/flow_rates.json"
liquid_config_file = "data/liquid_config.json"

# Configure Serial communication for Arduino
arduino_port = '/dev/ttyACM0'  # Update to your actual port
arduino_baudrate = 9600
arduino_timeout = 2

arduino_serial = serial.Serial(
    port=arduino_port,
    baudrate=arduino_baudrate,
    timeout=arduino_timeout
)

def read_from_json(file_path):
    """Read data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            append_console_message(f"Data read from {file_path}: {data}")
            return data
    except FileNotFoundError:
        append_console_message(f"File not found: {file_path}")
        return {}

# Disable pH-related functions for now
# def calculate_ph_adjustment(current_ph, target_ph, tank_volume, acid_ph, base_ph, flowrate):
#     """
#     Calculate how long to run the pump to achieve the desired pH.
#     Returns pump_id and duration in seconds.
#     """
#     append_console_message(f"Calculating pH adjustment: current_ph={current_ph}, target_ph={target_ph}, "
#           f"tank_volume={tank_volume}, acid_ph={acid_ph}, base_ph={base_ph}, flowrate={flowrate}")
#     
#     delta_ph = target_ph - current_ph
# 
#     if delta_ph > 0:
#         # We need to increase pH (alkalize)
#         pump_id = 2  # Pump 2 is for base (pH+)
#         solution_ph = base_ph
#     elif delta_ph < 0:
#         # We need to decrease pH (acidify)
#         pump_id = 1  # Pump 1 is for acid (pH-)
#         solution_ph = acid_ph
#     else:
#         # No adjustment needed
#         append_console_message("No pH adjustment needed.")
#         return None, 0
# 
#     # Calculate the amount of rebalancing liquid needed (in liters)
#     required_adjustment = abs(delta_ph) / abs(solution_ph - current_ph)
#     liquid_volume_liters = required_adjustment * tank_volume
# 
#     # Convert volume to seconds of pump operation
#     duration_seconds = liquid_volume_liters * 1000 / flowrate
#     append_console_message(f"Calculated adjustment: pump_id={pump_id}, duration_seconds={duration_seconds}")
#     
#     return pump_id, duration_seconds

# Disable pH adjustment call in adjust_ph
# def adjust_ph(sensor_data, goal_data, flowrate_data, liquid_config):
#     """Adjust the pH to the desired level."""
#     current_ph = sensor_data.get("pH")
#     target_ph = goal_data.get("pH")
#     tank_volume = liquid_config.get("tank", {}).get("volume")
#     acid_ph = liquid_config.get("ph_minus", {}).get("concentration")
#     base_ph = liquid_config.get("ph_plus", {}).get("concentration")
# 
#     append_console_message(f"Adjusting pH: current_ph={current_ph}, target_ph={target_ph}, "
#           f"tank_volume={tank_volume}, acid_ph={acid_ph}, base_ph={base_ph}")
#     
#     if None in (current_ph, target_ph, tank_volume, acid_ph, base_ph):
#         append_console_message("Missing pH or tank configuration data.")
#         return
# 
#     # Get flowrate for pumps
#     pump1_flowrate = flowrate_data.get("pump1", 0)
#     pump2_flowrate = flowrate_data.get("pump2", 0)
# 
#     append_console_message(f"Flow rates: pump1={pump1_flowrate}, pump2={pump2_flowrate}")
# 
#     # Calculate pH adjustment
#     pump_id, duration = calculate_ph_adjustment(
#         current_ph, target_ph, tank_volume, acid_ph, base_ph,
#         pump1_flowrate if target_ph < current_ph else pump2_flowrate
#     )
# 
#     if pump_id and duration > 0:
#         # Send command to Arduino to activate the correct pump
#         command = f"{'a' if pump_id == 1 else 'b'}:{duration:.2f}"  # Send pump control command
#         arduino_serial.write(command.encode())
#         append_console_message(f"Sent command to Arduino: {command}")
#     else:
#         append_console_message("pH is already balanced.")

def adjust_temperature(sensor_data, goal_data):
    """Adjust the temperature to the desired level."""
    current_temp = sensor_data.get("temperature")
    target_temp = goal_data.get("temperature")

    append_console_message(f"Adjusting temperature: current_temp={current_temp}, target_temp={target_temp}")

    if None in (current_temp, target_temp):
        append_console_message("Missing temperature data.")
        return

    if current_temp < target_temp:
        # Activate heater (Pump 3)
        arduino_serial.write(b"do")  # Heater on (Pin 3)
        append_console_message("Heater activated.")
    else:
        # Turn off heater
        arduino_serial.write(b"df")  # Heater off (Pin 3)
        append_console_message("Heater deactivated.")

def main():
    while True:
        # Load data from JSON files
        append_console_message("Loading JSON files...")
        sensor_data = read_from_json(sensor_data_file)
        goal_data = read_from_json(goal_file)
        flowrate_data = read_from_json(flowrate_file)
        liquid_config = read_from_json(liquid_config_file)

        if not sensor_data or not goal_data:
            append_console_message("Sensor or goal data is missing. Skipping this cycle.")
            time.sleep(5)
            continue

        # Adjust temperature (pH adjustments are disabled for now)
        append_console_message("Adjusting temperature...")
        adjust_temperature(sensor_data, goal_data)

        # Wait before the next adjustment cycle
        append_console_message("Waiting before next adjustment cycle...")
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        append_console_message("\nBalancer stopped by user.")
    finally:
        arduino_serial.close()
