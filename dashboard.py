from flask import Flask, render_template, request, redirect, url_for
import json
import time
import os
from control_libs.arduino import connect_to_arduino, send_command_and_get_response

app = Flask(__name__)

# Use absolute path for data file
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(base_dir, 'data/tanks.json')

def load_tanks():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'r') as file:
            return json.load(file)
    return {}

def save_tanks(tanks):
    with open(DATA_PATH, 'w') as file:
        json.dump(tanks, file, indent=4)

@app.route('/')
def index():
    tanks = load_tanks()
    return render_template('index.html', tanks=tanks)

@app.route('/create_tank', methods=['GET', 'POST'])
def create_tank():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        total_volume = float(request.form['total_volume'])
        full_cm = float(request.form['full_cm'])
        empty_cm = float(request.form['empty_cm'])

        tanks = load_tanks()
        tanks[name] = {
            'arduino_code': code,
            'total_volume': total_volume,
            'full_cm': full_cm,
            'empty_cm': empty_cm
        }
        save_tanks(tanks)
        return redirect(url_for('index'))

    return render_template('create_tank.html')

@app.route('/test_tanks')
def test_tanks():
    tanks = load_tanks()
    serial_conn = connect_to_arduino()
    time.sleep(2)
    
    test_results = {}
    for name, info in tanks.items():
        send_command_and_get_response(serial_conn, info['arduino_code'])
        time.sleep(0.5)
        if serial_conn.in_waiting:
            response = serial_conn.readline().decode().strip()
            try:
                distance = float(response)
                fill_percentage = max(0, min(100, ((info['empty_cm'] - distance) / 
                              (info['empty_cm'] - info['full_cm'])) * 100))
                current_volume = (fill_percentage / 100) * info['total_volume']
                test_results[name] = {
                    'distance': distance,
                    'fill_percentage': fill_percentage,
                    'current_volume': current_volume
                }
            except ValueError:
                test_results[name] = {'error': 'Invalid response'}
        else:
            test_results[name] = {'error': 'No response from sensor'}
    
    return render_template('test_tanks.html', test_results=test_results)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)  # Run Flask server
    finally:
        #ser.close()  # Ensure serial connection is closed on exit
