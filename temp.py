from flask import Flask, render_template
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
        time.sleep(0.1)  # Small delay for Arduino to respond
        line = ser.readline().decode('utf-8').strip()  # Read and decode response
        if line:  # Ensure we got a response
            return line
        else:
            return "No data"
    except Exception as e:
        return f"Error: {e}"

@app.route('/')
def index():
    temperature = get_temperature()  # Fetch temperature
    return render_template('index.html', temperature=temperature)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
