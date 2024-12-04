from flask_control import Flask, render_template, request, jsonify
import serial
import time

# Initialize Flask app
app = Flask(__name__)

# Serial configuration
serial_port = '/dev/ttyACM0'  # Update with your port
baud_rate = 9600

# Establish serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=1)
time.sleep(2)  # Allow Arduino to initialize


# Read temperature from Arduino
def get_temperature():
    ser.write(b'R')  # Send a read command to Arduino (you can adapt the command as needed)
    line = ser.readline().decode('utf-8').strip()
    return line

# Function to send commands to Arduino
def control_pin(pin, state):
    try:
        command = f"{pin}{state}".encode()  # Create command
        ser.write(command)  # Send command
        time.sleep(0.1)  # Short delay for Arduino to process
        response = ser.readline().decode('utf-8').strip()  # Read and decode response
        return response
    except Exception as e:
        return str(e)

@app.route('/')
def index():
    temperature = get_temperature()  # Get the temperature from Arduino
    return render_template('index.html', temperature=temperature)
    #return render_template('index.html')  # Render the web interface

@app.route('/control', methods=['POST'])
def control():
    try:
        pin = request.json.get('pin')  # Get pin from request
        state = request.json.get('state')  # Get state from request ('o' or 'f')
        response = control_pin(pin, state)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)  # Run Flask server
    finally:
        ser.close()  # Ensure serial connection is closed on exit
