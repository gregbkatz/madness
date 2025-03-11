from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from data.teams import teams
from datetime import datetime
from bracket_logic import initialize_bracket, select_team, auto_fill_bracket, pretty_print_bracket, update_winners, random_fill_bracket, reset_team_completely
import json
import os
import copy
import re

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for using sessions

# Dictionary to store brackets for each user
user_brackets = {}

# Ensure the saved_brackets directory exists
os.makedirs('saved_brackets', exist_ok=True)

# Create user directory if it doesn't exist
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), 'user_data')
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# In-memory bracket (will be moved to user-specific storage)
brackets = {}

def get_empty_bracket():
    """Create and return an empty bracket structure."""
    return {
        'west': [[None for _ in range(8)] for _ in range(4)],
        'east': [[None for _ in range(8)] for _ in range(4)],
        'south': [[None for _ in range(8)] for _ in range(4)],
        'midwest': [[None for _ in range(8)] for _ in range(4)],
        'finalFour': [None, None, None, None],
        'championship': [None, None],
        'champion': None
    }

def get_user_bracket_path(username):
    """Get the path to a user's bracket file."""
    user_dir = os.path.join(USER_DATA_DIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def validate_username(username):
    """Validate a username."""
    if not username:
        return False
    if len(username) < 3 or len(username) > 20:
        return False
    if not username.isalnum():
        return False
    return True

def load_bracket(username):
    """Load a user's bracket from disk."""
    user_dir = get_user_bracket_path(username)
    latest_file = None
    latest_time = 0

    # Look for the most recent bracket file
    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(user_dir, filename)
            file_time = os.path.getmtime(file_path)
            if file_time > latest_time:
                latest_time = file_time
                latest_file = file_path
    
    if latest_file:
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading bracket: {e}")
    
    # Return a new initialized bracket if no saved bracket is found
    return initialize_bracket()

def save_bracket(username, bracket):
    """Save a user's bracket to disk."""
    user_dir = get_user_bracket_path(username)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bracket_{timestamp}.json"
    file_path = os.path.join(user_dir, filename)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(bracket, f)
        return True, filename
    except Exception as e:
        return False, str(e)

# Initialize test bracket
brackets['test'] = initialize_bracket()

@app.route('/')
def index():
    """Render the login page."""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """Process login and redirect to the user's bracket."""
    username = request.form.get('username', '').strip()
    display_name = request.form.get('display_name', '').strip()
    
    if not validate_username(username):
        return render_template('login.html', error="Invalid username. Please use only letters and numbers, 3-20 characters.")
    
    # If no display name is provided, use the username
    if not display_name:
        display_name = username
    
    # Redirect to the user's bracket page
    return redirect(url_for('user_bracket', username=username, display_name=display_name))

@app.route('/bracket/<username>')
def user_bracket(username):
    """Render the bracket page for a specific user."""
    if not validate_username(username):
        return redirect(url_for('index'))
    
    display_name = request.args.get('display_name', username)
    is_owner = True  # For now, we're allowing anyone to edit any bracket
    
    # Load the user's bracket from disk if it exists
    if username not in brackets:
        brackets[username] = load_bracket(username)
    
    return render_template('index.html', username=username, display_name=display_name, is_owner=is_owner)

@app.route('/bracket-test')
def bracket_test():
    """Render the test bracket page (original implementation)."""
    return render_template('index.html', username='test', display_name='Test Bracket', is_owner=True)

@app.route('/logout')
def logout():
    """Log out the user by clearing their session"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/teams')
def get_teams():
    """Return the teams for the tournament."""
    return jsonify(teams)

@app.route('/api/save-bracket', methods=['POST'])
def api_save_bracket():
    """API endpoint to save the current bracket to a file."""
    username = request.args.get('username', 'test')
    
    if username not in brackets:
        return jsonify({'success': False, 'error': 'Bracket not found'})
    
    success, result = save_bracket(username, brackets[username])
    
    if success:
        return jsonify({'success': True, 'message': f'Bracket saved as {result}'})
    else:
        return jsonify({'success': False, 'error': result})

@app.route('/api/saved-brackets')
def api_saved_brackets():
    """API endpoint to get a list of saved brackets."""
    username = request.args.get('username', 'test')
    user_dir = get_user_bracket_path(username)
    
    if not os.path.exists(user_dir):
        return jsonify({'success': False, 'error': 'No saved brackets found'})
    
    bracket_files = []
    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(user_dir, filename)
            modified_time = os.path.getmtime(file_path)
            modified_time_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract date from filename
            file_date = filename.split('_')[0].replace('bracket_', '')
            
            bracket_files.append({
                'filename': filename,
                'modified': modified_time_str,
                'date': file_date
            })
    
    # Sort by modified time, newest first
    bracket_files.sort(key=lambda x: x['filename'], reverse=True)
    
    return jsonify({'success': True, 'brackets': bracket_files})

@app.route('/api/load-bracket/<filename>')
def api_load_bracket(filename):
    """API endpoint to load a bracket from a file."""
    username = request.args.get('username', 'test')
    user_dir = get_user_bracket_path(username)
    file_path = os.path.join(user_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'})
    
    try:
        with open(file_path, 'r') as f:
            loaded_bracket = json.load(f)
        
        # Update the in-memory bracket
        brackets[username] = loaded_bracket
        
        return jsonify({'success': True, 'message': f'Bracket loaded successfully', 'bracket': loaded_bracket})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bracket', methods=['GET', 'POST'])
def manage_bracket():
    """API endpoint to manage the bracket."""
    # Get the username from the query string, default to 'test'
    username = request.args.get('username', 'test')
    
    # Ensure the bracket exists for this user
    if username not in brackets:
        brackets[username] = load_bracket(username)
    
    bracket = brackets[username]
    
    if request.method == 'GET':
        return jsonify(bracket)
    
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        
        if action == 'update':
            region = data.get('region')
            round_index = data.get('roundIndex')
            game_index = data.get('gameIndex')
            team_index = data.get('teamIndex')
            
            # Calculate the team's position in the next round
            next_round_index = round_index + 1
            next_game_index = game_index // 2
            
            # Update the next round with the selected team
            if region in bracket and round_index < len(bracket[region]):
                # Get the team from the current game
                team_in_current_round = bracket[region][round_index][game_index][team_index] if bracket[region][round_index][game_index] else None
                
                if team_in_current_round:
                    # Place the team in the next round
                    if next_round_index < len(bracket[region]):
                        if bracket[region][next_round_index][next_game_index] is None:
                            bracket[region][next_round_index][next_game_index] = [None, None]
                        bracket[region][next_round_index][next_game_index][game_index % 2] = team_in_current_round
                        
                        # Clear following rounds
                        clear_following_rounds(bracket, region, next_round_index, next_game_index)
        
        elif action == 'update_final_four':
            region = data.get('region')
            slot_index = data.get('slotIndex')
            semifinal_index = data.get('semifinalIndex')
            team_index = data.get('teamIndex')
            
            # Get the regional champion
            if region in bracket:
                regional_champion = bracket[region][3][0][team_index] if bracket[region][3][0] else None
                
                if regional_champion:
                    # Update the Final Four slot
                    bracket['finalFour'][slot_index] = regional_champion
                    
                    # Clear championship slot corresponding to this semifinal
                    championship_slot = 0 if slot_index in [1, 2] else 1
                    if bracket['championship'][championship_slot] == regional_champion:
                        bracket['championship'][championship_slot] = None
                        
                        # If this team was the champion, clear the champion as well
                        if bracket['champion'] == regional_champion:
                            bracket['champion'] = None
        
        elif action == 'update_championship':
            ff_index = data.get('ffIndex')
            slot_index = data.get('slotIndex')
            
            # Get the team from Final Four
            team = bracket['finalFour'][ff_index]
            
            if team:
                # Update championship slot
                bracket['championship'][slot_index] = team
                
                # If this team was the champion and we're replacing it in the championship,
                # then clear the champion as well
                if bracket['champion'] == team:
                    bracket['champion'] = None
                
        elif action == 'select_champion':
            slot_index = data.get('slotIndex')
            
            # Get the team from championship
            team = bracket['championship'][slot_index]
            
            if team:
                # Toggle champion selection
                if bracket['champion'] == team:
                    bracket['champion'] = None
                else:
                    bracket['champion'] = team
        
        elif action == 'auto_fill':
            # Use the bracket_logic implementation for auto-fill
            brackets[username] = auto_fill_bracket(bracket)
            bracket = brackets[username]
        
        elif action == 'random_fill':
            # Use the bracket_logic implementation for random fill
            brackets[username] = random_fill_bracket(bracket)
            bracket = brackets[username]
        
        elif action == 'reset':
            # Reset the bracket to a new initialized state
            bracket = initialize_bracket()
            brackets[username] = bracket
        
        # Save the updated bracket
        save_bracket(username, bracket)
        
        return jsonify(bracket)

def clear_following_rounds(bracket, region, round_index, game_index):
    """Clear selections in all rounds following the given round and game."""
    # Clear the rest of the current round
    for next_round in range(round_index + 1, len(bracket[region])):
        next_game = game_index // (2 ** (next_round - round_index))
        
        if bracket[region][next_round][next_game] is not None:
            bracket[region][next_round][next_game][game_index % 2] = None
            
            # If this was a regional final, clear the Final Four as well
            if next_round == 3 and next_game == 0:
                ff_index = get_ff_index_for_region(region)
                if bracket['finalFour'][ff_index] is not None:
                    team = bracket['finalFour'][ff_index]
                    bracket['finalFour'][ff_index] = None
                    
                    # If this team was in the championship, clear that too
                    championship_slot = 0 if ff_index in [1, 2] else 1
                    if bracket['championship'][championship_slot] == team:
                        bracket['championship'][championship_slot] = None
                        
                        # If this team was the champion, clear that too
                        if bracket['champion'] == team:
                            bracket['champion'] = None

def get_ff_index_for_region(region):
    """Get the Final Four index for a region."""
    if region == 'west':
        return 0
    elif region == 'east':
        return 1
    elif region == 'south':
        return 2
    elif region == 'midwest':
        return 3
    return -1

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 