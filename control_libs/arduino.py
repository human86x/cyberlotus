import serial
import time
from serial.tools import list_ports
from control_libs.system_stats import system_state, save_system_state, load_system_state
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

def connect_to_wemos():
    global power_ser
    try:
        power_ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
        time.sleep(2)  # Wait for Arduino to reset
        power_ser.write(b'PING\r\n')  # Test command
        response = power_ser.readline().decode().strip()
        print("Response from Wemos:", response)
        return power_ser
    except Exception as e:
        print("Error:", e)
        return None


#def connect_to_wemos():
#    global power_ser
    
    
    
    
    
    
 #   try:
  #      power_ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
        #time.sleep(2)  # Wait for Arduino to reset
        #if state == "ON":
        #    power_ser.write(b'PU\r\n')  # Test command
        #    response = power_ser.readline().decode().strip()
   #     print("Wemos Connected....")
        #    return response
        #else if "OFF":
        #    power_ser.write(b'PD\r\n')  # Test command
        #    response = power_ser.readline().decode().strip()
        #    print("Response from Wemos after POWERING DOWN:", response)
    #    return power_ser
    #except Exception as e:
    #    print("Error connecting to Wemos:", e)
    #    return None


def hard_reset_arduino(power_ser):

    power_ser.write(b'RE\r\n')  # Test command
    response = power_ser.readline().decode().strip()
    print("Response from Wemos after the reset:", response)



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

                print(f"[INFO] Sent command: {command}, waiting for response...")
                ser.write(command.encode())
                
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        print(f"[INFO] Received response: {response}")

                        # Changed from == to in to check for partial match
                        if expected_response in response:
                            print(f"[SUCCESS] Arduino confirmed action: {response}")
                            system_state["relay_states"]["relay_" + pump_name]["state"] = f"{'ON' if state == 'o' else 'OFF'}"
                            system_state["relay_states"]["relay_" + pump_name]["timestamp"] = cur_time
                            return True  # Exit after successful confirmation
                        else:
                            #break  # Exit the inner loop to retry
                            print(f"[WARNING] Unexpected response: {response}")
                            ser.flush()  # Flush output buffer
                            ser.reset_input_buffer()  # Flush input buffer

                                # Reset Arduino via DTR
                            print(f"##################Reseting Arduino#####################: {response}")
                            
                            ser.dtr = True  # Set DTR line to reset Arduino
                            time.sleep(0.1)  # Short delay to ensure reset
                            ser.dtr = False  # Release DTR line
                            time.sleep(2)  # Give Arduino time to reboot

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
    global power_ser
    ser = get_serial_connection()
    """Safely send the emergency stop command to Arduino with verification."""
    max_retries = 3  # Number of retry attempts
    attempt = 0

    while attempt < max_retries:
        try:
            if ser and ser.is_open:
                #ser.write(b'X')
                hard_reset_arduino(power_ser)
                ser.flush()
                print(f"[ALERT] 🚨 Emergency RESET using external relay - Attempt {attempt + 1}")

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


def send_command_and_get_response(ser, command, retries=10, timeout=1.3):
    attempt = 0
    global power_ser
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
    hard_reset_arduino(power_ser)
    return None