import serial
import time
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


import serial
import time
from serial.tools import list_ports

def connect_to_arduino():
    """
    Robust Arduino connection manager with:
    - Persistent port binding using udev symlinks
    - Watchdog recovery
    - USB reset fallback
    """
    global ser
    
    ARDUINO_ID = {
        'vid': '2341',  # Arduino's Vendor ID
        'pid': '0043'   # Common Arduino Uno PID
    }
    SYMLINK_PORT = "/dev/arduino_controller"  # udev symlink
    TEST_COMMAND = b'PING\n'
    EXPECTED_RESPONSE = "PONG"
    MAX_RETRIES = 3
    CONNECT_DELAY = 2  # Seconds

    def test_connection(port):
        try:
            port.write(TEST_COMMAND)
            response = port.readline().decode().strip()
            return response == EXPECTED_RESPONSE
        except:
            return False

    def reset_usb():
        """Try to physically reset the USB port"""
        try:
            from subprocess import run
            run(['sudo', 'usbreset', f"{ARDUINO_ID['vid']}:{ARDUINO_ID['pid']}"], 
                check=True)
            time.sleep(5)  # Allow for reboot
        except:
            print("USB reset failed (install 'usbreset')")

    # Case 1: Test existing connection
    if ser and ser.is_open:
        if test_connection(ser):
            print(f"✓ Active connection on {ser.port}")
            return ser
        else:
            print(f"✗ Connection lost on {ser.port}")
            ser.close()

    # Case 2: Try symlink first (udev persistent port)
    try:
        ser = serial.Serial(SYMLINK_PORT, baudrate=9600, timeout=1)
        time.sleep(CONNECT_DELAY)
        if test_connection(ser):
            print(f"✓ Connected via symlink {SYMLINK_PORT}")
            return ser
        ser.close()
    except Exception as e:
        print(f"Symlink connection failed: {str(e)}")

    # Case 3: Scan all ports
    print("Scanning ports...")
    for port_info in list_ports.comports():
        if (ARDUINO_ID['vid'] in port_info.hwid and 
            ARDUINO_ID['pid'] in port_info.hwid):
            
            for attempt in range(MAX_RETRIES):
                try:
                    ser = serial.Serial(port_info.device, 
                                      baudrate=9600, 
                                      timeout=1)
                    time.sleep(CONNECT_DELAY)
                    
                    if test_connection(ser):
                        print(f"✓ Connected to {port_info.device}")
                        return ser
                    else:
                        ser.close()
                except Exception as e:
                    print(f"Attempt {attempt+1} failed: {str(e)}")
                    time.sleep(1)

    # Case 4: Nuclear option - USB reset
    print("Attempting USB reset...")
    reset_usb()
    return connect_to_arduino()  # Recursive retry




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
    global ser
    global system_stats
    ser = get_serial_connection()

    """
    Safely write a pump control command to the serial port and verify Arduino response.

    Args:
        pump_name (str): Name of the pump (must be in PUMP_COMMANDS).
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

                print(f"[INFO] Sent command: {command}, waiting for response...")
                ser.write(command.encode())
                
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        print(f"[INFO] Received response: {response}")

                        if response == expected_response:
                            print(f"[SUCCESS] Arduino confirmed action: {response}")
                            system_state["relay_states"]["relay_" + pump_name]["state"] = f"{'ON' if state == 'o' else 'OFF'}"
                            system_state["relay_states"]["relay_" + pump_name]["timestamp"] = int(time.time())
                            return True# Exit after successful confirmation
                        else:
                            # Unexpected response: Flush buffers and retry
                            print(f"[WARNING] Unexpected response: {response}")
                            ser.flush()  # Flush output buffer
                            ser.reset_input_buffer()  # Flush input buffer
                            break  # Exit the inner loop to retry

                    time.sleep(0.1)  # Small delay to avoid CPU overuse

                print(f"[ERROR] No valid response. Retrying... (Attempt {attempt + 1}/{retries})")
                attempt += 1
            else:
                print("[ERROR] Serial port is not open. Cannot send command.")
                return

        # After retries fail
        print("[ERROR] Failed to confirm command after retries. Attempting emergency stop.")
        safe_serial_write_emergency()

    except serial.SerialException as e:
        print(f"[ERROR] Serial write failed for {pump_name}: {e}")
        safe_serial_write_emergency()
    except Exception as e:
        print(f"[ERROR] Unexpected error while writing to serial: {e}")
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