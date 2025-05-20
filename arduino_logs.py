import serial
import time

def read_arduino_logs():
    # Configure serial port (change '/dev/ttyACM0' to your Arduino's port)
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser.flushInput()
    
    # Send command to request logs
    ser.write(b"GET_LOGS\n")
    
    # Read and display logs
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            
            # Exit after receiving end marker
            if line == "=== END LOGS ===":
                break
    
    ser.close()
read_arduino_logs()
