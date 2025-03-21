from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from data.teams import teams
from datetime import datetime
from bracket_logic import initialize_bracket, select_team, auto_fill_bracket, pretty_print_bracket, update_winners, random_fill_bracket, reset_team_completely
import json
import os
import copy
import re
import sys
import argparse
import glob  # For finding truth bracket files

# Add command-line argument parsing
parser = argparse.ArgumentParser(description='March Madness Bracket Application')
parser.add_argument('--read-only', 
                   dest='read_only',
                   type=lambda x: (str(x).lower() == 'true'),
                   default=True, 
                   help='Run the application in read-only mode (defaults to true)')
args = parser.parse_args()

app = Flask(__name__)
app.secret_key = 'march_madness_simple_key'  # Secret key for session

# Store read-only mode as a global application setting
READ_ONLY_MODE = args.read_only

# No longer using a global bracket - each user will have their own in their session

# Ensure the saved_brackets directory exists
os.makedirs('saved_brackets', exist_ok=True)
# Ensure the truth_brackets directory exists
os.makedirs('truth_brackets', exist_ok=True)

# Function to find the most recent truth bracket
def get_most_recent_truth_bracket():
    """Find and load the most recent truth bracket file."""
    try:
        # Get all bracket files in the truth_brackets directory
        truth_files = glob.glob('truth_brackets/*.json')
        
        if not truth_files:
            return None
            
        # Sort by modification time, most recent first
        truth_files.sort(key=os.path.getmtime, reverse=True)
        
        # Load the most recent file
        with open(truth_files[0], 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading truth bracket: {str(e)}")
        return None

# Function to load the "all chalk" bracket
def get_chalk_bracket():
    """Load the all chalk bracket from the predefined file."""
    try:
        with open('data/bracket_all_chalk.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading chalk bracket: {str(e)}")
        return None

# Define upset bonus multipliers for each round
UPSET_BONUS_MULTIPLIERS = {
    "round_1": 2,
    "round_2": 5, 
    "round_3": 10,
    "final_four": 20,
    "championship": 20,
    "champion": 20
}

# Define a global constant map for points per round
POINTS_MAP = {
    1: 10,              # Round of 32
    2: 20,              # Sweet 16
    3: 40,              # Elite 8
    "final_four": 80,
    "championship": 120,
    "champion": 160
}

def calculate_points_for_pick(team, round_idx):
    """Calculate both base and bonus points for a pick."""
    if not team:
        return 0, 0
        
    base_points = POINTS_MAP.get(round_idx, 0)
    bonus_points = team.get("bonus", 0)
    
    return base_points, bonus_points

# Function to compare a bracket with the truth bracket and add comparison CSS classes
def compare_with_truth(bracket):
    """Compare a bracket with the most recent truth bracket and add CSS classes."""
    truth_bracket = get_most_recent_truth_bracket()
    if not truth_bracket or not bracket:
        return bracket
        
    # Deep copy the bracket to avoid modifying the original
    result_bracket = copy.deepcopy(bracket)
    
    # Try to get the chalk bracket for bonus calculations
    chalk_bracket = get_chalk_bracket()
    print(f"Chalk bracket loaded: {chalk_bracket is not None}")
    
    # Debug counts
    correct_count = 0
    bonus_count = 0
    
    # Track eliminated teams - teams that were picked but are marked as incorrect
    eliminated_teams = set()
    
    # Add a classes field to each team if it doesn't exist
    for region in ["midwest", "west", "south", "east"]:
        for round_idx in range(len(result_bracket[region])):
            for i in range(len(result_bracket[region][round_idx])):
                team = result_bracket[region][round_idx][i]
                if team:
                    if not isinstance(team, dict):
                        # Skip if team is not a dictionary
                        continue
                    
                    # Initialize the classes field if it doesn't exist
                    if "classes" not in team:
                        team["classes"] = ""
                    
                    # Skip first round as it's pre-filled
                    if round_idx == 0:
                        continue
                        
                    # Compare with truth bracket
                    try:
                        truth_team = truth_bracket[region][round_idx][i] if round_idx < len(truth_bracket[region]) else None
                        
                        # Calculate potential bonus points regardless of whether this round exists in truth bracket
                        if chalk_bracket and round_idx > 0:
                            # Find the same POSITION in chalk bracket for this round
                            chalk_team = None
                            if round_idx < len(chalk_bracket[region]):
                                # Get the team at the same position in chalk bracket
                                if i < len(chalk_bracket[region][round_idx]):
                                    chalk_team = chalk_bracket[region][round_idx][i]
                            
                            # Calculate bonus if we found the team in chalk bracket
                            if chalk_team:
                                seed_diff = abs(int(chalk_team.get("seed", 0)) - int(team.get("seed", 0)))
                                if seed_diff > 0:
                                    # If team's seed is higher (numerically) than chalk_team's seed, it's an upset
                                    bonus = seed_diff * UPSET_BONUS_MULTIPLIERS[f"round_{round_idx}"]
                                    team["bonus"] = int(bonus)  # Ensure it's an integer
                                    bonus_count += 1
                                    print(f"Added bonus of {bonus} to {team['name']} in {region} round {round_idx} position {i}")
                                else:
                                    team["bonus"] = 0  # Explicitly set to zero instead of None
                                    print(f"Set bonus to 0 for {team['name']} in {region} round {round_idx} (no upset)")
                        
                        # If truth team is None (future round), we're done with this team
                        if not truth_team:
                            # Check if this team is in the eliminated teams set before continuing
                            if team["name"] in eliminated_teams:
                                team["classes"] += " incorrect"
                                team["correct"] = False
                                team["isEliminated"] = True
                                print(f"Marked future pick {team['name']} in {region} round {round_idx} as eliminated")
                            continue

                        # Compare teams by name and seed
                        if team["name"] == truth_team["name"] and team["seed"] == truth_team["seed"]:
                            team["classes"] += " correct"
                            team["correct"] = True
                            correct_count += 1
                        else:
                            team["classes"] += " incorrect"
                            team["correct"] = False
                            # Add the truth team data for incorrect picks
                            if truth_team:
                                team["truthTeam"] = {
                                    "name": truth_team["name"],
                                    "seed": truth_team["seed"],
                                    "abbrev": truth_team.get("abbrev", "")
                                }
                            
                            # Add this team to the eliminated teams set
                            eliminated_teams.add(team["name"])
                    except (IndexError, KeyError, TypeError) as e:
                        # If any error occurs, skip comparison for this team
                        print(f"Error comparing team in {region} round {round_idx} position {i}: {str(e)}")
                        continue
    
    # Compare Final Four
    for i in range(len(result_bracket["finalFour"])):
        team = result_bracket["finalFour"][i]
        if team:
            if "classes" not in team:
                team["classes"] = ""
                
            try:
                truth_team = truth_bracket["finalFour"][i] if i < len(truth_bracket["finalFour"]) else None
                
                # Calculate potential bonus for all teams regardless of truth team
                if chalk_bracket:
                    # Get the chalk team at the same position in the Final Four
                    chalk_team = None
                    if i < len(chalk_bracket["finalFour"]):
                        chalk_team = chalk_bracket["finalFour"][i]
                    
                    if chalk_team:
                        seed_diff = abs(int(chalk_team.get("seed", 0)) - int(team.get("seed", 0)))
                        if seed_diff > 0:
                            bonus = seed_diff * UPSET_BONUS_MULTIPLIERS["final_four"]
                            team["bonus"] = int(bonus)  # Ensure it's an integer
                            print(f"Added Final Four bonus of {bonus} to {team['name']} (pos {i})")
                        else:
                            team["bonus"] = 0
                
                # Skip comparison if truth team doesn't exist yet
                if not truth_team:
                    # Check if this team is in the eliminated teams set before continuing
                    if team["name"] in eliminated_teams:
                        team["classes"] += " incorrect"
                        team["correct"] = False
                        team["isEliminated"] = True
                        print(f"Marked future pick {team['name']} in Final Four as eliminated")
                    continue
                
                if team["name"] == truth_team["name"] and team["seed"] == truth_team["seed"]:
                    team["classes"] += " correct"
                    team["correct"] = True
                else:
                    team["classes"] += " incorrect"
                    team["correct"] = False
                    # Add the truth team data for incorrect picks
                    if truth_team:
                        team["truthTeam"] = {
                            "name": truth_team["name"],
                            "seed": truth_team["seed"],
                            "abbrev": truth_team.get("abbrev", "")
                        }
                    
                    # Add this team to the eliminated teams set
                    eliminated_teams.add(team["name"])
            except (IndexError, KeyError, TypeError) as e:
                print(f"Error comparing Final Four team at position {i}: {str(e)}")
                continue
    
    # Compare Championship
    for i in range(len(result_bracket["championship"])):
        team = result_bracket["championship"][i]
        if team:
            if "classes" not in team:
                team["classes"] = ""
                
            try:
                truth_team = truth_bracket["championship"][i] if i < len(truth_bracket["championship"]) else None
                
                # Calculate potential bonus for all teams regardless of truth team
                if chalk_bracket:
                    # Get the chalk team at the same position in the Championship
                    chalk_team = None
                    if i < len(chalk_bracket["championship"]):
                        chalk_team = chalk_bracket["championship"][i]
                    
                    if chalk_team:
                        seed_diff = abs(int(chalk_team.get("seed", 0)) - int(team.get("seed", 0)))
                        if seed_diff > 0:
                            bonus = seed_diff * UPSET_BONUS_MULTIPLIERS["championship"]
                            team["bonus"] = int(bonus)  # Ensure it's an integer
                            print(f"Added Championship bonus of {bonus} to {team['name']} (pos {i})")
                        else:
                            team["bonus"] = 0
                
                # Skip comparison if truth team doesn't exist yet
                if not truth_team:
                    # Check if this team is in the eliminated teams set before continuing
                    if team["name"] in eliminated_teams:
                        team["classes"] += " incorrect"
                        team["correct"] = False
                        team["isEliminated"] = True
                        print(f"Marked future pick {team['name']} in Championship as eliminated")
                    continue
                
                if team["name"] == truth_team["name"] and team["seed"] == truth_team["seed"]:
                    team["classes"] += " correct"
                    team["correct"] = True
                else:
                    team["classes"] += " incorrect"
                    team["correct"] = False
                    # Add the truth team data for incorrect picks
                    if truth_team:
                        team["truthTeam"] = {
                            "name": truth_team["name"],
                            "seed": truth_team["seed"],
                            "abbrev": truth_team.get("abbrev", "")
                        }
                    
                    # Add this team to the eliminated teams set
                    eliminated_teams.add(team["name"])
            except (IndexError, KeyError, TypeError) as e:
                print(f"Error comparing Championship team at position {i}: {str(e)}")
                continue
    
    # Compare Champion
    if result_bracket["champion"]:
        if "classes" not in result_bracket["champion"]:
            result_bracket["champion"]["classes"] = ""
            
        try:
            truth_champion = truth_bracket["champion"]
            
            # Calculate potential bonus for champion regardless of truth champion
            if chalk_bracket:
                # Get the chalk champion
                chalk_team = chalk_bracket.get("champion")
                
                if chalk_team:
                    seed_diff = abs(int(chalk_team.get("seed", 0)) - int(result_bracket["champion"].get("seed", 0)))
                    if seed_diff > 0:
                        bonus = seed_diff * UPSET_BONUS_MULTIPLIERS["champion"]
                        result_bracket["champion"]["bonus"] = int(bonus)  # Ensure it's an integer
                        print(f"Added Champion bonus of {bonus} to {result_bracket['champion']['name']}")
                    else:
                        result_bracket["champion"]["bonus"] = 0
            
            # Skip comparison if truth champion doesn't exist yet
            if not truth_champion:
                # Check if this team is in the eliminated teams set before continuing
                if result_bracket["champion"] and result_bracket["champion"]["name"] in eliminated_teams:
                    result_bracket["champion"]["classes"] += " incorrect"
                    result_bracket["champion"]["correct"] = False
                    result_bracket["champion"]["isEliminated"] = True
                    print(f"Marked future pick {result_bracket['champion']['name']} as Champion as eliminated")
                return result_bracket
            
            if result_bracket["champion"]["name"] == truth_champion["name"] and result_bracket["champion"]["seed"] == truth_champion["seed"]:
                result_bracket["champion"]["classes"] += " correct"
                result_bracket["champion"]["correct"] = True
            else:
                result_bracket["champion"]["classes"] += " incorrect"
                result_bracket["champion"]["correct"] = False
                # Add the truth team data for incorrect picks
                if truth_champion:
                    result_bracket["champion"]["truthTeam"] = {
                        "name": truth_champion["name"],
                        "seed": truth_champion["seed"],
                        "abbrev": truth_champion.get("abbrev", "")
                    }
                
                # Add this team to the eliminated teams set
                eliminated_teams.add(result_bracket["champion"]["name"])
        except (KeyError, TypeError) as e:
            print(f"Error comparing Champion: {str(e)}")
            pass
    
    # Now check for impossible future picks (teams that have been eliminated)
    print(f"Eliminated teams: {eliminated_teams}")
    
    # Check regions for future rounds
    for region in ["midwest", "west", "south", "east"]:
        for round_idx in range(len(result_bracket[region])):
            # Skip first round since it's pre-filled
            if round_idx == 0:
                continue
                
            for i in range(len(result_bracket[region][round_idx])):
                team = result_bracket[region][round_idx][i]
                if team and isinstance(team, dict):
                    # Skip if team is already marked as correct or incorrect
                    if "correct" in team:
                        continue
                        
                    # Check if this team is in the eliminated teams set
                    if team["name"] in eliminated_teams:
                        team["classes"] += " incorrect"
                        team["correct"] = False
                        team["isEliminated"] = True
                        print(f"Marked future pick {team['name']} in {region} round {round_idx} as eliminated")
    
    # Check Final Four for eliminated teams
    for i in range(len(result_bracket["finalFour"])):
        team = result_bracket["finalFour"][i]
        if team and isinstance(team, dict) and "correct" not in team:
            if team["name"] in eliminated_teams:
                team["classes"] += " incorrect"
                team["correct"] = False
                team["isEliminated"] = True
                print(f"Marked future pick {team['name']} in Final Four as eliminated")
                
    # Check Championship for eliminated teams
    for i in range(len(result_bracket["championship"])):
        team = result_bracket["championship"][i]
        if team and isinstance(team, dict) and "correct" not in team:
            if team["name"] in eliminated_teams:
                team["classes"] += " incorrect"
                team["correct"] = False
                team["isEliminated"] = True
                print(f"Marked future pick {team['name']} in Championship as eliminated")
                
    # Check Champion for eliminated teams
    if result_bracket["champion"] and isinstance(result_bracket["champion"], dict) and "correct" not in result_bracket["champion"]:
        if result_bracket["champion"]["name"] in eliminated_teams:
            result_bracket["champion"]["classes"] += " incorrect"
            result_bracket["champion"]["correct"] = False
            result_bracket["champion"]["isEliminated"] = True
            print(f"Marked future pick {result_bracket['champion']['name']} as Champion as eliminated")
    
    return result_bracket

# Helper function to validate username contains only filename-safe characters
def is_valid_username(username):
    # Allow only alphanumeric, underscore, hyphen, and period
    valid_chars = re.match(r'^[a-zA-Z0-9_\-\.]+$', username) is not None
    # Ensure minimum length of 3 characters
    valid_length = len(username) >= 3
    return valid_chars and valid_length

# Helper function to extract timestamp from bracket filename
def extract_timestamp_from_filename(filename):
    """
    Extract timestamp from a bracket filename.
    
    Filename format: bracket_{username}_{YYYYMMDD}_{HHMMSS}.json
    """        # Find the last two underscores
    last_underscore = filename.rfind('_')
    second_last_underscore = filename.rfind('_', 0, last_underscore)
    if last_underscore > 0 and second_last_underscore > 0:
        # Extract date part (between second last and last underscore)
        date_part = filename[second_last_underscore+1:last_underscore]
        
        # Extract time part (after last underscore, before .json)
        time_part = filename[last_underscore+1:filename.rfind('.json')]
        
        # Check that date and time parts have expected format (8 and 6 digits)
        if len(date_part) == 8 and len(time_part) == 6 and date_part.isdigit() and time_part.isdigit():
            # Parse the timestamp using strptime
            timestamp_str = f"{date_part}_{time_part}"
            return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
    print(f"Error extracting timestamp from filename {filename}")
    return None
    


# Helper function to get the user's bracket from session, or initialize a new one if needed
def get_user_bracket():
    if 'bracket' not in session:
        session['bracket'] = initialize_bracket()
    return session['bracket']

# Helper function to update the user's bracket in the session
def update_user_bracket(new_bracket):
    session['bracket'] = new_bracket
    # Force session to save the changes by setting modified flag
    session.modified = True
    return session['bracket']

# Helper function to automatically save a user's bracket
def auto_save_bracket(bracket):
    try:
        # Get the username (or use 'anonymous' if not logged in)
        username = session.get('username', 'anonymous')
        
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_brackets/bracket_{username}_{timestamp}.json"
        
        # Write the bracket to the file
        with open(filename, 'w') as f:
            json.dump(bracket, f, indent=2)
            
        print(f"Auto-saved bracket to {filename}")
        return True
    except Exception as e:
        print(f"Error auto-saving bracket: {str(e)}")
        return False

@app.route('/')
def index():
    # When in read-only mode, redirect to users list instead of login
    if READ_ONLY_MODE and 'username' not in session:
        return redirect(url_for('users_list'))
        
    # Regular behavior: check if user is logged in
    if 'username' not in session:
        return redirect(url_for('show_login'))
    
    # Use the global read-only setting instead of URL parameter
    read_only = READ_ONLY_MODE
    
    # Check if there's a username parameter for viewing another user's bracket
    view_username = request.args.get('username')
    if view_username and view_username != session.get('username'):
        # Try to load the latest bracket for this user
        try:
            # Find latest bracket for the specified username
            latest_bracket = None
            latest_timestamp = None
            
            for file in os.listdir('saved_brackets'):
                if file.endswith('.json') and file.startswith(f"bracket_{view_username}_"):
                    file_path = os.path.join('saved_brackets', file)
                    timestamp = extract_timestamp_from_filename(file)
                    
                    if timestamp and (latest_timestamp is None or timestamp > latest_timestamp):
                        latest_timestamp = timestamp
                        latest_bracket = file
            
            if latest_bracket:
                # Set read-only mode when viewing another user's bracket, regardless of global setting
                read_only = True
                
                # Load the bracket
                file_path = os.path.join('saved_brackets', latest_bracket)
                with open(file_path, 'r') as f:
                    loaded_bracket = json.load(f)
                
                # Store original username
                original_username = session.get('username')
                
                # Temporarily set session username to viewed user
                session['username'] = view_username
                
                # Update the user's bracket in session
                update_user_bracket(loaded_bracket)
                
                # Ensure winners are updated
                updated_bracket = update_winners(session['bracket'])
                update_user_bracket(updated_bracket)
                
                # Set bracket status
                formatted_timestamp = latest_timestamp.strftime("%Y-%m-%d %I:%M %p") if latest_timestamp else "Unknown time"
                session['bracket_status'] = {
                    'type': 'viewed',
                    'timestamp': formatted_timestamp,
                    'original_username': original_username  # Keep track of original user
                }
                
                # Set read-only flag
                session['read_only'] = True
                
                print(f"Viewing {view_username}'s bracket from {formatted_timestamp} in read-only mode")
        except Exception as e:
            print(f"Error loading bracket for username {view_username}: {str(e)}")
    
    # Store read_only state in session
    session['read_only'] = read_only
    
    # Initialize user's bracket if needed
    if 'bracket' not in session:
        session['bracket'] = initialize_bracket()
    
    current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
    return render_template('index.html', current_time=current_time, username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def show_login():
    if request.method == 'POST':
        username = request.form.get('username')
        action = request.form.get('action')
        
        if not username:
            return render_template('login.html', error='Please enter your name')
            
        # Validate username contains only filename-safe characters and is at lwest 3 characters
        if not is_valid_username(username):
            # Check specific validation issue to provide appropriate error
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
                error_msg = 'Username can only contain letters, numbers, underscores, hyphens, and periods'
            elif len(username) < 3:
                error_msg = 'Username must be at least 3 characters long'
            else:
                error_msg = 'Invalid username format'
            return render_template('login.html', error=error_msg, username=username)
            
        # Check if the user has any saved brackets
        saved_files = []
        for file in os.listdir('saved_brackets'):
            if file.endswith('.json') and file.startswith("bracket_" + username + "_"):
                file_path = os.path.join('saved_brackets', file)
                saved_files.append({
                    "filename": file,
                    "created": extract_timestamp_from_filename(file),
                    "path": file_path
                })
        
        # Sort by creation time (nemidwest first)
        saved_files.sort(key=lambda x: x["created"], reverse=True)
        
        # Handle based on the selected action
        if action == 'create':
            # User wants to create a new bracket
            if saved_files:
                # Bracket with this username already exists
                return render_template('login.html', 
                                      error=f'A bracket already exists for "{username}". If that was you, please use "Load Existing Bracket" otherwise choose a different name.',
                                      username=username)
            
            # No bracket exists, we can create a new one
            session['username'] = username
            # Initialize a new bracket
            update_user_bracket(initialize_bracket())
            
            # Set bracket status to indicate this is a new bracket
            session['bracket_status'] = {
                'type': 'new',
                'timestamp': datetime.now().strftime("%Y-%m-%d %I:%M %p")
            }
            print("Bracket status: New bracket created")
            
            # Immediately save the empty bracket so we remember this user exists
            auto_save_bracket(session['bracket'])
            
            return redirect(url_for('index'))
            
        elif action == 'load':
            # User wants to load an existing bracket
            if not saved_files:
                # No bracket exists for this username
                return render_template('login.html', 
                                      error=f'No saved bracket found for "{username}". Please use "Create New Bracket" or try a different name.',
                                      username=username)
            
            # Bracket exists, we can load it
            session['username'] = username
            
            # Load the most recent bracket
            most_recent = saved_files[0]
            print(f"Loading most recent bracket for {username}: {most_recent['filename']}")
            
            try:
                # Load the bracket
                with open(most_recent['path'], 'r') as f:
                    loaded_bracket = json.load(f)
                
                # Update the user's bracket in session
                update_user_bracket(loaded_bracket)
                
                # Ensure winners are updated
                updated_bracket = update_winners(session['bracket'])
                update_user_bracket(updated_bracket)
                
                # Set bracket status to indicate this is a loaded bracket
                session['bracket_status'] = {
                    'type': 'loaded',
                    'timestamp': most_recent['created'].strftime("%Y-%m-%d %I:%M %p")
                }
                print(f"Bracket status: Loaded from {session['bracket_status']['timestamp']}")
                
                return redirect(url_for('index'))
            except Exception as e:
                # Error loading the bracket
                print(f"Error loading saved bracket for {username}: {str(e)}")
                return render_template('login.html', error=f'Error loading bracket: {str(e)}', username=username)
        else:
            # Invalid action
            return render_template('login.html', error='Please select an action', username=username)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the username from the session
    session.pop('username', None)
    # Also clear the bracket to ensure a clean slate for the next user
    session.pop('bracket', None)
    # Redirect to the login page
    return redirect(url_for('show_login'))

@app.route('/api/teams')
def get_teams():
    return jsonify(teams)

@app.route('/api/save-bracket', methods=['POST'])
def save_bracket():
    """Save the current bracket to a file."""
    try:
        # Get the user's bracket from session
        user_bracket = get_user_bracket()
        
        # Include username in the filename
        username = session.get('username', 'anonymous')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_brackets/bracket_{username}_{timestamp}.json"
        
        # Write the user's bracket to the file
        with open(filename, 'w') as f:
            json.dump(user_bracket, f, indent=2)
            
        print(f"Bracket saved to {filename}")
        
        return jsonify({"success": True, "message": f"Bracket saved to {filename}"})
    except Exception as e:
        print(f"Error saving bracket: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/saved-brackets', methods=['GET'])
def list_saved_brackets():
    """List all saved brackets for the current user."""
    try:
        # Get the current username
        username = session.get('username', 'anonymous')
        
        # Get all JSON files in the saved_brackets directory
        saved_files = []
        for file in os.listdir('saved_brackets'):
            if file.endswith('.json'):
                # Only show files for the current user
                if username in file:
                    file_path = os.path.join('saved_brackets', file)

                    
                    saved_files.append({
                        "filename": file,
                        "created": extract_timestamp_from_filename(file),
                        "path": file_path
                    })
        
        # Sort by creation time (nemidwest first)
        saved_files.sort(key=lambda x: x["created"], reverse=True)
        
        return jsonify({"success": True, "brackets": saved_files})
    except Exception as e:
        print(f"Error listing saved brackets: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/load-bracket/<filename>', methods=['GET'])
def load_bracket(filename):
    """Load a saved bracket."""
    try:
        # Security check to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        # Check that the user can access this file (simple check - does filename contain username)
        username = session.get('username', 'anonymous')
        if username not in filename and username != 'admin':  # Allow 'admin' to access any file
            return jsonify({"success": False, "error": "You don't have permission to access this file"}), 403
        
        file_path = os.path.join('saved_brackets', filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": f"File {filename} not found"}), 404
        
        # Load the bracket from the file
        with open(file_path, 'r') as f:
            loaded_bracket = json.load(f)
        
        # Update the user's bracket in session
        update_user_bracket(loaded_bracket)
        
        # Ensure winners are updated
        updated_bracket = update_winners(session['bracket'])
        update_user_bracket(updated_bracket)
        
        print(f"Loaded bracket from {file_path}")
        
        return jsonify({"success": True, "message": f"Bracket loaded from {filename}", "bracket": session['bracket']})
    except Exception as e:
        print(f"Error loading bracket: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bracket', methods=['GET', 'POST'])
def manage_bracket():
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        # Get the user's bracket from session
        user_bracket = get_user_bracket()
        
        # Flag to track if the bracket was modified and should be auto-saved
        bracket_modified = False
        
        if action == 'update':
            # Update the bracket with the selected team
            region = data.get('region')
            round_index = data.get('roundIndex')
            game_index = data.get('gameIndex')
            team_index = data.get('teamIndex')
            
            # Log for debugging
            print(f"Updating bracket: region={region}, round={round_index}, game={game_index}, team={team_index}")
            
            # Calculate the team's position in the current round
            team_position = game_index * 2 + team_index
            
            # Get the selected team from the first round or current round
            if round_index == 0:
                # First round - get team directly from the first-round arrays
                selected_team = user_bracket[region][0][team_position]
            else:
                # Later rounds - get the team from its position in the current round
                selected_team = user_bracket[region][round_index][team_position]
            
            # Determine where this team should be placed in the next round
            next_round = round_index + 1
            next_game_index = game_index // 2
            next_position = next_game_index * 2 + (game_index % 2)
            
            # Special handling for Elite Eight selections (round 3)
            if round_index == 3:
                # Handle Elite Eight to Final Four
                ff_index = -1
                if region == 'midwest':
                    ff_index = 0
                elif region == 'west':
                    ff_index = 1
                elif region == 'south':
                    ff_index = 2
                elif region == 'east':
                    ff_index = 3
                
                print(f"Elite Eight to Final Four: region={region}, ff_index={ff_index}, selected_team={selected_team['name'] if selected_team else 'None'}")
                
                if ff_index >= 0:
                    # Check if we're changing teams
                    current_ff_team = user_bracket["finalFour"][ff_index]
                    if current_ff_team != selected_team:
                        # Reset the previous team if needed
                        if current_ff_team:
                            print(f"Replacing team in Final Four slot {ff_index}: {current_ff_team['name']} with {selected_team['name']}")
                            # Check Championship for this team
                            champ_index = 0 if ff_index in [1, 2] else 1  # South/west go to slot 0, east/midwest to slot 1
                            if user_bracket["championship"][champ_index] == current_ff_team:
                                print(f"Resetting championship slot {champ_index} because team is being replaced in Final Four")
                                user_bracket["championship"][champ_index] = None
                                # Also check champion
                                if user_bracket["champion"] == current_ff_team:
                                    print(f"Resetting champion because team is being replaced in Final Four")
                                    user_bracket["champion"] = None
                        
                        # Set the new team in Final Four
                        user_bracket["finalFour"][ff_index] = selected_team
                        print(f"Set new team in Final Four slot {ff_index}: {selected_team['name'] if selected_team else 'None'}")
                        bracket_modified = True
                else:
                    print(f"Error: Invalid region {region} for Elite Eight")
            else:
                # Regular rounds - place the team in the next round
                if next_round < 4:
                    # Get the team currently in the next round slot
                    current_team = user_bracket[region][next_round][next_position] if next_position < len(user_bracket[region][next_round]) else None
                    
                    # If replacing a different team, reset all instances of that team
                    if current_team and current_team != selected_team:
                        user_bracket = reset_team_completely(user_bracket, region, current_team, next_round)
                    
                    # Place the selected team in the next round
                    user_bracket[region][next_round][next_position] = selected_team
                    bracket_modified = True
            
            # Update winners for rendering
            user_bracket = update_winners(user_bracket)
            
            # Update the session with the modified bracket
            update_user_bracket(user_bracket)
                
            # Auto-save bracket if modified
            if bracket_modified:
                auto_save_bracket(user_bracket)
                
            return jsonify(user_bracket)
        
        elif action == 'update_final_four':
            # Update the Final Four section
            region = data.get('region')
            slot_index = data.get('slotIndex')
            
            # Add validation to ensure region is not None
            if region is None:
                print("Error: region is None in update_final_four")
                return jsonify({"error": "Missing or invalid region parameter"}), 400
                
            try:
                # Get the team from the Elite Eight (round 3)
                if len(user_bracket[region][3]) == 0 or user_bracket[region][3][0] is None:
                    return jsonify({"error": f"No winner found in the Elite Eight for {region} region"}), 400
                
                # Check if Elite Eight has a winner
                elite_eight_team = None
                
                # Iterate through the first round to find the Elite Eight winner's details
                for i, team in enumerate(user_bracket[region][0]):
                    if team and (team == user_bracket[region][3][0] or (isinstance(user_bracket[region][3][0], dict) and 
                                                                  team['name'] == user_bracket[region][3][0]['name'] and 
                                                                  team['seed'] == user_bracket[region][3][0]['seed'])):
                        elite_eight_team = team
                        break
                
                if not elite_eight_team:
                    # If we can't find it in round 0, use the Elite Eight team directly
                    elite_eight_team = user_bracket[region][3][0]
                
                # Check if this will be a change
                current_team = user_bracket["finalFour"][slot_index]
                if current_team != elite_eight_team:
                    # If replacing a different team, reset that team from championship
                    if current_team:
                        # Check which championship slot to check
                        champ_index = 0 if slot_index in [1, 2] else 1  # South/west go to slot 0, east/midwest to slot 1
                        if user_bracket["championship"][champ_index] == current_team:
                            # Reset from championship
                            user_bracket["championship"][champ_index] = None
                            
                            # Also check champion
                            if user_bracket["champion"] == current_team:
                                user_bracket["champion"] = None
                
                    # Place in Final Four
                    user_bracket['finalFour'][slot_index] = elite_eight_team
                    bracket_modified = True
                
                # Update winners for rendering
                user_bracket = update_winners(user_bracket)
                
                # Update the session with the modified bracket
                update_user_bracket(user_bracket)
                
                # Auto-save bracket if modified
                if bracket_modified:
                    auto_save_bracket(user_bracket)
                    
                return jsonify(user_bracket)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error in update_final_four: {str(e)}")
                return jsonify({"error": f"Error processing Final Four update: {str(e)}"}), 400
        
        elif action == 'update_championship':
            # Update the championship section
            ff_index = data.get('ffIndex')
            slot_index = data.get('slotIndex')
            
            print(f"update_championship: ffIndex={ff_index}, slotIndex={slot_index}")
            
            try:
                if ff_index is None or ff_index < 0 or ff_index >= len(user_bracket["finalFour"]):
                    return jsonify({"error": f"Invalid Final Four index: {ff_index}"}), 400
                
                selected_team = user_bracket["finalFour"][ff_index]
                print(f"Selected team from Final Four: {selected_team}")
                
                if not selected_team:
                    return jsonify({"error": "No team found in the specified Final Four slot"}), 400
                
                # Check if this will be a change
                current_team = user_bracket["championship"][slot_index]
                if current_team != selected_team:
                    # If replacing a different team and it's the champion, reset champion
                    if current_team and user_bracket["champion"] == current_team:
                        user_bracket["champion"] = None
                        print(f"Reset champion because we're replacing it")
                
                    # Set the team in championship
                    user_bracket['championship'][slot_index] = selected_team
                    print(f"Updated championship[{slot_index}] with team {selected_team['name'] if selected_team else 'None'}")
                    bracket_modified = True
                
                # Update winners for rendering
                user_bracket = update_winners(user_bracket)
                
                # Update the session with the modified bracket
                update_user_bracket(user_bracket)
                
                # Auto-save bracket if modified
                if bracket_modified:
                    auto_save_bracket(user_bracket)
                    
                return jsonify(user_bracket)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error in update_championship: {str(e)}")
                return jsonify({"error": f"Error processing Championship update: {str(e)}"}), 400
                
        elif action == 'select_champion':
            # Set the champion from the championship round
            slot_index = data.get('slotIndex')
            
            print(f"select_champion: slotIndex={slot_index}")
            
            try:
                if slot_index not in [0, 1]:
                    return jsonify({"error": "Invalid slot index for championship"}), 400
                    
                selected_team = user_bracket["championship"][slot_index]
                print(f"Selected team from championship: {selected_team}")
                
                if not selected_team:
                    return jsonify({"error": "No team found in the specified Championship slot"}), 400
                
                # Toggle champion selection
                if user_bracket["champion"] == selected_team:
                    # Clicking on current champion deselects it
                    user_bracket["champion"] = None
                    print(f"Deselected champion")
                    bracket_modified = True
                else:
                    # Otherwise set as new champion
                    user_bracket["champion"] = selected_team
                    print(f"Set new champion: {selected_team['name']}")
                    bracket_modified = True
                
                # Update winners for rendering
                user_bracket = update_winners(user_bracket)
                
                # Update the session with the modified bracket
                update_user_bracket(user_bracket)
                
                # Auto-save bracket if modified
                if bracket_modified:
                    auto_save_bracket(user_bracket)
                    
                return jsonify(user_bracket)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error in select_champion: {str(e)}")
                return jsonify({"error": f"Error selecting champion: {str(e)}"}), 400
        
        elif action == 'auto_fill':
            # Auto-fill the bracket
            new_bracket = auto_fill_bracket(copy.deepcopy(user_bracket))
            
            # Update the session with the auto-filled bracket
            update_user_bracket(new_bracket)
            
            # Auto-save the auto-filled bracket
            auto_save_bracket(new_bracket)
                
            return jsonify(new_bracket)
        
        elif action == 'random_fill':
            # Randomly fill the bracket
            print("Starting random fill with bracket structure:", user_bracket.keys())
            new_bracket = random_fill_bracket(copy.deepcopy(user_bracket))
            
            # Log the bracket structure after random_fill
            print("After random_fill, bracket structure:", new_bracket.keys())
            print("First round structure for midwest region:", [team['name'] if team else 'None' for team in new_bracket['midwest'][0]])
            print("Sample from winners:", new_bracket['winners']['midwest'][0][:3])
            
            # Update the session with the randomly filled bracket
            update_user_bracket(new_bracket)
            
            # Auto-save the randomly filled bracket
            auto_save_bracket(new_bracket)
                
            print("Returning random filled bracket to frontend")
            return jsonify(new_bracket)
        
        elif action == 'reset':
            # Reset the bracket to initial state
            new_bracket = initialize_bracket()
            
            # Ensure winners are updated before returning
            new_bracket = update_winners(new_bracket)
            
            # Update the session with the reset bracket
            update_user_bracket(new_bracket)
            
            # Auto-save the reset bracket
            auto_save_bracket(new_bracket)
            
            # Log the updated bracket for debugging
            print('Bracket data being returned:', pretty_print_bracket(new_bracket))
            
            return jsonify(new_bracket)
            
        else:
            print(f"Unknown action: {action}")
            return jsonify({"error": "Unknown action"}), 400
    
    # GET request - return the current bracket
    # Get the user's bracket from session
    user_bracket = get_user_bracket()
    
    # Ensure winners are updated before returning
    user_bracket = update_winners(user_bracket)
    update_user_bracket(user_bracket)
    
    # If in read-only mode, compare with truth bracket
    if session.get('read_only', False):
        user_bracket = compare_with_truth(user_bracket)
    
    print('Bracket data being returned:', pretty_print_bracket(user_bracket))
    return jsonify(user_bracket)

@app.route('/api/bracket-status')
def get_bracket_status():
    """Get information about whether the current bracket is new or loaded."""
    try:
        # Return the bracket status from the session, or a default if not available
        status = session.get('bracket_status', {'type': 'unknown', 'timestamp': None})
        
        # Add read_only flag to the response
        read_only = session.get('read_only', False)
        
        # Include original username if viewing someone else's bracket
        original_username = None
        if 'original_username' in status:
            original_username = status['original_username']
        
        return jsonify({
            "success": True, 
            "status": status,
            "read_only": read_only,
            "original_username": original_username
        })
    except Exception as e:
        print(f"Error getting bracket status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/users-list')
def users_list():
    """Show a list of all users who have created brackets."""
    try:
        # In read-only mode, ensure there's a session username for viewing brackets
        if READ_ONLY_MODE and 'username' not in session:
            session['username'] = 'viewer'
            session['read_only'] = True
            
        # Get the truth bracket
        truth_bracket = get_most_recent_truth_bracket()
        
        # Get all unique usernames from saved bracket files
        users = set()
        user_data = []

        # Create "PERFECT" entry - get the truth bracket first
        if truth_bracket:
            # Use the existing compare_with_truth function to compare the truth bracket with itself
            # This will mark all teams as correct and calculate bonus points
            perfect_bracket = copy.deepcopy(truth_bracket)
            compared_bracket = compare_with_truth(perfect_bracket)
            
            # Count completed picks and extract champion
            completed_picks = 0
            champion = None
            if compared_bracket.get("champion"):
                champion = compared_bracket["champion"]["name"]
            
            # Initialize the perfect score dictionary
            perfect_score = {
                "round_1": 0, "round_2": 0, "round_3": 0,
                "final_four": 0, "championship": 0, "champion": 0,
                "total": 0,
                "round_1_score": 0, "round_2_score": 0, "round_3_score": 0,
                "final_four_score": 0, "championship_score": 0, "champion_score": 0,
                "total_score": 0,
                "round_1_bonus": 0, "round_2_bonus": 0, "round_3_bonus": 0,
                "final_four_bonus": 0, "championship_bonus": 0, "champion_bonus": 0,
                "total_bonus": 0, "total_with_bonus": 0
            }
            
            # Count regional rounds (1-3)
            for region in ["midwest", "west", "south", "east"]:
                for round_idx in range(1, 4):
                    if region not in compared_bracket or round_idx >= len(compared_bracket[region]):
                        continue
                        
                    for team in compared_bracket[region][round_idx]:
                        if not team:
                            continue
                            
                        completed_picks += 1
                        
                        if team.get("correct", False):
                            base_points, bonus_points = calculate_points_for_pick(team, round_idx)
                            
                            if round_idx == 1:
                                perfect_score["round_1"] += 1
                                perfect_score["round_1_score"] += base_points
                            elif round_idx == 2:
                                perfect_score["round_2"] += 1
                                perfect_score["round_2_score"] += base_points
                            elif round_idx == 3:
                                perfect_score["round_3"] += 1
                                perfect_score["round_3_score"] += base_points
                            
                            perfect_score["total"] += 1
                            perfect_score["total_score"] += base_points
                            
                            # Add bonus if any
                            if bonus_points > 0:
                                bonus_key = f"round_{round_idx}_bonus"
                                perfect_score[bonus_key] += bonus_points
                                perfect_score["total_bonus"] += bonus_points
            
            # Count Final Four picks
            for team in compared_bracket.get("finalFour", []):
                if not team:
                    continue
                
                completed_picks += 1
                
                if team.get("correct", False):
                    perfect_score["final_four"] += 1
                    perfect_score["total"] += 1
                    
                    if team.get("bonus", 0) > 0:
                        perfect_score["final_four_bonus"] += team["bonus"]
                        perfect_score["total_bonus"] += team["bonus"]
            
            # Count Championship picks
            for team in compared_bracket.get("championship", []):
                if not team:
                    continue
                
                completed_picks += 1
                
                if team.get("correct", False):
                    perfect_score["championship"] += 1
                    perfect_score["total"] += 1
                    
                    if team.get("bonus", 0) > 0:
                        perfect_score["championship_bonus"] += team["bonus"]
                        perfect_score["total_bonus"] += team["bonus"]
            
            # Count Champion pick
            if compared_bracket.get("champion"):
                completed_picks += 1
                
                if compared_bracket["champion"].get("correct", False):
                    perfect_score["champion"] = 1
                    perfect_score["total"] += 1
                    
                    if compared_bracket["champion"].get("bonus", 0) > 0:
                        perfect_score["champion_bonus"] = compared_bracket["champion"]["bonus"]
                        perfect_score["total_bonus"] += compared_bracket["champion"]["bonus"]
            
            # Calculate scores using the standard point values
            perfect_score["round_1_score"] = perfect_score["round_1"] * 10
            perfect_score["round_2_score"] = perfect_score["round_2"] * 20
            perfect_score["round_3_score"] = perfect_score["round_3"] * 40
            perfect_score["final_four_score"] = perfect_score["final_four"] * 80
            perfect_score["championship_score"] = perfect_score["championship"] * 120
            perfect_score["champion_score"] = perfect_score["champion"] * 160
            
            # Calculate total score
            perfect_score["total_score"] = (
                perfect_score["round_1_score"] + 
                perfect_score["round_2_score"] + 
                perfect_score["round_3_score"] + 
                perfect_score["final_four_score"] + 
                perfect_score["championship_score"] + 
                perfect_score["champion_score"]
            )
            
            # Calculate total with bonus
            perfect_score["total_with_bonus"] = perfect_score["total_score"] + perfect_score["total_bonus"]
            
            # Calculate remaining picks
            picks_remaining = 63 - completed_picks
            
            # Generate an optimal future bracket that maximizes upset potential
            optimal_future_bracket = generate_optimal_future_bracket(truth_bracket)
            
            # Score the optimal bracket using existing compare_with_truth function
            scored_optimal_bracket = compare_with_truth(optimal_future_bracket)
            
            # Calculate max possible scores from the scored optimal bracket
            max_possible_score = {
                "max_base": 0,
                "max_bonus": 0,
                "max_total": 0
            }
            
            # Calculate scores for the optimal bracket
            for region in ["midwest", "west", "south", "east"]:
                for round_idx in range(4):  # 0 to 3 (First round through Elite Eight)
                    for team_idx, team in enumerate(scored_optimal_bracket[region][round_idx]):
                        if team:
                            # Calculate base points
                            base_points, _ = calculate_points_for_pick(team, round_idx + 1)
                            max_possible_score["max_base"] += base_points
                            
                            # Add bonus if exists
                            if 'bonus' in team and team['bonus']:
                                max_possible_score["max_bonus"] += team['bonus']
            
            # Final Four
            for i, team in enumerate(scored_optimal_bracket["finalFour"]):
                if team:
                    base_points, _ = calculate_points_for_pick(team, 4)
                    max_possible_score["max_base"] += base_points
                    
                    if 'bonus' in team and team['bonus']:
                        max_possible_score["max_bonus"] += team['bonus']
            
            # Championship
            for i, team in enumerate(scored_optimal_bracket["championship"]):
                if team:
                    base_points, _ = calculate_points_for_pick(team, 5)
                    max_possible_score["max_base"] += base_points
                    
                    if 'bonus' in team and team['bonus']:
                        max_possible_score["max_bonus"] += team['bonus']
            
            # Champion
            if scored_optimal_bracket["champion"]:
                base_points, _ = calculate_points_for_pick(scored_optimal_bracket["champion"], 6)
                max_possible_score["max_base"] += base_points
                
                if 'bonus' in scored_optimal_bracket["champion"] and scored_optimal_bracket["champion"]['bonus']:
                    max_possible_score["max_bonus"] += scored_optimal_bracket["champion"]["bonus"]
            
            # Calculate total max possible points
            max_possible_score["max_total"] = max_possible_score["max_base"] + max_possible_score["max_bonus"]
            max_possible_total = max_possible_score["max_total"]
            
            # Create the perfect entry with maximum possible points
            perfect_entry = {
                "username": "PERFECT",
                "last_updated": "Current truth bracket",
                "bracket_count": 1,
                "picks_remaining": picks_remaining,
                "champion": champion,
                "correct_picks": perfect_score,
                # "max_possible_base": max_possible_score["max_base"],
                # "max_possible_bonus": max_possible_score["max_bonus"],
                # "max_possible_total": max_possible_score["max_total"],
                "max_possible_base": 1680,
                "max_possible_bonus": "-",
                "max_possible_total": "-",
                "max_possible_base_remaining": 1680 - perfect_score["total_score"],
                "max_possible_bonus_remaining": "-",
                "max_possible_total_remaining": "-",
            }
            
            # Add the perfect entry to the user data
            user_data.append(perfect_entry)
        
        # Get list of all bracket files
        for file in os.listdir('saved_brackets'):
            if file.endswith('.json') and file.startswith("bracket_"):
                # Extract username from filename (format: bracket_USERNAME_timestamp.json)
                parts = file.split('_')
                
                if len(parts) >= 3:
                    # Username is the part between "bracket_" and the timestamp
                    username = '_'.join(parts[1:-2])
                    
                    # Skip if username is empty or only contains special characters
                    if not username or username == 'anonymous':
                        continue
                    
                    if username not in users:
                        # Get the most recent file for this user
                        timestamp = extract_timestamp_from_filename(file)
                        
                        # Get number of brackets for this user
                        user_brackets = [f for f in os.listdir('saved_brackets') 
                                       if f.endswith('.json') and f.startswith(f"bracket_{username}_")]
                        
                        # Sort brackets by timestamp to find the latest one
                        sorted_brackets = []
                        for bracket_file in user_brackets:
                            bracket_timestamp = extract_timestamp_from_filename(bracket_file)
                            if bracket_timestamp:
                                sorted_brackets.append((bracket_file, bracket_timestamp))
                        
                        sorted_brackets.sort(key=lambda x: x[1], reverse=True)
                        
                        # Calculate picks remaining for latest bracket
                        picks_remaining = 63  # Default - all picks remaining
                        champion = "None"  # Default - no champion selected
                        formatted_time = "Unknown"
                        
                        if sorted_brackets:
                            latest_bracket_file = sorted_brackets[0][0]
                            formatted_time = sorted_brackets[0][1].strftime("%Y-%m-%d %I:%M %p")
                            file_path = os.path.join('saved_brackets', latest_bracket_file)
                            try:
                                with open(file_path, 'r') as f:
                                    bracket_data = json.load(f)
                                
                                # Count completed picks
                                completed_picks = 0
                                
                                # Count teams in regional rounds (rounds 1-3)
                                for region in ["midwest", "west", "south", "east"]:
                                    for round_idx in range(1, 4):
                                        for team in bracket_data[region][round_idx]:
                                            if team is not None:
                                                completed_picks += 1
                                
                                # Count Final Four picks
                                for team in bracket_data["finalFour"]:
                                    if team is not None:
                                        completed_picks += 1
                                
                                # Count Championship picks
                                for team in bracket_data["championship"]:
                                    if team is not None:
                                        completed_picks += 1
                                
                                # Count Champion
                                if bracket_data["champion"] is not None:
                                    completed_picks += 1
                                    # Extract champion name
                                    champion = bracket_data["champion"]["name"]
                                
                                # Calculate remaining picks
                                picks_remaining = 63 - completed_picks
                                
                                # Compare with truth bracket to count correct picks
                                correct_picks = {
                                    "round_1": 0,
                                    "round_2": 0,
                                    "round_3": 0,
                                    "final_four": 0,
                                    "championship": 0,
                                    "champion": 0,
                                    "total": 0,
                                    "round_1_score": 0,
                                    "round_2_score": 0,
                                    "round_3_score": 0,
                                    "final_four_score": 0,
                                    "championship_score": 0,
                                    "champion_score": 0,
                                    "total_score": 0,
                                    "round_1_bonus": 0,
                                    "round_2_bonus": 0,
                                    "round_3_bonus": 0,
                                    "final_four_bonus": 0,
                                    "championship_bonus": 0,
                                    "champion_bonus": 0,
                                    "total_bonus": 0,
                                    "total_with_bonus": 0
                                }
                                
                                # Get the truth bracket
                                if truth_bracket:
                                    # Create a copy of the user's bracket for comparison
                                    comparison_bracket = copy.deepcopy(bracket_data)
                                    
                                    # Use the compare_with_truth function to mark correct picks and calculate bonuses
                                    compared_bracket = compare_with_truth(comparison_bracket)
                                    
                                    # Count correct picks in regular rounds (1-3)
                                    for region in ["midwest", "west", "south", "east"]:
                                        for round_idx in range(1, 4):
                                            if region not in compared_bracket or round_idx >= len(compared_bracket[region]):
                                                continue
                                                
                                            for team in compared_bracket[region][round_idx]:
                                                if not team:
                                                    continue
                                                
                                                if team.get("correct", False):
                                                    base_points, bonus_points = calculate_points_for_pick(team, round_idx)
                                                    
                                                    if round_idx == 1:
                                                        correct_picks["round_1"] += 1
                                                        correct_picks["round_1_score"] += base_points
                                                    elif round_idx == 2:
                                                        correct_picks["round_2"] += 1
                                                        correct_picks["round_2_score"] += base_points
                                                    elif round_idx == 3:
                                                        correct_picks["round_3"] += 1
                                                        correct_picks["round_3_score"] += base_points
                                                    
                                                    correct_picks["total"] += 1
                                                    correct_picks["total_score"] += base_points
                                                    
                                                    # Add bonus if any
                                                    if bonus_points > 0:
                                                        bonus_key = f"round_{round_idx}_bonus"
                                                        correct_picks[bonus_key] += bonus_points
                                                        correct_picks["total_bonus"] += bonus_points
                                    
                                    # Count Final Four correct picks
                                    for team in compared_bracket.get("finalFour", []):
                                        if not team:
                                            continue
                                        
                                        if team.get("correct", False):
                                            correct_picks["final_four"] += 1
                                            correct_picks["total"] += 1
                                            
                                            if team.get("bonus", 0) > 0:
                                                correct_picks["final_four_bonus"] += team["bonus"]
                                                correct_picks["total_bonus"] += team["bonus"]
                                    
                                    # Count Championship correct picks
                                    for team in compared_bracket.get("championship", []):
                                        if not team:
                                            continue
                                        
                                        if team.get("correct", False):
                                            correct_picks["championship"] += 1
                                            correct_picks["total"] += 1
                                            
                                            if team.get("bonus", 0) > 0:
                                                correct_picks["championship_bonus"] += team["bonus"]
                                                correct_picks["total_bonus"] += team["bonus"]
                                    
                                    # Count Champion correct pick
                                    if compared_bracket.get("champion") and compared_bracket["champion"].get("correct", False):
                                        correct_picks["champion"] = 1
                                        correct_picks["total"] += 1
                                        
                                        if compared_bracket["champion"].get("bonus", 0) > 0:
                                            correct_picks["champion_bonus"] = compared_bracket["champion"]["bonus"]
                                            correct_picks["total_bonus"] += compared_bracket["champion"]["bonus"]
                            
                                # Calculate scores using standard point values
                                correct_picks["round_1_score"] = correct_picks["round_1"] * 10
                                correct_picks["round_2_score"] = correct_picks["round_2"] * 20
                                correct_picks["round_3_score"] = correct_picks["round_3"] * 40
                                correct_picks["final_four_score"] = correct_picks["final_four"] * 80
                                correct_picks["championship_score"] = correct_picks["championship"] * 120
                                correct_picks["champion_score"] = correct_picks["champion"] * 160
                                
                                # Calculate total score
                                correct_picks["total_score"] = (
                                    correct_picks["round_1_score"] + 
                                    correct_picks["round_2_score"] + 
                                    correct_picks["round_3_score"] + 
                                    correct_picks["final_four_score"] + 
                                    correct_picks["championship_score"] + 
                                    correct_picks["champion_score"]
                                )
                                
                                # Calculate total with bonus
                                correct_picks["total_with_bonus"] = correct_picks["total_score"] + correct_picks["total_bonus"]
                                
                                # Calculate maximum possible points (current + potential)
                                max_possible_base = correct_picks["total_score"]  # Start with current score
                                max_possible_bonus = correct_picks["total_bonus"]  # Start with current bonus
                                
                                # For each region, calculate potential points
                                for region in ["midwest", "west", "south", "east"]:
                                    for round_idx in range(1, 4):
                                        if region not in compared_bracket or round_idx >= len(compared_bracket[region]):
                                            continue
                                            
                                        for team in compared_bracket[region][round_idx]:
                                            # Only count teams that aren't already scored (not correct/incorrect)
                                            # and haven't been eliminated
                                            if team and team.get("correct") is None and not team.get("isEliminated", False):
                                                base, bonus = calculate_points_for_pick(team, round_idx)
                                                max_possible_base += base
                                                max_possible_bonus += bonus
                                
                                # Calculate potential points for Final Four
                                for team in compared_bracket.get("finalFour", []):
                                    if team and team.get("correct") is None and not team.get("isEliminated", False):
                                        base, bonus = calculate_points_for_pick(team, "final_four")
                                        max_possible_base += base
                                        max_possible_bonus += bonus
                                
                                # Calculate potential points for Championship
                                for team in compared_bracket.get("championship", []):
                                    if team and team.get("correct") is None and not team.get("isEliminated", False):
                                        base, bonus = calculate_points_for_pick(team, "championship")
                                        max_possible_base += base
                                        max_possible_bonus += bonus
                                
                                # Calculate potential points for Champion
                                if compared_bracket.get("champion") and compared_bracket["champion"].get("correct") is None and not compared_bracket["champion"].get("isEliminated", False):
                                    base, bonus = calculate_points_for_pick(compared_bracket["champion"], "champion")
                                    max_possible_base += base
                                    max_possible_bonus += bonus
                                
                                # Calculate total maximum possible points
                                max_possible_total = max_possible_base + max_possible_bonus

                            except Exception as e:
                                print(f"Error calculating picks for {username}: {str(e)}")
                        
                        # Add to user data
                        user_data.append({
                            "username": username,
                            "last_updated": formatted_time,
                            "bracket_count": len(user_brackets),
                            "picks_remaining": picks_remaining,
                            "champion": champion,
                            "correct_picks": correct_picks if 'correct_picks' in locals() else {
                                "round_1": 0, "round_2": 0, "round_3": 0,
                                "final_four": 0, "championship": 0, "champion": 0,
                                "total": 0,
                                "round_1_score": 0, "round_2_score": 0, "round_3_score": 0,
                                "final_four_score": 0, "championship_score": 0, "champion_score": 0,
                                "total_score": 0, 
                                "round_1_bonus": 0, "round_2_bonus": 0, "round_3_bonus": 0,
                                "final_four_bonus": 0, "championship_bonus": 0, "champion_bonus": 0,
                                "total_bonus": 0, "total_with_bonus": 0
                            },
                            "max_possible_base": max_possible_base if 'max_possible_base' in locals() else correct_picks["total_score"],
                            "max_possible_bonus": max_possible_bonus if 'max_possible_bonus' in locals() else correct_picks["total_bonus"],
                            "max_possible_total": max_possible_total if 'max_possible_total' in locals() else correct_picks["total_with_bonus"],
                            "max_possible_base_remaining": max_possible_base - correct_picks["total_score"],
                            "max_possible_bonus_remaining": max_possible_bonus - correct_picks["total_bonus"],
                            "max_possible_total_remaining": max_possible_total - correct_picks["total_with_bonus"]
                        })
                        
                        # Add to users set
                        users.add(username)
        
        # Sort user data to put PERFECT at the top, then by score
        user_data.sort(key=lambda x: (0 if x["username"] == "PERFECT" else 1, -x["correct_picks"]["total_with_bonus"]))
        
        # Add ranking to user data (handling ties)
        current_rank = 1
        previous_score = None
        skip_count = 0
        
        for i, user in enumerate(user_data):
            # Skip ranking the PERFECT row
            if user["username"] == "PERFECT":
                user["rank"] = "-"
                continue
                
            current_score = user["correct_picks"]["total_with_bonus"]
            
            if previous_score is not None and current_score != previous_score:
                # If score is different from previous, increment rank by the number of tied users plus 1
                current_rank += skip_count + 1
                skip_count = 0
            else:
                # For the first user or tied users, increment skip counter
                if previous_score is not None:
                    skip_count += 1
                    
            user["rank"] = current_rank
            previous_score = current_score
        
        return render_template('users_list.html', users=user_data, error=None)
    except Exception as e:
        # Log the error and return empty user list
        print(f"Error in users_list route: {str(e)}")
        return render_template('users_list.html', users=[], error=str(e))

# Add this function after compare_with_truth and before users_list
def generate_optimal_future_bracket(truth_bracket):
    """
    Generate a bracket that maximizes potential upset bonuses for future games.
    For games already played (in truth bracket), keep those results.
    For future games, pick teams with the highest seed number to maximize upset potential.
    Only picks from teams that are not eliminated.
    
    Args:
        truth_bracket: The current truth bracket with actual results
        
    Returns:
        A bracket with optimal future picks to maximize bonus potential
    """
    # Create a deep copy to avoid modifying the original
    optimal_bracket = copy.deepcopy(truth_bracket)
    
    # Process each region
    for region in ["midwest", "west", "south", "east"]:
        # Track teams that have been eliminated in this region
        eliminated_teams = set()
        
        # First, identify teams that have already been eliminated based on truth bracket
        for round_idx in range(4):  # Process rounds 0-3
            games_in_round = 2 ** (3 - round_idx)
            for game_idx in range(games_in_round):
                team1_idx = game_idx * 2
                team2_idx = game_idx * 2 + 1
                
                # If we have teams in this round of the truth bracket
                if round_idx < len(truth_bracket[region]) and team1_idx < len(truth_bracket[region][round_idx]) and team2_idx < len(truth_bracket[region][round_idx]):
                    team1 = truth_bracket[region][round_idx][team1_idx]
                    team2 = truth_bracket[region][round_idx][team2_idx]
                    
                    # If we have a result in the next round, one team must have been eliminated
                    if round_idx < 3:  # Not Elite Eight yet
                        next_round_idx = round_idx + 1
                        next_game_idx = game_idx // 2
                        next_team_idx = game_idx % 2
                        next_slot = next_game_idx * 2 + next_team_idx
                        
                        if (next_round_idx < len(truth_bracket[region]) and 
                            next_slot < len(truth_bracket[region][next_round_idx]) and 
                            truth_bracket[region][next_round_idx][next_slot] is not None):
                            
                            advancing_team = truth_bracket[region][next_round_idx][next_slot]
                            
                            # The other team must have been eliminated
                            if team1 and team2:
                                if team1["name"] == advancing_team["name"]:
                                    eliminated_teams.add(team2["name"])
                                elif team2["name"] == advancing_team["name"]:
                                    eliminated_teams.add(team1["name"])
        
        # Now fill in future games, starting from the earliest incomplete round
        for round_idx in range(4):
            games_in_round = 2 ** (3 - round_idx)
            
            for game_idx in range(games_in_round):
                # For each game position
                next_round_idx = round_idx + 1
                next_game_idx = game_idx // 2
                next_team_idx = game_idx % 2
                next_slot = next_game_idx * 2 + next_team_idx
                
                # Check if this position feeds into a position that's not yet decided in the truth bracket
                if (round_idx < 3 and  # Not Elite Eight
                    next_round_idx < len(truth_bracket[region]) and
                    next_slot < len(truth_bracket[region][next_round_idx]) and
                    truth_bracket[region][next_round_idx][next_slot] is None):
                    
                    # This is a future game - get the two teams in the current matchup
                    team1_idx = game_idx * 2
                    team2_idx = game_idx * 2 + 1
                    
                    if team1_idx < len(optimal_bracket[region][round_idx]) and team2_idx < len(optimal_bracket[region][round_idx]):
                        team1 = optimal_bracket[region][round_idx][team1_idx]
                        team2 = optimal_bracket[region][round_idx][team2_idx]
                        
                        # Skip if either team is missing
                        if not team1 or not team2:
                            continue
                            
                        # Skip if both teams are eliminated
                        if team1["name"] in eliminated_teams and team2["name"] in eliminated_teams:
                            continue
                            
                        # If only one team is not eliminated, that team advances
                        if team1["name"] in eliminated_teams:
                            optimal_bracket[region][next_round_idx][next_slot] = team2
                            continue
                        if team2["name"] in eliminated_teams:
                            optimal_bracket[region][next_round_idx][next_slot] = team1
                            continue
                        
                        # Both teams are available - choose the one with higher seed number (bigger upset potential)
                        if int(team1["seed"]) > int(team2["seed"]):
                            optimal_bracket[region][next_round_idx][next_slot] = team1
                        else:
                            optimal_bracket[region][next_round_idx][next_slot] = team2
    
    # Process Elite Eight to Final Four
    for region in ["midwest", "west", "south", "east"]:
        # Find which Final Four slot this region feeds into
        ff_idx = 0 if region == "midwest" else 1 if region == "west" else 2 if region == "south" else 3
        
        # Skip if this Final Four position is already filled in truth bracket
        if truth_bracket["finalFour"][ff_idx] is not None:
            continue
            
        # Get the Elite Eight teams for this region
        elite_eight_teams = []
        if optimal_bracket[region][3][0] is not None:
            elite_eight_teams.append(optimal_bracket[region][3][0])
        if optimal_bracket[region][3][1] is not None:
            elite_eight_teams.append(optimal_bracket[region][3][1])
            
        # Pick the team with highest seed number that advances
        if elite_eight_teams:
            best_upset_team = max(elite_eight_teams, key=lambda team: int(team["seed"]))
            optimal_bracket["finalFour"][ff_idx] = best_upset_team
    
    # Process Final Four to Championship
    # First semifinal: slots 0 and 1 of finalFour feed into championship[0]
    if truth_bracket["championship"][0] is None:
        semifinal1_teams = []
        if optimal_bracket["finalFour"][0] is not None:
            semifinal1_teams.append(optimal_bracket["finalFour"][0])
        if optimal_bracket["finalFour"][1] is not None:
            semifinal1_teams.append(optimal_bracket["finalFour"][1])
            
        if semifinal1_teams:
            best_upset_team = max(semifinal1_teams, key=lambda team: int(team["seed"]))
            optimal_bracket["championship"][0] = best_upset_team
    
    # Second semifinal: slots 2 and 3 of finalFour feed into championship[1]
    if truth_bracket["championship"][1] is None:
        semifinal2_teams = []
        if optimal_bracket["finalFour"][2] is not None:
            semifinal2_teams.append(optimal_bracket["finalFour"][2])
        if optimal_bracket["finalFour"][3] is not None:
            semifinal2_teams.append(optimal_bracket["finalFour"][3])
            
        if semifinal2_teams:
            best_upset_team = max(semifinal2_teams, key=lambda team: int(team["seed"]))
            optimal_bracket["championship"][1] = best_upset_team
    
    # Process Championship to Champion
    if truth_bracket["champion"] is None:
        championship_teams = []
        if optimal_bracket["championship"][0] is not None:
            championship_teams.append(optimal_bracket["championship"][0])
        if optimal_bracket["championship"][1] is not None:
            championship_teams.append(optimal_bracket["championship"][1])
            
        if championship_teams:
            best_upset_team = max(championship_teams, key=lambda team: int(team["seed"]))
            optimal_bracket["champion"] = best_upset_team
    
    return optimal_bracket

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port) 