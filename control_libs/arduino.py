import serial
import time
from serial.tools import list_ports
from control_libs.system_stats import system_state, save_system_state, load_system_state
from control_libs.system_stats import append_console_message

#i#mport SerialException
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from control_libs.arduino import connect_to_arduino, send_command_and_get_response

#from config_tools.flow_tune import PUMP_COMMANDS

ser = None  # Define the global variable for the serial connection
power_ser = None
#def connect_to_arduino():
#    global ser  # Access the global serial connection variable
#    """
#    Ensures only one connection is created and reused.
#    Reconnects if the connection is lost or invalid.
#    """
#    append_console_message("Checking Arduino connection...")#
#
#    # Check if a valid connection already exists
#    if ser and ser.is_open:
#        append_console_message(f"Arduino is already connected on {ser.port}.")
#        ser.close()  # Close the connection
#        append_console_message(f"Connection Closed {ser.port}.")
#        append_console_message(f"Reconnecting to {ser.port}...")
#        ser = serial.Serial(ser.port, baudrate=9600, timeout=1)  # Set a 1-second timeout
#        time.sleep(2)  # Allow time for Arduino to reset
#        append_console_message(f"Reconnected to {ser.port}")
#        return ser
#
#    # Try to establish a new connection
#    for i in range(11):  # Check ports /dev/ttyACM0 to /dev/ttyACM10
#        port = f"/dev/ttyACM{i}"
#        try:
#            append_console_message(f"Trying to connect to {port}...")
#            ser = serial.Serial(port, baudrate=9600, timeout=1)  # Set a 1-second timeout
#            time.sleep(2)  # Allow time for Arduino to reset
#            append_console_message(f"Connected successfully to {port}")
#            return ser
#        except serial.SerialException as e:
#            append_console_message(f"Failed to connect to {port}: {e}")
#            continue#
#
#    # Raise an exception if no ports work
#    raise Exception("Unable to connect to Arduino on any /dev/ttyACM* port.")


import serial
import time
import glob

def find_serial_devices(device_type="arduino"):
    """Search for possible serial devices with device-specific filtering"""
    possible_ports = []
    append_console_message("Searching for Arduino and Wemos boards..")
    if device_type.lower() == "wemos":
        # Wemos only appears on USB ports
        possible_ports += glob.glob('/dev/ttyUSB[0-9]*')
        # For Windows
        possible_ports += glob.glob('COM[0-9]*')
    elif device_type.lower() == "arduino":
        # Arduino only appears on ACM ports
        possible_ports += glob.glob('/dev/ttyACM[0-9]*')
        # For some Arduino models on Windows
        possible_ports += glob.glob('COM[0-9]*')
    
    return possible_ports

def test_serial_connection(port, device_type="arduino"):
    """Test if a device is responding on the given port with exact response validation"""
    append_console_message("Testing the serial connection")
    try:
        with serial.Serial(port, 9600, timeout=2) as test_ser:
            time.sleep(2)  # Wait for device to reset
            test_ser.write(b'PING\r\n')
            response = test_ser.readline().decode().strip()
            
            # Device-specific validation
            if device_type.lower() == "wemos":
                if response == "&#!WEMOS PONG":  # Exact Wemos response
                    append_console_message(f"✓ Valid Wemos found at {port}")
                    append_console_message("✓ Wemos found.")
                    return test_ser
            elif device_type.lower() == "arduino":
                if response == "PONG" or "ARDUINO_READY":  # Exact Arduino response
                    append_console_message(f"✓ Valid Arduino found at {port}")
                     
                    append_console_message("✓ Arduino found.")
                    ser = test_ser
                    return ser
                    
    except (serial.SerialException, OSError) as e:
        pass  # Silently handle failures
    return None

def connect_to_arduino():
    global ser
    # Try default port first
    default_port = '/dev/arduino_mega'
    append_console_message("Connecting to Arduino...")
    try:
        ser = serial.Serial(default_port, 9600, timeout=2)
        time.sleep(2)
        ser.write(b'PING\r\n')
        response = ser.readline().decode().strip()
        append_console_message(f"############    response - {response}")
        if response == "PONG" or "ARDUINO_READY":
            append_console_message(f"Connected to Arduino at default {default_port}")
            append_console_message("✓ Connected to Arduino.")
            return ser
        ser.close()
    except Exception as e:
        append_console_message(f"Default Arduino port {default_port} not available")
    
    # Search only ACM ports for Arduino
    possible_ports = find_serial_devices("arduino")
    for port in possible_ports:
        ser = test_serial_connection(port, "arduino")
        if ser:
            return ser
    
    append_console_message("× Error: No Arduino found on any ACM port")
    return None

def connect_to_wemos():
    global power_ser
    max_attempts = 3
    append_console_message("Connecting to Wemos...")
    
    for attempt in range(max_attempts):
        try:
            # Try default port first
            default_port = '/dev/ttyUSB0'
            power_ser = serial.Serial(default_port, 9600, timeout=2)
            time.sleep(2)  # Allow time for initialization
            
            # Test connection
            power_ser.write(b'PING\r\n')
            response = power_ser.readline().decode().strip()
            
            if response == "&#!WEMOS PONG":
                append_console_message(f"✓ Connected to Wemos on {default_port} (Attempt {attempt + 1})")
                return power_ser
                
            power_ser.close()
        except Exception as e:
            append_console_message(f"Attempt {attempt + 1} failed: {str(e)}")
        
        # If default port failed, search USB ports
        possible_ports = find_serial_devices("wemos")
        for port in possible_ports:
            try:
                power_ser = serial.Serial(port, 9600, timeout=2)
                time.sleep(2)
                power_ser.write(b'PING\r\n')
                response = power_ser.readline().decode().strip()
                
                if response == "&#!WEMOS PONG":
                    append_console_message(f"✓ Connected to Wemos on {port} (Attempt {attempt + 1})")
                    return power_ser
                    
                power_ser.close()
            except Exception as e:
                append_console_message(f"Failed on port {port}: {str(e)}")
        
        if attempt < max_attempts - 1:
            time.sleep(1)  # Wait before retrying
    
    append_console_message("× Error: Failed to connect to Wemos after multiple attempts", "error")
    return None
#def connect_to_wemos():
#    global power_ser
    
    
    
    
    
    
 #   try:
  #      power_ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
        #time.sleep(2)  # Wait for Arduino to reset
        #if state == "ON":
        #    power_ser.write(b'PU\r\n')  # Test command
        #    response = power_ser.readline().decode().strip()
   #     append_console_message("Wemos Connected....")
        #    return response
        #else if "OFF":
        #    power_ser.write(b'PD\r\n')  # Test command
        #    response = power_ser.readline().decode().strip()
        #    append_console_message("Response from Wemos after POWERING DOWN:", response)
    #    return power_ser
    #except Exception as e:
    #    append_console_message("Error connecting to Wemos:", e)
    #    return None


def hard_reset_arduino():
    global power_ser
    try:
        # Ensure we have a connection
        if power_ser is None:
            power_ser = connect_to_wemos()
            if power_ser is None:
                append_console_message("Cannot reset - no Wemos connection", "error")
                return False
                
        # Send reset command
        power_ser.write(b'RE\r\n')
        response = power_ser.readline().decode().strip()
        append_console_message(f"Wemos reset response: {response}")
        return True
        
    except Exception as e:
        append_console_message(f"Reset failed: {str(e)}", "error")
        power_ser = None  # Force reconnect on next attempt
        return False



def construction_connect_to_arduino():
    """
    Connect to Arduino Mega 2560 using a symlink.
    """
    SYMLINK = "/dev/arduino_mega"

    def test_connection(port):
        try:
            port.write(b'PING\n')
            time.sleep(1)
            response = port.readline().decode().strip()
            append_console_message(f"DEBUG: Response -> {response}")
            return response in ('PONG', 'ARDUINO_READY')  # Accept both responses
        except Exception as e:
            append_console_message(f"DEBUG: Error testing connection -> {e}")
            return False


    # Try connecting via symlink only
    try:
        append_console_message(f"DEBUG: Trying symlink {SYMLINK}")
        ser = serial.Serial(SYMLINK, baudrate=9600, timeout=1)
        time.sleep(2)
        if test_connection(ser):
            append_console_message(f"✓ Connected via symlink {SYMLINK}")
            return ser
        ser.close()
    except serial.SerialException as e:
        append_console_message(f"⚠ Symlink connection failed: {e}")

    raise Exception("Could not establish connection to Arduino Mega via symlink")

# Usage:
#try:
#    ser = connect_to_arduino()
#    append_console_message("Connection successful!")
#except Exception as e:
#    append_console_message(f"Connection failed: {e}")




    # Implement emergency procedures here
# Initialize connection
#try:
#    ser = connect_to_arduino()
#except Exception as e:
#    append_console_message(f"Critical error: {str(e)}")
#    # Implement emergency shutdown here



def get_serial_connection():
    global ser
    if ser and ser.is_open:
        return ser
    else:
        append_console_message("[ERROR] Serial connection is not established.")
        ser = connect_to_arduino()
        return ser

def get_wemos_connection():
    global power_ser
    if power_ser and power_ser.is_open:
        return power_ser
    else:
        append_console_message("[ERROR] Serial connection is not established.")
        power_ser = connect_to_wemos()
        return power_ser

def close_serial_connection():
    global ser
    if ser and ser.is_open:
        ser.close()
        append_console_message("[INFO] Serial connection closed.")

def safe_serial_write(pump_name, state, retries=5, timeout=2):
    global ser
    global system_state
    ser = get_serial_connection()

    """
    Safely write a pump control command to the serial port and verify Arduino response.
    Now checks if expected response is contained in the received response.

    Args:
        pump_name (str): Name of the pump.
        state (str): 'o' to turn ON, 'f' to turn OFF.
        retries (int): Number of retries if no valid response is received.
        timeout (int): Time in seconds to wait for Arduino response.
    """
    try:
        command = pump_name + state
        expected_response = f"{'ON' if state == 'o' else 'OFF'}_{pump_name}"
        
        attempt = 0
        cur_time = int(time.time())

        while attempt <= retries:
            if ser and ser.is_open:
                # Flush serial buffers to avoid leftover data
                ser.flushInput()  # Clears the input buffer
                ser.flushOutput()  # Clears the output buffer

                append_console_message(f"[INFO] Sent command: {command}, waiting for response...")
                ser.write(command.encode())
                time.sleep(1)  # Small delay to avoid CPU overuse

                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        append_console_message(f"[INFO] Received response: {response}")

                        # Changed from == to in to check for partial match
                        if expected_response in response:
                            append_console_message(f"[SUCCESS] Arduino confirmed action: {response}")
                            system_state["relay_states"]["relay_" + pump_name]["state"] = f"{'ON' if state == 'o' else 'OFF'}"
                            system_state["relay_states"]["relay_" + pump_name]["timestamp"] = cur_time
                            
                            append_console_message(f"system_state[\relay_states/][relay_ + {pump_name}][state] = {state}")
                            
                            
                            return True  # Exit after successful confirmation
                        else:
                            #break  # Exit the inner loop to retry
                            append_console_message(f"[WARNING] Unexpected response: {response}")
                            ser.flush()  # Flush output buffer
                            ser.reset_input_buffer()  # Flush input buffer

                                # Reset Arduino via DTR
                            append_console_message(f"##################Reseting Arduino#####################: {response}")
                            hard_reset_arduino()
                            #ser.dtr = True  # Set DTR line to reset Arduino
                            #time.sleep(0.1)  # Short delay to ensure reset
                            #ser.dtr = False  # Release DTR line
                            #time.sleep(2)  # Give Arduino time to reboot

                            break  # Exit the inner loop to retry

                    time.sleep(0.1)  # Small delay to avoid CPU overuse

                append_console_message(f"[ERROR] No valid response. Retrying... (Attempt {attempt + 1}/{retries})")
                attempt += 1
            else:
                append_console_message("[ERROR] Serial port is not open. Cannot send command.")
                return

        # After retries fail
        append_console_message("[ERROR] Failed to confirm command after retries. Attempting emergency stop.")
        safe_serial_write_emergency()

    except serial.SerialException as e:
        append_console_message(f"[ERROR] Serial write failed for {pump_name}: {e}")
        safe_serial_write_emergency()
    except Exception as e:
        append_console_message(f"[ERROR] Unexpected error while writing to serial: {e}")
        safe_serial_write_emergency()

def safe_serial_write_precise(pump_name, duration, retries=5, timeout=2):
    global ser
    global system_state
    ser = get_serial_connection()
    """
    Safely write a precise pump control command to the serial port and verify Arduino response.

    Args:
        pump_name (str): Name of the pump (must be in PUMP_COMMANDS).
        duration (int): Duration in milliseconds for which the pump should remain ON.
        retries (int): Number of retries if no valid response is received.
        timeout (int): Time in seconds to wait for Arduino response.
    """
    try:
        if not isinstance(duration, int) or duration <= 0:
            append_console_message(f"[ERROR] Invalid duration value: {duration}. Must be a positive integer.")
            return

        command = f"{pump_name}{duration}"  # Combine pump name and duration
        expected_response = f"ON_{pump_name}_for_{duration}ms"  # Adjust expected response
        attempt = 0

        while attempt <= retries:
            if ser and ser.is_open:
                #ser.flushOutput()
                time.sleep(0.1)  # Small delay to avoid CPU overuse

                ser.write(command.encode())
                
                append_console_message(f"[INFO] Sent precise delivery command: {command}, waiting for response...")
                time.sleep(duration / 1000)  # Small delay to avoid CPU overuse

                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        append_console_message(f"[INFO] Received response: {response}")

                        if response == expected_response:
                            append_console_message(f"[SUCCESS] Arduino confirmed action: {response}")
                            system_state["relay_states"]["relay_" + pump_name]["state"] = f"ON for {duration}ms"
                            system_state["relay_states"]["relay_" + pump_name]["timestamp"] = int(time.time())
                            return True # Exit after successful confirmation
                        else:
                            append_console_message(f"[WARNING] Unexpected response: {response}")

                    time.sleep(0.1)  # Small delay to avoid CPU overuse

                append_console_message(f"[ERROR] No valid response. Retrying... (Attempt {attempt + 1}/{retries})")
                attempt += 1
            else:
                append_console_message("[ERROR] Serial port is not open. Cannot send command.")
                return

        # After retries fail
        append_console_message("[ERROR] Failed to confirm precise delivery command after retries. Attempting emergency stop.")
        safe_serial_write_emergency()

    except serial.SerialException as e:  # Corrected line
        append_console_message(f"[ERROR] Serial write failed for {pump_name}: {e}")
        safe_serial_write_emergency()
    except Exception as e:
        append_console_message(f"[ERROR] Unexpected error while writing to serial: {e}")
        safe_serial_write_emergency()



def emergency_stop(pump_name):
    global ser
    ser = get_serial_connection()
    """Immediately stop the specified pump in case of error."""
    try:
        append_console_message(f"[EMERGENCY] Stopping {pump_name} immediately!")
        if ser and ser.is_open:
            ser.write(f"{pump_name}f".encode())
            ser.flush()
        else:
            append_console_message("[ERROR] Serial port is not open. Attempting reconnection...")
            connect_to_arduino()
            ser.write(f"{pump_name}f".encode())
    except Exception as e:
        append_console_message(f"[CRITICAL] Failed to stop {pump_name}: {e}")


# Usage example
#t#ry:
#    arduino = connect_arduino()
#    # Add code to interact with the Arduino
#    arduino.write(b"Hello Arduino!")
#    arduino.close()
#except Exception as e:
#    append_console_message(e)

#ser = arduino_connect()#serial.Serial(serial_port, baud_rate, timeout=1)
#time.sleep(2)  # Allow Arduino to initialize

# Function to send a command and handle "HEARTBEAT" responses

import time

def safe_serial_write_emergency():
    global ser
    global power_ser
    ser = get_serial_connection()
    """Safely send the emergency stop command to Arduino with verification."""
    max_retries = 3  # Number of retry attempts
    attempt = 0

    while attempt < max_retries:
        try:
            if ser and ser.is_open:
                #ser.write(b'X')
                hard_reset_arduino()
                ser.flush()
                append_console_message(f"[ALERT] 🚨 Emergency RESET using external relay - Attempt {attempt + 1}")

                # Wait for Arduino response
                response = ser.readline().decode().strip()
                append_console_message(f"[INFO] Arduino response: {response}")

                if response == "All pumps turned OFF":
                    append_console_message("[SUCCESS] ✅ Arduino confirmed: All pumps are OFF.")
                    return  # Exit function if successful
                else:
                    append_console_message("[WARNING] ⚠️ Unexpected response. Reconnecting and retrying...")

            else:
                append_console_message("[ERROR] Serial port is not open. Attempting to reconnect...")

            # Reconnect and retry
            connect_to_arduino()
            attempt += 1

        except serial.SerialException as e:
            append_console_message(f"[ERROR] Serial write failed during Emergency Stop: {e}. Reconnecting and retrying...")
            connect_to_arduino()
            attempt += 1

        except Exception as e:
            append_console_message(f"[ERROR] Unexpected error during Emergency Stop: {e}. Reconnecting and retrying...")
            connect_to_arduino()
            attempt += 1

    append_console_message("[FAILURE] ❌ Emergency Stop failed after multiple attempts. Manual intervention may be required.")







import time
import serial
from serial import SerialException


def send_command_and_get_response(ser, command, retries=1, timeout=2.3):
    attempt = 0
    global power_ser
    while attempt < retries:
        # Ensure serial connection is open
        if ser is None or not ser.is_open:
            append_console_message("Serial port is not open, attempting to reconnect...")
            append_console_message("Serial port is not open, attempting to reconnect")
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                append_console_message("Error: Unable to reconnect to Arduino.")
                append_console_message("Error Unable to connect.")
                return None
        
        try:
            # Clear the input and output buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            append_console_message(f"Send command and get response -> the command >>> {command}")
            append_console_message(f"Sending the command > {command}")

            # Send the command to the Arduino
            ser.write(command)  # No need to encode if command is already bytes
            append_console_message(f"Successfully communicated command - {command}")

            # Wait for the Arduino to process the command
            time.sleep(timeout)

            # Read response from Arduino
            line = ser.readline().decode('utf-8').strip()
            append_console_message(f"Send command and get response -> the response >>> {line}")
            append_console_message(f"Response: {line}")
            # Check if response is a valid float
            try:
                value = float(line)
                append_console_message(f"******VALUE = {value}")
                append_console_message("✓ Valid value.")
                return value  # Valid response, return the float
            except ValueError:
                append_console_message(f"Error: Invalid response: {line}, not a valid float")
                append_console_message("Error: Not a valid float!")

        except SerialException as e:
            append_console_message(f"Serial I/O error: {e}")
            append_console_message("Attempting to reconnect to Arduino...")
            append_console_message("Attempting to reconect to arduino")
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                append_console_message("Error: Unable to reconnect to Arduino.")
                append_console_message("Error: Unable to connect..")
                return None

        except Exception as e:
            append_console_message(f"Unexpected error: {e}")
            append_console_message("Attempting to reconnect to Arduino...")
            
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                append_console_message("Error: Unable to reconnect to Arduino.")
                return None
            

        attempt += 1
        time.sleep(timeout)  # Retry delay
    
    append_console_message(f"Error: No valid response after {retries} retries for command {command.decode('utf-8')}")
    #append_console_message("Error: No valid responses after " + retries + " for " + command)
    append_console_message(f"Error: No valid response after {retries} retries for command {command.decode('utf-8')}")
    
    power_ser = connect_to_wemos()
    hard_reset_arduino()
    return None