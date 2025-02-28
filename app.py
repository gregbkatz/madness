from flask import Flask, render_template, jsonify
from data.teams import teams
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
    return render_template('index.html', current_time=current_time)

@app.route('/api/teams')
def get_teams():
    return jsonify(teams)

if __name__ == '__main__':
    app.run(debug=True) 