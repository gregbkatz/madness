"""
Module for handling bracket logic for the March Madness application.
This centralizes bracket management functionality that was previously in the frontend.
"""
from data.teams import teams
import copy
import random
import json

def initialize_bracket():
    """
    Initialize a new bracket with teams in the first round
    and placeholder nulls for subsequent rounds.
    """
    bracket = {
        "west": [[] for _ in range(4)],
        "east": [[] for _ in range(4)],
        "south": [[] for _ in range(4)],
        "midwest": [[] for _ in range(4)],
        "finalFour": [None, None, None, None],
        "championship": [None, None],
        "champion": None
    }
    
    # Initialize the bracket with teams in the first round
    for region in ["west", "east", "south", "midwest"]:
        # First round setup (8 games with 16 teams)
        first_round = []
        region_teams = teams[region]
        
        # Game 0: 1 vs 16
        first_round.append(region_teams[0])  # 1 seed
        first_round.append(region_teams[1])  # 16 seed
        
        # Game 1: 8 vs 9
        first_round.append(region_teams[2])  # 8 seed
        first_round.append(region_teams[3])  # 9 seed
        
        # Game 2: 5 vs 12
        first_round.append(region_teams[4])  # 5 seed
        first_round.append(region_teams[5])  # 12 seed
        
        # Game 3: 4 vs 13
        first_round.append(region_teams[6])  # 4 seed
        first_round.append(region_teams[7])  # 13 seed
        
        # Game 4: 6 vs 11
        first_round.append(region_teams[8])  # 6 seed
        first_round.append(region_teams[9])  # 11 seed
        
        # Game 5: 3 vs 14
        first_round.append(region_teams[10])  # 3 seed
        first_round.append(region_teams[11])  # 14 seed
        
        # Game 6: 7 vs 10
        first_round.append(region_teams[12])  # 7 seed
        first_round.append(region_teams[13])  # 10 seed
        
        # Game 7: 2 vs 15
        first_round.append(region_teams[14])  # 2 seed
        first_round.append(region_teams[15])  # 15 seed
        
        bracket[region][0] = first_round
        
        # Initialize subsequent rounds with Nones
        # Round 1 (second round): 8 slots
        bracket[region][1] = [None] * 8
        
        # Round 2 (Sweet 16): 4 slots
        bracket[region][2] = [None] * 4
        
        # Round 3 (Elite 8): 2 slots
        bracket[region][3] = [None] * 2
    
    return bracket

def get_region_final_four_index(region):
    """Map region to Final Four index"""
    mapping = {
        'west': 0,
        'east': 1,
        'south': 2,
        'midwest': 3
    }
    return mapping.get(region, -1)

def reset_team_completely(bracket, region, team_to_reset, start_round):
    """
    Reset a team from all subsequent rounds if it appears
    """
    if not team_to_reset:
        return bracket
    
    # Save the team details for comparison
    team_name = team_to_reset['name']
    team_seed = team_to_reset['seed']
    
    # Helper function to check if a team matches our target team
    def is_matching_team(team):
        return team and team['name'] == team_name and team['seed'] == team_seed
    
    # Track changes for debugging
    changes = []
    
    # 1. Check all subsequent rounds in this region
    for round_idx in range(start_round, 4):
        for slot in range(len(bracket[region][round_idx])):
            if is_matching_team(bracket[region][round_idx][slot]):
                # Found the team, clear it
                bracket[region][round_idx][slot] = None
                changes.append(f"Cleared {team_name} from {region} round {round_idx} slot {slot}")
                
                # If this is the Elite Eight round, check Final Four
                if round_idx == 3:
                    ff_index = get_region_final_four_index(region)
                    
                    # Check if this team made it to Final Four
                    if is_matching_team(bracket["finalFour"][ff_index]):
                        # Clear from Final Four
                        bracket["finalFour"][ff_index] = None
                        changes.append(f"Cleared {team_name} from Final Four slot {ff_index}")
                        
                        # Check Championship
                        champ_index = 0 if ff_index < 2 else 1
                        if is_matching_team(bracket["championship"][champ_index]):
                            # Clear from Championship
                            bracket["championship"][champ_index] = None
                            changes.append(f"Cleared {team_name} from Championship slot {champ_index}")
                            
                            # Check Champion
                            if is_matching_team(bracket["champion"]):
                                bracket["champion"] = None
                                changes.append(f"Cleared {team_name} from Champion")
    
    # 2. Also check Final Four directly
    for i in range(len(bracket["finalFour"])):
        if is_matching_team(bracket["finalFour"][i]):
            bracket["finalFour"][i] = None
            changes.append(f"Cleared {team_name} from Final Four slot {i}")
            
            # Check Championship
            champ_index = 0 if i < 2 else 1
            if is_matching_team(bracket["championship"][champ_index]):
                bracket["championship"][champ_index] = None
                changes.append(f"Cleared {team_name} from Championship slot {champ_index}")
                
                # Check Champion
                if is_matching_team(bracket["champion"]):
                    bracket["champion"] = None
                    changes.append(f"Cleared {team_name} from Champion")
    
    # 3. Check Championship directly
    for i in range(len(bracket["championship"])):
        if is_matching_team(bracket["championship"][i]):
            bracket["championship"][i] = None
            changes.append(f"Cleared {team_name} from Championship slot {i}")
            
            # Check Champion
            if is_matching_team(bracket["champion"]):
                bracket["champion"] = None
                changes.append(f"Cleared {team_name} from Champion")
    
    # 4. Finally check Champion directly
    if is_matching_team(bracket["champion"]):
        bracket["champion"] = None
        changes.append(f"Cleared {team_name} from Champion")
    
    return bracket

def select_team(bracket, region, round_idx, game_index, team_index):
    """
    Select a team in the bracket and advance it to the next round,
    handling all the cascading logic to remove teams as needed.
    """
    # Make a deep copy to avoid modifying the original bracket
    bracket = copy.deepcopy(bracket)
    
    # Get the selected team
    selected_team = None
    if round_idx < 4:  # Regular rounds
        team_slot = game_index * 2 + team_index
        if team_slot < len(bracket[region][round_idx]):
            selected_team = bracket[region][round_idx][team_slot]
    elif round_idx == 4:  # Final Four
        # This is special handling for Final Four selections
        if region == "finalFour":
            semifinal_index = game_index
            team_slot = team_index
            if semifinal_index == 0:  # Left semifinal
                final_four_index = 2 if team_slot == 0 else 1  # South or East
                selected_team = bracket["finalFour"][final_four_index]
                champ_index = 0
            else:  # Right semifinal
                final_four_index = 3 if team_slot == 0 else 0  # Midwest or West
                selected_team = bracket["finalFour"][final_four_index]
                champ_index = 1
            
            # Get current team in championship slot
            current_championship_team = bracket["championship"][champ_index]
            
            # Toggle behavior
            if current_championship_team == selected_team:
                # Clear the championship slot
                bracket["championship"][champ_index] = None
                
                # Clear champion if needed
                if bracket["champion"] == current_championship_team:
                    bracket["champion"] = None
            else:
                # Set new team in championship
                bracket["championship"][champ_index] = selected_team
                
                # Clear champion if from this slot
                if bracket["champion"] == current_championship_team:
                    bracket["champion"] = None
            
            return bracket
    elif round_idx == 5:  # Championship
        if region == "championship":
            team_index = game_index  # In this case, game_index is actually the team index
            selected_team = bracket["championship"][team_index]
            
            # Toggle champion selection
            if bracket["champion"] == selected_team:
                bracket["champion"] = None
            else:
                bracket["champion"] = selected_team
            
            return bracket
    
    # Ensure a team was selected
    if not selected_team:
        return bracket
    
    if round_idx < 3:  # Regular rounds (not Elite Eight)
        # Determine next round and game position
        next_round = round_idx + 1
        next_game_index = game_index // 2
        next_team_index = game_index % 2
        next_slot = next_game_index * 2 + next_team_index
        
        # Check what team is currently in the next round's slot
        team_in_next_slot = bracket[region][next_round][next_slot] if next_slot < len(bracket[region][next_round]) else None
        
        # If clicking the same team already in next round, do nothing
        if team_in_next_slot == selected_team:
            return bracket
        
        # Set the selected team in the next round
        bracket[region][next_round][next_slot] = selected_team
        
        # If replacing a different team, reset all instances of that team
        if team_in_next_slot and team_in_next_slot != selected_team:
            bracket = reset_team_completely(bracket, region, team_in_next_slot, next_round)
    
    elif round_idx == 3:  # Elite Eight to Final Four
        # Get the Final Four slot index for this region
        ff_index = get_region_final_four_index(region)
        
        # Current team in this Final Four slot
        current_final_four_team = bracket["finalFour"][ff_index]
        
        # If same team already in Final Four, no change
        if current_final_four_team == selected_team:
            return bracket
        
        # Set the new Elite Eight winner in Final Four
        bracket["finalFour"][ff_index] = selected_team
        
        # If replacing a team in Final Four, reset it from Championship and Champion
        if current_final_four_team and current_final_four_team != selected_team:
            # Determine which Championship slot this affects
            champ_index = 0 if ff_index < 2 else 1
            
            # Check if the replaced team was in Championship
            if bracket["championship"][champ_index] == current_final_four_team:
                # Clear the Championship slot
                bracket["championship"][champ_index] = None
                
                # Clear champion if needed
                if bracket["champion"] == current_final_four_team:
                    bracket["champion"] = None
    
    return bracket

def auto_fill_bracket(bracket=None):
    """
    Auto-fill the bracket by selecting teams with lower seeds (or random if seeds are equal)
    """
    if bracket is None:
        bracket = initialize_bracket()
    else:
        bracket = copy.deepcopy(bracket)
    
    # Process each region separately
    for region in ["west", "east", "south", "midwest"]:
        # Process rounds 0-3 (First Round through Elite Eight)
        for round_idx in range(4):
            games_in_round = 2 ** (3 - round_idx)
            
            for game_index in range(games_in_round):
                # Get the two teams in this matchup
                if round_idx == 0:
                    # First round - teams are already set
                    team1 = bracket[region][round_idx][game_index * 2]
                    team2 = bracket[region][round_idx][game_index * 2 + 1]
                else:
                    # Later rounds - need to get teams from previous round's winners
                    team1_idx = game_index * 2
                    team2_idx = game_index * 2 + 1
                    
                    if team1_idx < len(bracket[region][round_idx]):
                        team1 = bracket[region][round_idx][team1_idx]
                    else:
                        team1 = None
                        
                    if team2_idx < len(bracket[region][round_idx]):
                        team2 = bracket[region][round_idx][team2_idx]
                    else:
                        team2 = None
                
                # Skip if either team is missing
                if not team1 or not team2:
                    continue
                
                # Determine the winner based on seed
                if int(team1["seed"]) < int(team2["seed"]):
                    # Team 1 has a lower seed (better)
                    winner = team1
                elif int(team2["seed"]) < int(team1["seed"]):
                    # Team 2 has a lower seed (better)
                    winner = team2
                else:
                    # Seeds are the same, select randomly
                    winner = team1 if random.random() < 0.5 else team2
                
                # Set the winner in the next round
                if round_idx < 3:
                    # For rounds 0-2, advance to the next round in same region
                    next_round = round_idx + 1
                    next_game_index = game_index // 2
                    next_team_index = game_index % 2
                    next_slot = next_game_index * 2 + next_team_index
                    
                    if next_slot < len(bracket[region][next_round]):
                        bracket[region][next_round][next_slot] = winner
                else:
                    # For Elite Eight (round 3), advance to Final Four
                    ff_index = get_region_final_four_index(region)
                    bracket["finalFour"][ff_index] = winner
    
    # Process Final Four (semifinal matchups)
    for semifinal_index in range(2):
        if semifinal_index == 0:
            # South vs East
            team1 = bracket["finalFour"][2]  # South
            team2 = bracket["finalFour"][1]  # East
        else:
            # Midwest vs West
            team1 = bracket["finalFour"][3]  # Midwest
            team2 = bracket["finalFour"][0]  # West
        
        # Make sure we have both teams
        if team1 and team2:
            # Determine winner based on seed
            if int(team1["seed"]) < int(team2["seed"]):
                winner = team1
            elif int(team2["seed"]) < int(team1["seed"]):
                winner = team2
            else:
                # Seeds are same, select randomly
                winner = team1 if random.random() < 0.5 else team2
            
            # Set winner in championship
            bracket["championship"][semifinal_index] = winner
    
    # Process Championship
    team1 = bracket["championship"][0]
    team2 = bracket["championship"][1]
    
    # Make sure we have both teams
    if team1 and team2:
        # Determine winner based on seed
        if int(team1["seed"]) < int(team2["seed"]):
            winner = team1
        elif int(team2["seed"]) < int(team1["seed"]):
            winner = team2
        else:
            # Seeds are same, select randomly
            winner = team1 if random.random() < 0.5 else team2
        
        # Set the champion
        bracket["champion"] = winner
    
    return bracket

def pretty_print_bracket(bracket):
    """
    Return a nicely formatted string representation of the bracket
    """
    return json.dumps(bracket, indent=2) 