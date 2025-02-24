from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, AnonymousUserMixin
from datetime import datetime
import os

app = Flask(__name__)
# Use environment variables for configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
# Database URL from environment variable, fallback to SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///madness.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    picks = db.relationship('BracketPick', backref='user', lazy=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    seed = db.Column(db.Integer, nullable=False)
    region = db.Column(db.String(20), nullable=False)  # East, West, South, Midwest
    eliminated = db.Column(db.Boolean, default=False)
    picks = db.relationship('BracketPick', backref='team', lazy=True)

class BracketPick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)  # 1=First Round, 2=Second Round, etc.
    position = db.Column(db.Integer, nullable=False)  # Position in the bracket
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # In production, use proper password hashing!
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/bracket')
def bracket():
    # Check if any teams exist in the database
    team_count = Team.query.count()
    
    # If no teams exist, redirect to initialization page
    if team_count == 0:
        flash('Please initialize teams before viewing the bracket.')
        return redirect(url_for('init_teams_page'))
    
    # Get all teams organized by region
    teams = {}
    for region in ['East', 'West', 'South', 'Midwest']:
        teams[region] = Team.query.filter_by(region=region).order_by(Team.seed).all()
    
    # Get user's picks if they exist
    picks_dict = {}
    if current_user.is_authenticated:
        user_picks = BracketPick.query.filter_by(user_id=current_user.id).all()
        picks_dict = {f"{p.round_number}-{p.position}": p.team_id for p in user_picks}
    
    return render_template('bracket.html', teams=teams, picks=picks_dict)

@app.route('/bracket/submit', methods=['POST'])
@login_required
def submit_bracket():
    if request.method == 'POST':
        try:
            # Clear existing picks
            BracketPick.query.filter_by(user_id=current_user.id).delete()
            
            # Process new picks
            picks_data = request.json
            for pick in picks_data:
                new_pick = BracketPick(
                    user_id=current_user.id,
                    team_id=pick['team_id'],
                    round_number=pick['round'],
                    position=pick['position']
                )
                db.session.add(new_pick)
            
            db.session.commit()
            return jsonify({'status': 'success'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/bracket/picks')
@login_required
def get_picks():
    picks = BracketPick.query.filter_by(user_id=current_user.id).all()
    picks_data = [{
        'team_id': pick.team_id,
        'round': pick.round_number,
        'position': pick.position
    } for pick in picks]
    return jsonify(picks_data)

# Admin route to initialize teams
@app.route('/admin/init-teams', methods=['POST'])
@login_required
def init_teams():
    try:
        # Clear existing teams
        Team.query.delete()
        
        # 2024 March Madness Teams
        teams_data = {
            'East': [
                {'name': 'UConn', 'seed': 1},
                {'name': 'Iowa State', 'seed': 2},
                {'name': 'Illinois', 'seed': 3},
                {'name': 'Auburn', 'seed': 4},
                {'name': 'San Diego State', 'seed': 5},
                {'name': 'BYU', 'seed': 6},
                {'name': 'Washington State', 'seed': 7},
                {'name': 'FAU', 'seed': 8},
                {'name': 'Northwestern', 'seed': 9},
                {'name': 'Drake', 'seed': 10},
                {'name': 'Duquesne', 'seed': 11},
                {'name': 'UAB', 'seed': 12},
                {'name': 'Yale', 'seed': 13},
                {'name': 'Morehead State', 'seed': 14},
                {'name': 'South Dakota State', 'seed': 15},
                {'name': 'Stetson', 'seed': 16}
            ],
            'West': [
                {'name': 'North Carolina', 'seed': 1},
                {'name': 'Arizona', 'seed': 2},
                {'name': 'Baylor', 'seed': 3},
                {'name': 'Alabama', 'seed': 4},
                {'name': 'Saint Mary\'s', 'seed': 5},
                {'name': 'Clemson', 'seed': 6},
                {'name': 'Dayton', 'seed': 7},
                {'name': 'Mississippi State', 'seed': 8},
                {'name': 'Michigan State', 'seed': 9},
                {'name': 'Nevada', 'seed': 10},
                {'name': 'New Mexico', 'seed': 11},
                {'name': 'Grand Canyon', 'seed': 12},
                {'name': 'Charleston', 'seed': 13},
                {'name': 'Colgate', 'seed': 14},
                {'name': 'Long Beach State', 'seed': 15},
                {'name': 'Wagner', 'seed': 16}
            ],
            'South': [
                {'name': 'Houston', 'seed': 1},
                {'name': 'Marquette', 'seed': 2},
                {'name': 'Kentucky', 'seed': 3},
                {'name': 'Duke', 'seed': 4},
                {'name': 'Wisconsin', 'seed': 5},
                {'name': 'Texas Tech', 'seed': 6},
                {'name': 'Florida', 'seed': 7},
                {'name': 'Nebraska', 'seed': 8},
                {'name': 'Texas A&M', 'seed': 9},
                {'name': 'Colorado', 'seed': 10},
                {'name': 'NC State', 'seed': 11},
                {'name': 'James Madison', 'seed': 12},
                {'name': 'Vermont', 'seed': 13},
                {'name': 'Oakland', 'seed': 14},
                {'name': 'Western Kentucky', 'seed': 15},
                {'name': 'Longwood', 'seed': 16}
            ],
            'Midwest': [
                {'name': 'Purdue', 'seed': 1},
                {'name': 'Tennessee', 'seed': 2},
                {'name': 'Creighton', 'seed': 3},
                {'name': 'Kansas', 'seed': 4},
                {'name': 'Gonzaga', 'seed': 5},
                {'name': 'South Carolina', 'seed': 6},
                {'name': 'Texas', 'seed': 7},
                {'name': 'Utah State', 'seed': 8},
                {'name': 'TCU', 'seed': 9},
                {'name': 'Virginia', 'seed': 10},
                {'name': 'Oregon', 'seed': 11},
                {'name': 'McNeese', 'seed': 12},
                {'name': 'Samford', 'seed': 13},
                {'name': 'Akron', 'seed': 14},
                {'name': 'Saint Peter\'s', 'seed': 15},
                {'name': 'Montana State', 'seed': 16}
            ]
        }
        
        for region, teams in teams_data.items():
            for team in teams:
                new_team = Team(
                    name=team['name'],
                    seed=team['seed'],
                    region=region
                )
                db.session.add(new_team)
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

# Add a test user creation route for development
@app.route('/create-test-user')
def create_test_user():
    if app.debug:  # Only allow in debug mode
        # Check if test user already exists
        if not User.query.filter_by(username='test').first():
            test_user = User(
                username='test',
                password='password',  # In production, hash this!
                email='test@example.com'
            )
            db.session.add(test_user)
            db.session.commit()
            flash('Test user created successfully!')
        return redirect(url_for('login'))
    return "Not available in production", 403

@app.route('/init-teams-page')
def init_teams_page():
    return render_template('init_teams.html')

if __name__ == '__main__':
    # Only create tables if running locally
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
        with app.app_context():
            db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)