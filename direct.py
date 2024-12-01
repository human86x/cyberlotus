import serial
import time

# Serial configuration
serial_port = '/dev/ttyACM0'  # Update with your port
baud_rate = 9600

# Establish connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)  # Allow Arduino to initialize

def get_temperature():
    ser.write(b'R')  # Request temperature
    time.sleep(0.1)  # Wait for Arduino to respond
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    return response

def control_pin(pin, state):
    command = f"{pin}{state}".encode()  # Create command
    ser.write(command)  # Send command
    time.sleep(0.1)  # Short delay for Arduino to process
    print(f"Sent command: {command.decode()}")

try:
    # Get temperature
    temperature = get_temperature()
    print(f"Temperature: {temperature} °C")
    
    # Control pin 7 (mapped to 'e')
    control_pin('a', 'o')  # Turn pin 7 ON
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('a', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)           # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    
    
    control_pin('b', 'o')  # Turn pin 7 ON
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('b', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    
    control_pin('c', 'o')  # Turn pin 7 ON
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('c', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    

    control_pin('d', 'o')  # Turn pin 7 ON
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('d', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)           # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    

    control_pin('e', 'o')  # Turn pin 7 ON
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('e', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)           # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    
    control_pin('l', 'o')  # Turn pin 7 ON
    time.sleep(0.2)        # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('l', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)          # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    

    control_pin('g', 'o')  # Turn pin 7 ON
    time.sleep(0.2)         # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('g', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)         # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    

    control_pin('h', 'o')  # Turn pin 7 ON
    time.sleep(0.2)         # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    control_pin('h', 'f')  # Turn pin 7 OFF
    time.sleep(0.2)        # Wait for 2 seconds
    response = ser.readline().decode('utf-8').strip()  # Read and decode response
    print(f"The response:  {response}")
    
    


    

    
    
    
    
    
    
    





finally:
    ser.close()  # Close serial connection
