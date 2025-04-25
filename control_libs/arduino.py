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





import serial
import time


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

def construction_connect_to_arduino():
    """
    Connect to Arduino Mega 2560, trying symlink first then common ports.
    """
    SYMLINK = "/dev/arduino_mega"
    COMMON_PORTS = [f"/dev/ttyACM{i}" for i in range(6)] + [f"/dev/ttyUSB{i}" for i in range(6)]

    test_connection()

    # Try connecting via symlink first
    try:
        print(f"DEBUG: Trying symlink {SYMLINK}")
        ser = serial.Serial(SYMLINK, baudrate=9600, timeout=1)
        time.sleep(2)  # Give time for Arduino to initialize
        if test_connection(ser):
            print(f"✓ Connected via symlink {SYMLINK}")
            return ser
        ser.close()
    except serial.SerialException as e:
        print(f"⚠ Symlink connection failed: {e}")

    # If symlink failed, try common ports
    for port in COMMON_PORTS:
        try:
            print(f"DEBUG: Trying port {port}")
            ser = serial.Serial(port, baudrate=9600, timeout=1)
            time.sleep(2)  # Give time for Arduino to initialize
            if test_connection(ser):
                print(f"✓ Connected via port {port}")
                return ser
            ser.close()
        except serial.SerialException as e:
            print(f"⚠ Connection failed on {port}: {e}")
            continue

    raise Exception("Could not establish connection to Arduino Mega on any port")


import subprocess





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
def get_arduino_connection(max_retries=3):
    for attempt in range(max_retries):
        try:
            ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            if test_connection(ser):  # Your existing test function
                return ser
            ser.close()
        except Exception:
            pass
            
        print(f"Connection failed, attempt {attempt+1}/{max_retries}")
        if not reset_arduino_usb():
            print("Physical replug required!")
            break
        time.sleep(5)
    
    raise Exception("Failed to reconnect to Arduino")


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
    ser = get_serial_connection()
    """Safely send the emergency stop command to Arduino with verification."""
    max_retries = 3  # Number of retry attempts
    attempt = 0

    while attempt < max_retries:
        try:
            if ser and ser.is_open:
                #ser.write(b'X')
                #ser.flush()
                print(f"[WARNING] Unexpected response: {response}   RESETING ARDUINO #############################################")
                ser.flush()  # Flush output buffer
                ser.reset_input_buffer()  # Flush input buffer
                ser.write("RESET")
# Reset Arduino via DTR
                ser.dtr = True  # Set DTR line to reset Arduino
                time.sleep(0.1)  # Short delay to ensure reset
                ser.dtr = False  # Release DTR line
                time.sleep(2)  # Give Arduino time to reboot

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
                print(f"###################Error: Invalid response: {line}, not a valid float")
                #ser.write(b"RESET\n")  # Notice the 'b' prefix for bytes

        except SerialException as e:
            print(f"Serial I/O error: {e}")
            print("Attempting to reconnect to Arduino...")
            ser.write(b"RESET\n")  # Notice the 'b' prefix for bytes
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                print("Error: Unable to reconnect to Arduino.")
                return None

        except Exception as e:
            print(f"Unexpected error: {e}")
            print("Attempting to reconnect to Arduino...")
            ser.write(b"RESET\n")  # Notice the 'b' prefix for bytes
            ser = connect_to_arduino()  # Reconnect to Arduino
            if ser is None or not ser.is_open:
                print("Error: Unable to reconnect to Arduino.")
                return None
            

        attempt += 1
        time.sleep(timeout)  # Retry delay
    
    print(f"Error: No valid response after {retries} retries for command {command.decode('utf-8')}")
    print("1. ----------- Closing arduino connection")
    reset_arduino_usb()
    close_serial_connection()
    print("2. ----------- Reconnecting to arduino")
    
    construction_connect_to_arduino()
    print("3. ----------- Other way of conecting to arduino")
    
    connect_to_arduino()
    return None


import subprocess
import time
import os

def reset_arduino_usb():
    """Aggressive USB reset that works when physical replugging fails"""
    try:
        # 1. Try soft reset first
        print("Attempting soft USB reset...")
        subprocess.run(["sudo", "uhubctl", "-l", "1", "-p", "1", "-a", "0"], timeout=5)
        time.sleep(3)
        subprocess.run(["sudo", "uhubctl", "-l", "1", "-p", "1", "-a", "1"], timeout=5)
        time.sleep(5)
        
        # 2. Check if Arduino reappeared
        if os.path.exists('/dev/ttyACM0'):
            print("Soft reset successful")
            return True
            
        # 3. Fallback to USB controller reset
        print("Soft reset failed - trying nuclear option...")
        subprocess.run([
            "sudo", "bash", "-c", 
            "echo 0 > /sys/bus/usb/devices/usb1/authorized && " +
            "sleep 2 && " +
            "echo 1 > /sys/bus/usb/devices/usb1/authorized"
        ], shell=True, timeout=10)
        time.sleep(5)
        
        return os.path.exists('/dev/ttyACM0')
        
    except Exception as e:
        print(f"Reset failed: {str(e)}")
        return False
    



    ########################################################################
import serial
import time
import subprocess
import os
from serial.tools import list_ports

SYMLINK = "/dev/arduino_mega"
ARDUINO_IDS = {(0x2341, 0x0042)}  # Arduino Mega VID:PID

def setup_permissions():
    """Ensure proper permissions for serial devices"""
    try:
        subprocess.run(["sudo", "chmod", "666", "/dev/ttyACM*"], check=True)
        subprocess.run(["sudo", "chmod", "666", "/dev/ttyUSB*"], check=True)
        if os.path.exists(SYMLINK):
            subprocess.run(["sudo", "chmod", "666", SYMLINK], check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠ Permission setup failed: {e}")

def find_arduino_ports():
    """Find all potential Arduino ports"""
    ports = []
    
    # Check symlink first
    if os.path.exists(SYMLINK):
        ports.append(SYMLINK)
    
    # Check by hardware ID
    for port in list_ports.comports():
        if (port.vid, port.pid) in ARDUINO_IDS:
            ports.append(port.device)
    
    # Fallback to standard ports
    for i in range(6):
        for prefix in ['ttyACM', 'ttyUSB']:
            port = f"/dev/{prefix}{i}"
            if os.path.exists(port) and port not in ports:
                ports.append(port)
    
    return ports

def update_symlink(target):
    """Safely update symlink with sudo"""
    try:
        subprocess.run([
            "sudo", "ln", "-sf", target, SYMLINK
        ], check=True)
        subprocess.run(["sudo", "chmod", "666", SYMLINK], check=True)
        print(f"Updated symlink: {SYMLINK} → {target}")
    except subprocess.CalledProcessError as e:
        print(f"⚠ Symlink update failed: {e}")

def robust_connect(retries=3):
    """Main connection handler"""
    setup_permissions()
    
    for attempt in range(retries):
        print(f"\nAttempt {attempt+1}/{retries}")
        
        for port in find_arduino_ports():
            try:
                print(f"Trying {port}...")
                ser = serial.Serial(port, baudrate=9600, timeout=2)
                
                # Test connection
                ser.write(b'PING\n')
                response = ser.readline().decode().strip()
                
                if response in ('PONG', 'ARDUINO_READY'):
                    print(f"✓ Connected on {port}")
                    if port != SYMLINK:
                        update_symlink(port)
                    return ser
                
                ser.close()
            except Exception as e:
                print(f"⚠ Connection failed on {port}: {str(e)}")
        
        # Reset USB if no ports worked
        if attempt < retries - 1:
            print("Resetting USB...")
            try:
                subprocess.run([
                    "sudo", "bash", "-c",
                    "echo 0 > /sys/bus/usb/devices/usb1/authorized && "
                    "sleep 2 && "
                    "echo 1 > /sys/bus/usb/devices/usb1/authorized"
                ], check=True)
                time.sleep(5)
            except Exception as e:
                print(f"⚠ USB reset failed: {e}")
    
    raise Exception("Failed to establish connection")

# Usage Example
try:
    print("Initializing Arduino connection...")
    arduino = robust_connect(retries=3)
    print("Connection established successfully!")
    
    # Your application code here
    
except Exception as e:
    print(f"Fatal error: {e}")
    # Implement your failure recovery here