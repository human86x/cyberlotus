from flask import Flask, render_template, request
import serial
import time

# Setup Serial Connection to Arduino
serial_port = '/dev/ttyACM0'  # Ensure this is the correct port for your setup
ser = serial.Serial(serial_port, 9600)
time.sleep(2)  # Wait for Arduino to initialize

# Create Flask app
app = Flask(__name__)

# Read temperature from Arduino
def get_temperature():
    ser.write(b'R')  # Send a read command to Arduino (you can adapt the command as needed)
    line = ser.readline().decode('utf-8').strip()
    return line

# Control pin based on button press
def control_pin(pin, state):
    if state == 'on':
        ser.write(pin.encode())  # Send the corresponding command to Arduino
    elif state == 'off':
        ser.write(pin.encode())  # Send the corresponding command to Arduino

@app.route('/')
def index():
    temperature = get_temperature()  # Get the temperature from Arduino
    
    # Generate pin labels 'a' to 'h'
    pins = [chr(96 + i) for i in range(1, 9)]  # 'a' to 'h'
    
    # Create a list of pins with their corresponding index
    pin_data = [{"index": i + 3, "pin": pin} for i, pin in enumerate(pins)]
    
    return render_template('index.html', temperature=temperature, pin_data=pin_data)

@app.route('/control', methods=['POST'])
def control():
    pin = request.form.get('pin')
    state = request.form.get('state')
    control_pin(pin, state)
    return index()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
