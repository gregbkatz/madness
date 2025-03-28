from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from data.teams import teams
from datetime import datetime
from bracket_logic import initialize_bracket, select_team, auto_fill_bracket, pretty_print_bracket, update_winners, random_fill_bracket, reset_team_completely
from utils.scoring import compare_with_truth, calculate_points_for_pick, get_correct_picks_and_scores
from utils.bracket_utils import get_sorted_truth_files
import json
import os
import copy
import re
import sys
import argparse
import glob  # For finding truth bracket files
import traceback

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
def get_most_recent_truth_bracket(index=0):
    """
    Find and load a truth bracket file by index.
    Index 0 is the most recent file, higher indexes are older files.
    
    Args:
        index (int): The index of the truth file to load (0 = newest)
        
    Returns:
        dict: The loaded bracket data or None if no files exist or an error occurs
    """
    try:
        # Get all sorted truth files
        truth_files = get_sorted_truth_files()
        
        if not truth_files:
            return None
        
        # Check if the requested index is valid
        if index < 0 or index >= len(truth_files):
            # If invalid, default to the most recent
            index = 0
            
        # Load the requested file
        print(f"Loading truth bracket file: {index}, {truth_files[index]}")
        with open(truth_files[index], 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading truth bracket: {str(e)}")
        return None

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
    # When in read-only mode, redirect to leaderboard instead of login
    try:
        if READ_ONLY_MODE and 'username' not in session:
            return redirect('/users-list')
        
        if 'username' not in session:
            return redirect('/login')
            
        # Get username from URL query param if provided (for viewing other users' brackets)
        display_username = request.args.get('username')
        
        if not display_username:
            display_username = session['username']
            viewing_own_bracket = True
        else:
            viewing_own_bracket = (display_username == session['username'])
            
        # Get truth files for timeline
        all_truth_files = get_sorted_truth_files()
        
        # Get the selected truth file index
        selected_index = request.args.get('truth_index', None)
        
        # If a specific index was requested in the URL, use it
        if selected_index is not None:
            try:
                selected_index = int(selected_index)
                if selected_index < 0 or selected_index >= len(all_truth_files):
                    selected_index = 0
            except ValueError:
                selected_index = 0
                
            # Store in session for subsequent requests
            session['selected_truth_index'] = selected_index
        # Otherwise use the value from session, defaulting to 0 (newest)
        else:
            selected_index = session.get('selected_truth_index', 0)
            
            # Validate the index is still in range
            if selected_index < 0 or selected_index >= len(all_truth_files):
                selected_index = 0
                session['selected_truth_index'] = selected_index
                
        # Get the truth bracket based on the selected index
        truth_bracket = get_most_recent_truth_bracket(selected_index)
        
        # Format truth filenames for display
        truth_file_names = []
        for file_path in all_truth_files:
            # Extract just the filename without the directory path
            filename = os.path.basename(file_path)
            truth_file_names.append(filename)
        
        # Get read-only flag from session
        is_read_only = session.get('read_only', False)
        
        # Get user bracket data
        if viewing_own_bracket and not is_read_only:
            user_bracket = get_user_bracket()
        else:
            # Load another user's bracket
            # Find the most recent bracket file for the requested user
            bracket_files = []
            for f in os.listdir('saved_brackets'):
                if f.startswith(f'bracket_{display_username}_') and f.endswith('.json'):
                    # Extract the username from the filename to ensure exact match
                    parts = f.split('_')
                    if len(parts) >= 4:  # We need at least 4 parts: bracket, username parts, date, time
                        file_username = '_'.join(parts[1:-2])
                        if file_username == display_username:
                            bracket_files.append(f)
            
            if not bracket_files:
                return render_template('error.html', error=f"No bracket found for user {display_username}")
                
            # Sort by timestamp (newest first)
            bracket_files.sort(key=lambda x: extract_timestamp_from_filename(x), reverse=True)
            newest_file = bracket_files[0]
            
            try:
                with open(os.path.join('saved_brackets', newest_file), 'r') as f:
                    user_bracket = json.load(f)
            except Exception as e:
                return render_template('error.html', error=f"Error loading bracket: {str(e)}")
                
        # Compare user bracket with truth data
        if truth_bracket:
            # Create a copy of the user's bracket to avoid modifying the original
            compared_bracket = copy.deepcopy(user_bracket)
            
            # Mark correct and incorrect picks
            compared_bracket = compare_with_truth(compared_bracket, truth_bracket)
            
            # Use the compared bracket for display
            user_bracket = compared_bracket
            
        return render_template('index.html', 
                             username=display_username, 
                             viewing_own=viewing_own_bracket,
                             truth_file_names=truth_file_names,
                             selected_index=selected_index,
                             current_truth_file=truth_file_names[selected_index] if truth_file_names else None)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', error=str(e))

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
    """
    API endpoint for managing bracket data.
    GET: Return the current user's bracket or the selected user's bracket
    POST: Update the current user's bracket
    """
    # For GET requests, return the current bracket
    if request.method == 'GET':
        try:
            # Check if we're in read-only mode
            read_only = session.get('read_only', False)
            
            # Get the username from the query parameters
            username = request.args.get('username')
            
            # Check if truth_index is provided for AJAX requests
            truth_index_str = request.args.get('truth_index')
            if truth_index_str:
                try:
                    truth_index = int(truth_index_str)
                    # Store the correct index in the session
                    session['selected_truth_index'] = truth_index
                    print(f"Updated selected truth index to {truth_index}")
                except ValueError:
                    truth_index = session.get('selected_truth_index', 0)
                    print(f"Invalid truth index provided, using {truth_index}")
            else:
                truth_index = session.get('selected_truth_index', 0)
                print(f"Using existing truth index: {truth_index}")
                
            # Get the truth bracket for comparison
            truth_bracket = get_most_recent_truth_bracket(truth_index)
            
            # Log which truth file is being loaded
            truth_files = get_sorted_truth_files()
            if truth_files and truth_index < len(truth_files):
                print(f"Loading truth bracket file: {truth_index}, {truth_files[truth_index]}")
            else:
                print(f"No truth file found for index {truth_index}")
            
            # If username is provided and in read-only mode, load that user's bracket
            viewing_own_bracket = True
            if username and read_only:
                try:
                    user_bracket = get_user_bracket_for_user(username)
                    viewing_own_bracket = (username == session.get('username'))
                    print(f"Loaded bracket for user: {username}")
                except Exception as e:
                    print(f"Error loading {username}'s bracket: {str(e)}")
                    # On error, fall back to current user's bracket
                    user_bracket = get_user_bracket()
                    print(f"Falling back to current user bracket")
            else:
                # Otherwise, get the current user's bracket
                user_bracket = get_user_bracket()
                print(f"Loaded current user bracket")
                
            # Compare with truth bracket if available
            if truth_bracket:
                comparison_data = compare_with_truth(user_bracket, truth_bracket)
                print(f"Compared bracket with truth data")
            else:
                comparison_data = None
                print(f"No truth data available for comparison")
                
            # Prepare the response data
            response_data = {
                'bracket': user_bracket,
                'truth_data': comparison_data,
                'viewing_own_bracket': viewing_own_bracket,
                'read_only': read_only
            }
            return jsonify(response_data)
                
        except Exception as e:
            import traceback
            print(f"Error in API bracket GET: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
            
    # For POST requests, update the bracket
    elif request.method == 'POST':
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
        # Get the selected truth bracket index from session or default to 0
        selected_index = session.get('selected_truth_index', 0)
        # Get the appropriate truth bracket
        truth_bracket = get_most_recent_truth_bracket(selected_index)
        # Compare the user's bracket with the selected truth bracket
        user_bracket = compare_with_truth(user_bracket, truth_bracket)
    
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

def format_percentage(value):
    """Format a percentage value to 1 decimal place."""
    if value > 0 and value < 0.5:
        return 0.1
    else: 
        return round(value, 0)

def add_mc_data(truth_file, user_data):
    # Load Monte Carlo analysis data if available
    monte_carlo_data = {}
    if truth_file:
        # Find the Monte Carlo analysis file
        analysis_file = find_monte_carlo_analysis(truth_file)
        print("analysis_file", analysis_file)
        if analysis_file and os.path.exists(analysis_file):
            try:
                with open(analysis_file, 'r') as f:
                    monte_carlo_data = json.load(f)
                print(f"Loaded Monte Carlo data from: {analysis_file}")
            except Exception as e:
                print(f"Error loading Monte Carlo data: {str(e)}")
        else:
            print("No Monte Carlo analysis file found")
    
    # Add Monte Carlo data to user data if available
    if monte_carlo_data:
        for user in user_data:
            username = user['username']
            if username in monte_carlo_data:
                user_stats = monte_carlo_data[username]
                # Add min score from the Monte Carlo data
                user['monte_carlo_pct_first_place'] = format_percentage(user_stats.get('pct_first_place', 0))
                user['monte_carlo_min_rank'] = user_stats.get('min_rank', 0)
                user['monte_carlo_max_rank'] = user_stats.get('max_rank', 0)
                user['monte_carlo_min_score'] = user_stats.get('min_score', 0)
                user['monte_carlo_max_score'] = user_stats.get('max_score', 0)
    return user_data, bool(monte_carlo_data)

def get_users_list(truth_bracket):
    """
    Process and return user data with scores based on the provided truth bracket.
    
    Args:
        truth_bracket: The truth bracket to compare user brackets against
        
    Returns:
        list: List of user data dictionaries with scores and rankings
    """
    # Get all unique usernames from saved bracket files
    users = set()
    user_data = []

    # Create "PERFECT" entry - get the truth bracket first
    if truth_bracket:
        # Use the existing compare_with_truth function to compare the truth bracket with itself
        # This will mark all teams as correct and calculate bonus points
        perfect_bracket = copy.deepcopy(truth_bracket)
        compared_bracket = compare_with_truth(perfect_bracket, truth_bracket)
        
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
        scored_optimal_bracket = compare_with_truth(optimal_future_bracket, truth_bracket)
        
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
            "monte_carlo_pct_first_place": 0,
            "monte_carlo_min_rank": 0,
            "monte_carlo_max_rank": 0,
            "monte_carlo_min_score": 0,
            "monte_carlo_max_score": 0,
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
                            
                  
                            
                            # Get the truth bracket
                            if truth_bracket:
                                # Create a copy of the user's bracket for comparison
                                comparison_bracket = copy.deepcopy(bracket_data)
                                
                                # Use the compare_with_truth function to mark correct picks and calculate bonuses
                                compared_bracket = compare_with_truth(comparison_bracket, truth_bracket)

                            correct_picks = get_correct_picks_and_scores(compared_bracket) 
                               
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
                        "max_possible_total_remaining": max_possible_total - correct_picks["total_with_bonus"],
                        "monte_carlo_pct_first_place": 0,
                        "monte_carlo_min_rank": 0,
                        "monte_carlo_max_rank": 0,
                        "monte_carlo_min_score": 0,
                        "monte_carlo_max_score": 0
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
    
    return user_data

@app.route('/users-list')
def users_list():
    """Show the leaderboard with all users who have created brackets."""
    try:
        # In read-only mode, ensure there's a session username for viewing brackets
        if READ_ONLY_MODE and 'username' not in session:
            session['username'] = 'viewer'
            session['read_only'] = True
        
        # Get all truth files for the slider
        all_truth_files = get_sorted_truth_files()
        
        # Get the selected truth file index from the session or request
        selected_index = request.args.get('truth_index', None)
        
        # If a specific index was requested in the URL, use it and store in session
        if selected_index is not None:
            try:
                selected_index = int(selected_index)
                if selected_index < 0 or selected_index >= len(all_truth_files):
                    selected_index = 0
            except ValueError:
                selected_index = 0
            
            # Store in session for subsequent requests
            session['selected_truth_index'] = selected_index
        # Otherwise use the value from session, defaulting to 0 (newest)
        else:
            selected_index = session.get('selected_truth_index', 0)
            
            # Validate the index is still in range (in case files were added/removed)
            if selected_index < 0 or selected_index >= len(all_truth_files):
                selected_index = 0
                session['selected_truth_index'] = selected_index
        
        # Get the truth bracket based on the selected index
        truth_bracket = get_most_recent_truth_bracket(selected_index)
        truth_file = all_truth_files[selected_index] if all_truth_files else None
        
        # Format truth filenames for display in the slider
        truth_file_names = []
        for file_path in all_truth_files:
            # Extract just the filename without the directory path
            filename = os.path.basename(file_path)
            truth_file_names.append(filename)
        
        # Process user data with the extracted function
        user_data = get_users_list(truth_bracket)
        user_data, mc_data_found = add_mc_data(truth_file, user_data)
        
        return render_template('users_list.html', 
                              users=user_data, 
                              error=None, 
                              truth_file_names=truth_file_names,
                              selected_index=selected_index,
                              current_truth_file=truth_file_names[selected_index] if truth_file_names else None,
                              monte_carlo_available=mc_data_found)
    except Exception as e:
        # Log the error and return empty user list
        print(f"Error in users_list route: {str(e)}")
        return render_template('users_list.html', users=[], error=str(e))

def find_monte_carlo_analysis(truth_file):
    """
    Find the Monte Carlo analysis file for a given truth file.
    Selects the file with the largest number of brackets if multiple are available.
    
    Args:
        truth_file (str): Path to the truth file
        
    Returns:
        str: Path to the analysis file, or None if not found
    """
    try:
        # Extract the identifier from the truth file
        basename = os.path.basename(truth_file)
        
        # Handle new format "round_x_game_y - {seed} {winner} defeats {seed} {loser}.json"
        if ' defeats ' in basename:
            # Extract just the round_X_game_Y part
            match = re.search(r'(round_\d+_game_\d+)', basename)
            if match:
                truth_id = match.group(1)
            else:
                return None
        # Handle old format "round_x_game_y.json"
        elif basename.startswith("round_") and "_game_" in basename:
            # Extract the round_X_game_Y part
            truth_id = os.path.splitext(basename)[0]  # Remove extension
            # If there are additional parts after game_Y, remove them
            if '_' in truth_id[truth_id.index('_game_') + 6:]:
                parts = truth_id.split('_')
                truth_id = f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}"
        else:
            return None
            
        # Look for analysis files in data/simulations
        simulations_dir = "data/simulations"
        if not os.path.exists(simulations_dir):
            return None
            
        # Check for files with pattern: analysis_{truth_id}_{count}_brackets.json
        analysis_files = []
        for filename in os.listdir(simulations_dir):
            if filename.startswith(f"analysis_{truth_id}_") and filename.endswith("_brackets.json"):
                filepath = os.path.join(simulations_dir, filename)
                
                # Try to extract the count from the filename
                # Expected pattern: analysis_round_X_game_Y_Z_brackets.json where Z is the count
                count = 0
                try:
                    # Split by underscore and extract the part before "_brackets.json"
                    parts = filename.split('_')
                    if len(parts) >= 5:  # Should have at least analysis_round_X_game_Y_Z
                        # The count should be the second-to-last part
                        count_str = parts[-2]
                        count = int(count_str)
                except Exception:
                    # If we can't parse the count, assume it's 0
                    count = 0
                
                # Store the file path, count, and modification time
                file_info = {
                    'path': filepath,
                    'count': count,
                    'mtime': os.path.getmtime(filepath)
                }
                analysis_files.append(file_info)
                
        # If we found files, return the one with the largest count
        # If there are multiple with the same count, choose the most recent
        if analysis_files:
            # Sort by count (descending) and then by modification time (descending)
            analysis_files.sort(key=lambda x: (-x['count'], -x['mtime']))
            print(f"Using Monte Carlo analysis with {analysis_files[0]['count']} brackets")
            return analysis_files[0]['path']
            
        return None
    except Exception as e:
        print(f"Error finding Monte Carlo analysis: {str(e)}")
        traceback.print_exc()  # Print traceback for easier debugging
        return None

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

# Import for scores service
from services.scores_service import ScoresService

@app.route('/scores')
def scores():
    """Display live basketball scores from ESPN API."""
    try:
        # Create scores service
        scores_service = ScoresService()
        
        # Get scores data
        scores_data = scores_service.get_tournament_scores()
        
        # Check for errors
        if 'error' in scores_data:
            return render_template('scores.html', error=scores_data['error'])
        
        # Format the last_updated timestamp for display
        if 'last_updated' in scores_data:
            try:
                dt = datetime.fromisoformat(scores_data['last_updated'])
                scores_data['last_updated'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                pass  # Keep original format if parsing fails
        
        return render_template('scores.html', scores=scores_data)
    except Exception as e:
        print(f"Error getting scores: {str(e)}")
        return render_template('scores.html', error=str(e))

@app.route('/api/user-scores', methods=['GET'])
def api_user_scores():
    """API endpoint that returns user scores for a specific truth bracket index."""
    try:
        # Get truth index from query param
        truth_index = request.args.get('truth_index', type=int, default=0)
        
        # Get all truth files to validate index
        all_truth_files = get_sorted_truth_files()
        if not all_truth_files:
            return jsonify({'error': 'No truth bracket files found'}), 404
            
        # Validate index
        if truth_index < 0 or truth_index >= len(all_truth_files):
            return jsonify({'error': f'Invalid truth index: {truth_index}. Valid range is 0-{len(all_truth_files)-1}'}), 400
        
        # Get truth bracket for the specified index
        truth_bracket = get_most_recent_truth_bracket(truth_index)
        if not truth_bracket:
            return jsonify({'error': f'Could not load truth bracket for index {truth_index}'}), 500
        
        # Get users list with scores
        users_list = get_users_list(truth_bracket)
        truth_file = all_truth_files[truth_index] if all_truth_files else None
        users_list, _ = add_mc_data(truth_file, users_list)

        if users_list is None:
            return jsonify({'error': 'Could not generate users list'}), 500
        
        # Wrap users list in 'users' property to match what the JavaScript expects
        return jsonify({'users': users_list})
    
    except Exception as e:
        app.logger.error(f"Error in api_user_scores: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/update-truth-index', methods=['POST'])
def api_update_truth_index():
    """API endpoint to update the session's selected truth index."""
    try:
        # Get truth index from query param
        truth_index = request.args.get('index', type=int, default=0)
        
        # Get all truth files to validate index
        all_truth_files = get_sorted_truth_files()
        if not all_truth_files:
            return jsonify({'error': 'No truth bracket files found'}), 404
            
        # Validate index
        if truth_index < 0 or truth_index >= len(all_truth_files):
            return jsonify({'error': f'Invalid truth index: {truth_index}. Valid range is 0-{len(all_truth_files)-1}'}), 400
        
        # Update session
        session['selected_truth_index'] = truth_index
        
        return jsonify({'success': True, 'message': f'Truth index updated to {truth_index}'})
    
    except Exception as e:
        app.logger.error(f"Error in api_update_truth_index: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def get_user_bracket_for_user(username):
    """Load a bracket for a specific user by username"""
    try:
        # Find the most recent bracket file for the requested user
        bracket_files = []
        for f in os.listdir('saved_brackets'):
            if f.startswith(f'bracket_{username}_') and f.endswith('.json'):
                # Extract the username from the filename to ensure exact match
                parts = f.split('_')
                if len(parts) >= 4:  # We need at least 4 parts: bracket, username parts, date, time
                    file_username = '_'.join(parts[1:-2])
                    if file_username == username:
                        bracket_files.append(f)
        
        if not bracket_files:
            print(f"No bracket file found for user: {username}")
            return None
        
        # Sort by timestamp (newest first)
        bracket_files.sort(key=lambda x: extract_timestamp_from_filename(x), reverse=True)
        newest_file = bracket_files[0]
        bracket_file = os.path.join('saved_brackets', newest_file)
        
        print(f"Found bracket file for user: {username} - {newest_file}")
        
        with open(bracket_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading bracket for user {username}: {str(e)}")
        raise

def save_rankings(rankings, output_file):
    """
    Save rankings to a JSON file.
    
    Args:
        rankings (dict): Dictionary of rankings data
        output_file (str): Path to save the rankings
    """
    with open(output_file, 'w') as f:
        json.dump(rankings, f, indent=2)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port) 