import serial
import time
from serial.tools import list_ports
from control_libs.system_stats import system_state, save_system_state, load_system_state
#i#mport SerialException
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from control_libs.arduino import connect_to_arduino, send_command_and_get_response

#from config_tools.flow_tune import PUMP_COMMANDS

ser = None  # Define the global variable for the serial connection

#def connect_to_arduino():
#    global ser  # Access the global serial connection variable
#    """
#    Ensures only one connection is created and reused.
#    Reconnects if the connection is lost or invalid.
#    """
#    print("Checking Arduino connection...")#
#
#    # Check if a valid connection already exists
#    if ser and ser.is_open:
#        print(f"Arduino is already connected on {ser.port}.")
#        ser.close()  # Close the connection
#        print(f"Connection Closed {ser.port}.")
#        print(f"Reconnecting to {ser.port}...")
#        ser = serial.Serial(ser.port, baudrate=9600, timeout=1)  # Set a 1-second timeout
#        time.sleep(2)  # Allow time for Arduino to reset
#        print(f"Reconnected to {ser.port}")
#        return ser
#
#    # Try to establish a new connection
#    for i in range(11):  # Check ports /dev/ttyACM0 to /dev/ttyACM10
#        port = f"/dev/ttyACM{i}"
#        try:
#            print(f"Trying to connect to {port}...")
#            ser = serial.Serial(port, baudrate=9600, timeout=1)  # Set a 1-second timeout
#            time.sleep(2)  # Allow time for Arduino to reset
#            print(f"Connected successfully to {port}")
#            return ser
#        except serial.SerialException as e:
#            print(f"Failed to connect to {port}: {e}")
#            continue#
#
#    # Raise an exception if no ports work
#    raise Exception("Unable to connect to Arduino on any /dev/ttyACM* port.")



def connect_to_arduino():
    global ser
    try:
        ser = serial.Serial('/dev/arduino_mega', 9600, timeout=2)
        time.sleep(2)  # Wait for Arduino to reset
        ser.write(b'PING\r\n')  # Test command
        response = ser.readline().decode().strip()
        print("Response from Arduino:", response)
        return ser
    except Exception as e:
        print("Error:", e)
        return None





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
            print(f"DEBUG: Response -> {response}")
            return response in ('PONG', 'ARDUINO_READY')  # Accept both responses
        except Exception as e:
            print(f"DEBUG: Error testing connection -> {e}")
            return False


    # Try connecting via symlink only
    try:
        print(f"DEBUG: Trying symlink {SYMLINK}")
        ser = serial.Serial(SYMLINK, baudrate=9600, timeout=1)
        time.sleep(2)
        if test_connection(ser):
            print(f"✓ Connected via symlink {SYMLINK}")
            return ser
        ser.close()
    except serial.SerialException as e:
        print(f"⚠ Symlink connection failed: {e}")

    raise Exception("Could not establish connection to Arduino Mega via symlink")

# Usage:
#try:
#    ser = connect_to_arduino()
#    print("Connection successful!")
#except Exception as e:
#    print(f"Connection failed: {e}")




    # Implement emergency procedures here
# Initialize connection
#try:
#    ser = connect_to_arduino()
#except Exception as e:
#    print(f"Critical error: {str(e)}")
#    # Implement emergency shutdown here



def get_serial_connection():
    global ser
    if ser and ser.is_open:
        return ser
    else:
        print("[ERROR] Serial connection is not established.")
        ser = connect_to_arduino()
        return ser

def close_serial_connection():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("[INFO] Serial connection closed.")

def safe_serial_write(pump_name, state, retries=5, timeout=2):
    """
    Enhanced serial communication with partial response matching and better error recovery
    
    Args:
        pump_name (str): Pump identifier (must exist in PUMP_COMMANDS)
        state (str): 'o' for ON, 'f' for OFF
        retries (int): Maximum retry attempts
        timeout (float): Seconds to wait for response per attempt
    """
    global ser, system_state
    
    def emergency_recovery():
        """Handle connection failures"""
        #nonlocal ser
        print("[EMERGENCY] Attempting recovery...")
        try:
            safe_serial_write_emergency()
            ser = get_serial_connection()  # Re-establish connection
            time.sleep(1)  # Allow for Arduino reset
        except Exception as e:
            print(f"[CRITICAL] Recovery failed: {str(e)}")

    # Validate inputs
    if pump_name not in PUMP_COMMANDS:
        print(f"[ERROR] Invalid pump name: {pump_name}")
        return False
        
    if state not in ('o', 'f'):
        print(f"[ERROR] Invalid state: {state} (must be 'o' or 'f')")
        return False

    command = f"{pump_name}{state}"
    expected_prefix = f"{'ON' if state == 'o' else 'OFF'}_{pump_name}"
    full_expected = f"{expected_prefix}\r\n"  # Arduino typically sends CRLF
    
    attempt = 0
    while attempt <= retries:
        try:
            # Ensure connection exists
            if not ser or not ser.is_open:
                ser = get_serial_connection()
                if not ser:
                    raise serial.SerialException("No serial connection")
            
            # Clear buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # Send command
            print(f"[CMD] Sending: {command} (Attempt {attempt+1}/{retries})")
            ser.write(command.encode() + b'\n')  # Explicit newline
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < timeout:
                if ser.in_waiting:
                    response = ser.readline().decode().strip()
                    print(f"[RESP] Raw: {response}")
                    
                    # Check if expected string exists in response
                    if expected_prefix in response:
                        print(f"[SUCCESS] Valid response: {response}")
                        # Update system state
                        system_state["relay_states"][f"relay_{pump_name}"] = {
                            "state": "ON" if state == 'o' else "OFF",
                            "timestamp": int(time.time())
                        }
                        return True
                    
                    print(f"[WARNING] Unexpected response: {response}")
                    break  # Exit wait loop to retry
                
                time.sleep(0.05)  # Reduce CPU usage
            
            attempt += 1
            if attempt <= retries:
                print(f"[RETRY] Will retry {command}...")
                time.sleep(0.5)  # Brief pause between retries
            
        except serial.SerialException as e:
            print(f"[ERROR] Serial failure: {str(e)}")
            emergency_recovery()
            attempt += 1
        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            emergency_recovery()
            return False
    
    print(f"[FAILED] Command {command} failed after {retries} retries")
    safe_serial_write_emergency()
    return False


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
            print(f"[ERROR] Invalid duration value: {duration}. Must be a positive integer.")
            return

        command = f"{pump_name}{duration}"  # Combine pump name and duration
        expected_response = f"ON_{pump_name}_for_{duration}ms"  # Adjust expected response
        attempt = 0

        while attempt <= retries:
            if ser and ser.is_open:
                #ser.flushOutput()
                time.sleep(0.1)  # Small delay to avoid CPU overuse

                ser.write(command.encode())
                
                print(f"[INFO] Sent precise delivery command: {command}, waiting for response...")
                time.sleep(duration / 1000)  # Small delay to avoid CPU overuse

                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        print(f"[INFO] Received response: {response}")

                        if response == expected_response:
                            print(f"[SUCCESS] Arduino confirmed action: {response}")
                            system_state["relay_states"]["relay_" + pump_name]["state"] = f"ON for {duration}ms"
                            system_state["relay_states"]["relay_" + pump_name]["timestamp"] = int(time.time())
                            return True # Exit after successful confirmation
                        else:
                            print(f"[WARNING] Unexpected response: {response}")

                    time.sleep(0.1)  # Small delay to avoid CPU overuse

                print(f"[ERROR] No valid response. Retrying... (Attempt {attempt + 1}/{retries})")
                attempt += 1
            else:
                print("[ERROR] Serial port is not open. Cannot send command.")
                return

        # After retries fail
        print("[ERROR] Failed to confirm precise delivery command after retries. Attempting emergency stop.")
        safe_serial_write_emergency()

    except serial.SerialException as e:  # Corrected line
        print(f"[ERROR] Serial write failed for {pump_name}: {e}")
        safe_serial_write_emergency()
    except Exception as e:
        print(f"[ERROR] Unexpected error while writing to serial: {e}")
        safe_serial_write_emergency()



def emergency_stop(pump_name):
    global ser
    ser = get_serial_connection()
    """Immediately stop the specified pump in case of error."""
    try:
        print(f"[EMERGENCY] Stopping {pump_name} immediately!")
        if ser and ser.is_open:
            ser.write(f"{pump_name}f".encode())
            ser.flush()
        else:
            print("[ERROR] Serial port is not open. Attempting reconnection...")
            connect_to_arduino()
            ser.write(f"{pump_name}f".encode())
    except Exception as e:
        print(f"[CRITICAL] Failed to stop {pump_name}: {e}")


# Usage example
#t#ry:
#    arduino = connect_arduino()
#    # Add code to interact with the Arduino
#    arduino.write(b"Hello Arduino!")
#    arduino.close()
#except Exception as e:
#    print(e)

#ser = arduino_connect()#serial.Serial(serial_port, baud_rate, timeout=1)
#time.sleep(2)  # Allow Arduino to initialize

# Function to send a command and handle "HEARTBEAT" responses

import time

def safe_serial_write_emergency():
    global ser
    ser = get_serial_connection()
    """Safely send the emergency stop command to Arduino with verification."""
    max_retries = 3  # Number of retry attempts
    attempt = 0

    while attempt < max_retries:
        try:
            if ser and ser.is_open:
                ser.write(b'X')
                ser.flush()
                print(f"[ALERT] 🚨 Emergency Stop command 'X' sent to Arduino. Attempt {attempt + 1}")

                # Wait for Arduino response
                response = ser.readline().decode().strip()
                print(f"[INFO] Arduino response: {response}")

                if response == "All pumps turned OFF":
                    print("[SUCCESS] ✅ Arduino confirmed: All pumps are OFF.")
                    return  # Exit function if successful
                else:
                    print("[WARNING] ⚠️ Unexpected response. Reconnecting and retrying...")

            else:
                print("[ERROR] Serial port is not open. Attempting to reconnect...")

            # Reconnect and retry
            connect_to_arduino()
            attempt += 1

        except serial.SerialException as e:
            print(f"[ERROR] Serial write failed during Emergency Stop: {e}. Reconnecting and retrying...")
            connect_to_arduino()
            attempt += 1

        except Exception as e:
            print(f"[ERROR] Unexpected error during Emergency Stop: {e}. Reconnecting and retrying...")
            connect_to_arduino()
            attempt += 1

    print("[FAILURE] ❌ Emergency Stop failed after multiple attempts. Manual intervention may be required.")







import time
import serial
from serial import SerialException


def send_command_and_get_response(ser, command, retries=5, timeout=1.3):
    attempt = 0
    
    while attempt < retries:
        # Ensure serial connection is open
        if ser is None or not ser.is_open:
            print("Serial port is not open, attempting to reconnect...")
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                print("Error: Unable to reconnect to Arduino.")
                return None
        
        try:
            # Clear the input and output buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            print(f"Send command and get response -> the command >>> {command}")

            # Send the command to the Arduino
            ser.write(command)  # No need to encode if command is already bytes
            print(f"Successfully communicated command - {command}")

            # Wait for the Arduino to process the command
            time.sleep(timeout)

            # Read response from Arduino
            line = ser.readline().decode('utf-8').strip()
            print(f"Send command and get response -> the response >>> {line}")

            # Check if response is a valid float
            try:
                value = float(line)
                print(f"******VALUE = {value}")
                return value  # Valid response, return the float
            except ValueError:
                print(f"Error: Invalid response: {line}, not a valid float")

        except SerialException as e:
            print(f"Serial I/O error: {e}")
            print("Attempting to reconnect to Arduino...")
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                print("Error: Unable to reconnect to Arduino.")
                return None

        except Exception as e:
            print(f"Unexpected error: {e}")
            print("Attempting to reconnect to Arduino...")
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                print("Error: Unable to reconnect to Arduino.")
                return None
            

        attempt += 1
        time.sleep(timeout)  # Retry delay
    
    print(f"Error: No valid response after {retries} retries for command {command.decode('utf-8')}")
    return None