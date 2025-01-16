from flask import Flask, render_template, request, redirect, url_for, jsonify
from config_tools.tank_manager import load_tanks, add_tank, test_tanks

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/pumps')
def pumps():
    return render_template('pumps.html')

@app.route('/sequences')
def sequences():
    return render_template('sequences.html')
@app.route('/ec')
def ec():
    return render_template('EC.html')
@app.route('/ph')
def ph():
    return render_template('ph.html')
@app.route('/ecosystem')
def ecosystem():
    return render_template('ecsystem.html')






@app.route('/tanks')
def tanks():
    tanks_data = load_tanks()
    return render_template('tanks.html', tanks=tanks_data)

@app.route('/tanks/create', methods=['POST'])
def create_tank_route():
    name = request.form['name']
    code = request.form['code']
    total_volume = float(request.form['total_volume'])
    full_cm = float(request.form['full_cm'])
    empty_cm = float(request.form['empty_cm'])

    add_tank(name, code, total_volume, full_cm, empty_cm)
    return redirect(url_for('tanks'))

@app.route('/tanks/test', methods=['GET'])
def test_tanks_route():
    results = test_tanks()
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
