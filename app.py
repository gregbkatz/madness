from flask import Flask, render_template, jsonify, request
from data.teams import teams
from datetime import datetime
from bracket_logic import initialize_bracket, select_team, auto_fill_bracket, pretty_print_bracket

app = Flask(__name__)

# Store the bracket in server memory (in a real app, this would be in a database)
bracket = initialize_bracket()

@app.route('/')
def index():
    current_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
    return render_template('index.html', current_time=current_time)

@app.route('/api/teams')
def get_teams():
    return jsonify(teams)

@app.route('/api/bracket', methods=['GET', 'POST'])
def manage_bracket():
    global bracket
    
    if request.method == 'POST':
        try:
            data = request.json
            action = data.get('action')
            
            if action == 'select_team':
                region = data.get('region')
                round_idx = data.get('round')
                game_index = data.get('gameIndex')
                team_index = data.get('teamIndex')
                
                # Update the bracket using our backend logic
                bracket = select_team(bracket, region, round_idx, game_index, team_index)
                
            elif action == 'select_final_four':
                semifinal_index = data.get('semifinalIndex')
                team_index = data.get('teamIndex')
                
                # For Final Four selections, we use a special region
                bracket = select_team(bracket, "finalFour", 4, semifinal_index, team_index)
                
            elif action == 'select_championship':
                team_index = data.get('teamIndex')
                
                # For Championship selections
                bracket = select_team(bracket, "championship", 5, team_index, 0)
                
            elif action == 'auto_fill':
                # Auto-fill the bracket
                bracket = auto_fill_bracket(bracket)
                
            elif action == 'reset':
                # Reset the entire bracket
                bracket = initialize_bracket()
            
            # Log the updated bracket for debugging
            print('Bracket data being returned:', pretty_print_bracket(bracket))
            
            return jsonify(bracket)
            
        except Exception as e:
            print(f"Error processing bracket update: {e}")
            return jsonify({"error": str(e)}), 400
    
    # GET request - return the current bracket
    print('Bracket data being returned:', pretty_print_bracket(bracket))
    return jsonify(bracket)

if __name__ == '__main__':
    app.run(debug=True) 