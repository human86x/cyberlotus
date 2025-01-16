from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/tanks')
def tanks():
    return render_template('tanks.html')

@app.route('/pumps')
def pumps():
    return render_template('pumps.html')

@app.route('/sequences')
def sequences():
    return render_template('sequences.html')

@app.route('/ph')
def ph():
    return render_template('ph.html')

@app.route('/ec')
def ec():
    return render_template('ec.html')

@app.route('/ecosystem')
def ecosystem():
    return render_template('ecosystem.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
