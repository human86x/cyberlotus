import serial
import time
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from control_libs.arduino import connect_to_arduino, send_command_and_get_response

#from config_tools.flow_tune import PUMP_COMMANDS

ser = None  # Define the global variable for the serial connection

def connect_to_arduino():
    global ser  # Access the global serial connection variable
    """
    Ensures only one connection is created and reused.
    Reconnects if the connection is lost or invalid.
    """
    print("Checking Arduino connection...")

    # Check if a valid connection already exists
    if ser and ser.is_open:
        print(f"Arduino is already connected on {ser.port}.")
        return ser

    # Try to establish a new connection
    for i in range(11):  # Check ports /dev/ttyACM0 to /dev/ttyACM10
        port = f"/dev/ttyACM{i}"
        try:
            print(f"Trying to connect to {port}...")
            ser = serial.Serial(port, baudrate=9600, timeout=1)  # Set a 1-second timeout
            time.sleep(2)  # Allow time for Arduino to reset
            print(f"Connected successfully to {port}")
            return ser
        except serial.SerialException as e:
            print(f"Failed to connect to {port}: {e}")
            continue

    # Raise an exception if no ports work
    raise Exception("Unable to connect to Arduino on any /dev/ttyACM* port.")



def get_serial_connection():
    global ser
    if ser and ser.is_open:
        return ser
    else:
        print("[ERROR] Serial connection is not established.")
        return None

def close_serial_connection():
    global ser
    if ser and ser.is_open:
        ser.close()
        print("[INFO] Serial connection closed.")


def safe_serial_write(pump_name, state, retries=1, timeout=2):
    global ser
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
    #    if pump_name not in PUMP_COMMANDS:
    #        print(f"[ERROR] Invalid pump name: {pump_name}")
    #        return

    #    if state not in ['o', 'f']:
    #        print(f"[ERROR] Invalid pump state: {state}")
    #        return

        command = pump_name + state
        expected_response = f"{'ON' if state == 'o' else 'OFF'}_{pump_name}"
        
        attempt = 0

        while attempt <= retries:
            if ser and ser.is_open:
                #ser.reset_input_buffer()  # Clear any previous data
                ser.write(command.encode())
                ser.flushOutput()
                print(f"[INFO] Sent command: {command}, waiting for response...")

                start_time = time.time()
                while time.time() - start_time < timeout:
                    if ser.in_waiting > 0:
                        response = ser.readline().decode().strip()
                        print(f"[INFO] Received response: {response}")

                        if response == expected_response:
                            print(f"[SUCCESS] Arduino confirmed action: {response}")
                            return  # Exit after successful confirmation
                        else:
                            print(f"[WARNING] Unexpected response: {response}")
                    
                    time.sleep(0.1)  # Small delay to avoid CPU overuse

                    # If no valid response, retry
                print(f"[ERROR] No valid response. Retrying... (Attempt {attempt + 1}/{retries})")
                attempt += 1

            else:
                print("[ERROR] Serial port is not open. Cannot send command.")
                return

        # After retries fail
        print("[ERROR] Failed to confirm command after retries. Attempting emergency stop.")
        emergency_stop(pump_name)

    except ser.SerialException as e:
        print(f"[ERROR] Serial write failed for {pump_name}: {e}")
        emergency_stop(pump_name)
    except Exception as e:
        print(f"[ERROR] Unexpected error while writing to serial: {e}")
        emergency_stop(pump_name)



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

def send_command_and_get_response(ser, command, retries=5, timeout=1):
    attempt = 0
    
    while attempt < retries:
        # Ensure serial connection is open
        if not ser.is_open:
            #print("Serial port is not open, attempting to reconnect...")
            ser = connect_to_arduino()  # Ensure you have a function to reconnect to Arduino
            if ser is None or not ser.is_open:
                print("Error: Unable to reconnect to Arduino.")
                return None
        
        # Clear the input buffer
        #while ser.in_waiting > 0:
            #ser.read(1)
        
        # Clear the output buffer
        #ser.flushOutput()
        
        print(f"Send command and get response -> the command >>> {command}")
        ser.write(command)  # No need to encode if command is already bytes
        
        # Read response from Arduino
        line = ser.readline().decode('utf-8').strip()
        print(f"Send command and get response -> the response >>> {line}")
        
        # Check if response is a valid float
        try:
            value = float(line)
            return value  # Valid response, return the float
        except ValueError:
            print(f"Error: Invalid response: {line}, not a valid float")
        
        attempt += 1
        time.sleep(timeout)  # Retry delay
    
    print(f"Error: No valid response after {retries} retries for command {command.decode('utf-8')}")
    return None