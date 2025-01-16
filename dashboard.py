from flask import Flask, render_template, request, redirect, url_for
import time
from control_libs.arduino import connect_to_arduino
from tanks import load_tanks, save_tanks, create_tank, test_tanks

app = Flask(__name__)

@app.route('/')
def index():
    tanks = load_tanks()
    return render_template('index.html', tanks=tanks)

@app.route('/create_tank', methods=['GET', 'POST'])
def create_tank_route():
    if request.method == 'POST':
        name = request.form['name']
        code = request.form['code']
        total_volume = float(request.form['total_volume'])
        full_cm = float(request.form['full_cm'])
        empty_cm = float(request.form['empty_cm'])

        tanks = load_tanks()
        create_tank(tanks, name, code, total_volume, full_cm, empty_cm)
        return redirect(url_for('index'))

    return render_template('create_tank.html')

@app.route('/test_tanks')
def test_tanks_route():
    tanks = load_tanks()
    serial_conn = connect_to_arduino()
    time.sleep(2)
    
    test_results = test_tanks(tanks, serial_conn)
    return render_template('test_tanks.html', test_results=test_results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
