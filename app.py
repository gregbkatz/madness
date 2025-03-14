from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from data.teams import teams
from datetime import datetime
from bracket_logic import initialize_bracket, select_team, auto_fill_bracket, pretty_print_bracket, update_winners, random_fill_bracket, reset_team_completely
import json
import os
import copy

app = Flask(__name__)
app.secret_key = 'march_madness_simple_key'  # Secret key for session

# Store the bracket in server memory (in a real app, this would be in a database)
bracket = initialize_bracket()

# Ensure the saved_brackets directory exists
os.makedirs('saved_brackets', exist_ok=True)

@app.route('/')
def index():
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('show_login'))
    
    current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
    return render_template('index.html', current_time=current_time, username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def show_login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Please enter your name')
    return render_template('login.html')

@app.route('/api/teams')
def get_teams():
    return jsonify(teams)

@app.route('/api/save-bracket', methods=['POST'])
def save_bracket():
    """Save the current bracket to a file."""
    try:
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saved_brackets/bracket_{timestamp}.json"
        
        # Write the current bracket to the file
        with open(filename, 'w') as f:
            json.dump(bracket, f, indent=2)
            
        print(f"Bracket saved to {filename}")
        
        return jsonify({"success": True, "message": f"Bracket saved to {filename}"})
    except Exception as e:
        print(f"Error saving bracket: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/saved-brackets', methods=['GET'])
def list_saved_brackets():
    """List all saved brackets."""
    try:
        # Get all JSON files in the saved_brackets directory
        saved_files = []
        for file in os.listdir('saved_brackets'):
            if file.endswith('.json'):
                # Get file creation time
                file_path = os.path.join('saved_brackets', file)
                created_time = datetime.fromtimestamp(os.path.getctime(file_path))
                readable_time = created_time.strftime("%Y-%m-%d %H:%M:%S")
                
                saved_files.append({
                    "filename": file,
                    "created": readable_time,
                    "path": file_path
                })
        
        # Sort by creation time (newest first)
        saved_files.sort(key=lambda x: x["created"], reverse=True)
        
        return jsonify({"success": True, "brackets": saved_files})
    except Exception as e:
        print(f"Error listing saved brackets: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/load-bracket/<filename>', methods=['GET'])
def load_bracket(filename):
    """Load a saved bracket."""
    global bracket
    
    try:
        # Security check to prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        file_path = os.path.join('saved_brackets', filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({"success": False, "error": f"File {filename} not found"}), 404
        
        # Load the bracket from the file
        with open(file_path, 'r') as f:
            loaded_bracket = json.load(f)
        
        # Update the global bracket
        bracket = loaded_bracket
        
        # Ensure winners are updated
        bracket = update_winners(bracket)
        
        print(f"Loaded bracket from {file_path}")
        
        return jsonify({"success": True, "message": f"Bracket loaded from {filename}", "bracket": bracket})
    except Exception as e:
        print(f"Error loading bracket: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bracket', methods=['GET', 'POST'])
def manage_bracket():
    global bracket
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
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
                selected_team = bracket[region][0][team_position]
            else:
                # Later rounds - get the team from its position in the current round
                selected_team = bracket[region][round_index][team_position]
            
            # Determine where this team should be placed in the next round
            next_round = round_index + 1
            next_game_index = game_index // 2
            next_position = next_game_index * 2 + (game_index % 2)
            
            # Special handling for Elite Eight selections (round 3)
            if round_index == 3:
                # Handle Elite Eight to Final Four
                ff_index = -1
                if region == 'west':
                    ff_index = 0
                elif region == 'east':
                    ff_index = 1
                elif region == 'south':
                    ff_index = 2
                elif region == 'midwest':
                    ff_index = 3
                
                print(f"Elite Eight to Final Four: region={region}, ff_index={ff_index}, selected_team={selected_team['name'] if selected_team else 'None'}")
                
                if ff_index >= 0:
                    # Check if we're changing teams
                    current_ff_team = bracket["finalFour"][ff_index]
                    if current_ff_team != selected_team:
                        # Reset the previous team if needed
                        if current_ff_team:
                            print(f"Replacing team in Final Four slot {ff_index}: {current_ff_team['name']} with {selected_team['name']}")
                            # Check Championship for this team
                            champ_index = 0 if ff_index in [1, 2] else 1  # South/East go to slot 0, Midwest/West to slot 1
                            if bracket["championship"][champ_index] == current_ff_team:
                                print(f"Resetting championship slot {champ_index} because team is being replaced in Final Four")
                                bracket["championship"][champ_index] = None
                                # Also check champion
                                if bracket["champion"] == current_ff_team:
                                    print(f"Resetting champion because team is being replaced in Final Four")
                                    bracket["champion"] = None
                        
                        # Set the new team in Final Four
                        bracket["finalFour"][ff_index] = selected_team
                        print(f"Set new team in Final Four slot {ff_index}: {selected_team['name'] if selected_team else 'None'}")
                else:
                    print(f"Error: Invalid region {region} for Elite Eight")
            else:
                # Regular rounds - place the team in the next round
                if next_round < 4:
                    # Get the team currently in the next round slot
                    current_team = bracket[region][next_round][next_position] if next_position < len(bracket[region][next_round]) else None
                    
                    # If replacing a different team, reset all instances of that team
                    if current_team and current_team != selected_team:
                        bracket = reset_team_completely(bracket, region, current_team, next_round)
                    
                    # Place the selected team in the next round
                    bracket[region][next_round][next_position] = selected_team
            
            # Update winners for rendering
            bracket = update_winners(bracket)
            
            # Save the updated bracket
            with open('bracket.json', 'w') as f:
                json.dump(bracket, f)
                
            return jsonify(bracket)
        
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
                if len(bracket[region][3]) == 0 or bracket[region][3][0] is None:
                    return jsonify({"error": f"No winner found in the Elite Eight for {region} region"}), 400
                
                # Check if Elite Eight has a winner
                elite_eight_team = None
                
                # Iterate through the first round to find the Elite Eight winner's details
                for i, team in enumerate(bracket[region][0]):
                    if team and (team == bracket[region][3][0] or (isinstance(bracket[region][3][0], dict) and 
                                                                  team['name'] == bracket[region][3][0]['name'] and 
                                                                  team['seed'] == bracket[region][3][0]['seed'])):
                        elite_eight_team = team
                        break
                
                if not elite_eight_team:
                    # If we can't find it in round 0, use the Elite Eight team directly
                    elite_eight_team = bracket[region][3][0]
                
                # Check if this will be a change
                current_team = bracket["finalFour"][slot_index]
                if current_team != elite_eight_team:
                    # If replacing a different team, reset that team from championship
                    if current_team:
                        # Check which championship slot to check
                        champ_index = 0 if slot_index in [1, 2] else 1  # South/East go to slot 0, Midwest/West to slot 1
                        if bracket["championship"][champ_index] == current_team:
                            # Reset from championship
                            bracket["championship"][champ_index] = None
                            
                            # Also check champion
                            if bracket["champion"] == current_team:
                                bracket["champion"] = None
                
                # Place in Final Four
                bracket['finalFour'][slot_index] = elite_eight_team
                
                # Update winners for rendering
                bracket = update_winners(bracket)
                
                # Save the updated bracket
                with open('bracket.json', 'w') as f:
                    json.dump(bracket, f)
                    
                return jsonify(bracket)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error in update_final_four: {str(e)}")
                return jsonify({"error": f"Error processing Final Four update: {str(e)}"}), 400
        
        elif action == 'update_championship':
            # Update the championship section
            ff_index = data.get('ffIndex')
            slot_index = data.get('slotIndex')
            
            print(f"update_championship: ffIndex={ff_index}, slotIndex={slot_index}")
            
            try:
                if ff_index is None or ff_index < 0 or ff_index >= len(bracket["finalFour"]):
                    return jsonify({"error": f"Invalid Final Four index: {ff_index}"}), 400
                
                selected_team = bracket["finalFour"][ff_index]
                print(f"Selected team from Final Four: {selected_team}")
                
                if not selected_team:
                    return jsonify({"error": "No team found in the specified Final Four slot"}), 400
                
                # Check if this will be a change
                current_team = bracket["championship"][slot_index]
                if current_team != selected_team:
                    # If replacing a different team and it's the champion, reset champion
                    if current_team and bracket["champion"] == current_team:
                        bracket["champion"] = None
                        print(f"Reset champion because we're replacing it")
                
                # Set the team in championship
                bracket['championship'][slot_index] = selected_team
                print(f"Updated championship[{slot_index}] with team {selected_team['name'] if selected_team else 'None'}")
                
                # Update winners for rendering
                bracket = update_winners(bracket)
                
                # Save the updated bracket
                with open('bracket.json', 'w') as f:
                    json.dump(bracket, f)
                    
                return jsonify(bracket)
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
                    
                selected_team = bracket["championship"][slot_index]
                print(f"Selected team from championship: {selected_team}")
                
                if not selected_team:
                    return jsonify({"error": "No team found in the specified Championship slot"}), 400
                
                # Toggle champion selection
                if bracket["champion"] == selected_team:
                    # Clicking on current champion deselects it
                    bracket["champion"] = None
                    print(f"Deselected champion")
                else:
                    # Otherwise set as new champion
                    bracket["champion"] = selected_team
                    print(f"Set new champion: {selected_team['name']}")
                
                # Update winners for rendering
                bracket = update_winners(bracket)
                
                # Save the updated bracket
                with open('bracket.json', 'w') as f:
                    json.dump(bracket, f)
                    
                return jsonify(bracket)
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error in select_champion: {str(e)}")
                return jsonify({"error": f"Error selecting champion: {str(e)}"}), 400
        
        elif action == 'auto_fill':
            # Auto-fill the bracket
            bracket = auto_fill_bracket(copy.deepcopy(bracket))
            
            # Save the updated bracket
            with open('bracket.json', 'w') as f:
                json.dump(bracket, f)
                
            return jsonify(bracket)
        
        elif action == 'random_fill':
            # Randomly fill the bracket
            print("Starting random fill with bracket structure:", bracket.keys())
            bracket = random_fill_bracket(copy.deepcopy(bracket))
            
            # Log the bracket structure after random_fill
            print("After random_fill, bracket structure:", bracket.keys())
            print("First round structure for west region:", [team['name'] if team else 'None' for team in bracket['west'][0]])
            print("Sample from winners:", bracket['winners']['west'][0][:3])
            
            # Save the updated bracket
            with open('bracket.json', 'w') as f:
                json.dump(bracket, f)
                
            print("Returning random filled bracket to frontend")
            return jsonify(bracket)
        
        elif action == 'reset':
            # Reset the bracket to initial state
            bracket = initialize_bracket()
            
            # Ensure winners are updated before returning
            bracket = update_winners(bracket)
            
            # Log the updated bracket for debugging
            print('Bracket data being returned:', pretty_print_bracket(bracket))
            
            return jsonify(bracket)
            
        else:
            print(f"Unknown action: {action}")
            return jsonify({"error": "Unknown action"}), 400
    
    # GET request - return the current bracket
    # Ensure winners are updated before returning
    bracket = update_winners(bracket)
    print('Bracket data being returned:', pretty_print_bracket(bracket))
    return jsonify(bracket)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port) 