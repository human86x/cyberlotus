from flask import Flask, render_template, request
import serial
import time

# Serial connection to Arduino
serial_port = '/dev/ttyACM0'  # Adjust to match your Arduino port
ser = serial.Serial(serial_port, 9600, timeout=1)
time.sleep(2)  # Allow Arduino time to initialize

app = Flask(__name__)

# Function to read temperature from Arduino
def get_temperature():
    try:
        ser.write(b'R')  # Send 'R' command to request temperature
        time.sleep(0.1)
        line = ser.readline().decode('utf-8').strip()  # Read and decode response
        if line:
            return line
        else:
            return "No data"
    except Exception as e:
        return f"Error: {e}"


# Function to control pins
#def control_pin(pin, state):
#    try:
#        ser.write(f"{pin}{state}".encode())  # Send pin and state (e.g., 'ao' or 'af')
#    except Exception as e:
#        print(f"Error sending pin control command: {e}")
def control_pin(pin, state):
    command = f"{pin}{state}".encode()  # Create command
    ser.write(command)  # Send command
    time.sleep(0.1)  # Short delay for Arduino to process
    print(f"Sent command: {command.decode()}")

@app.route('/')
def index():
    temperature = get_temperature()  # Fetch temperature
    # Pins 'a' to 'h' map to Arduino pins 3–10
    pins = [{"pin": chr(97 + i), "label": f"Pin {3 + i}"} for i in range(8)]  # 'a' to 'h'
    return render_template('index.html', temperature=temperature, pins=pins)



@app.route('/control', methods=['POST'])
def control():
    print("Headers:", request.headers)
    print("Form data:", request.form)
    print("Raw data:", request.data.decode())
    
    pin = request.form.get('pin')
    state = request.form.get('state')

    if not pin or not state:
        return "Invalid request: 'pin' or 'state' missing", 400

    control_pin(pin, state)
    return "Pin controlled successfully!"




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
