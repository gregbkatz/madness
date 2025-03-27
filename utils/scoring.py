"""
Scoring Module

This module provides functionality for scoring brackets against truth data,
calculating points, and determining rankings.
"""

import json
import os
import copy
from collections import defaultdict

# Define points for each round
POINTS_MAP = {
    0: 1,   # Round of 64
    1: 2,   # Round of 32
    2: 4,   # Sweet 16
    3: 8,   # Elite 8
    4: 16,  # Final Four
    5: 32,  # Championship
    6: 64   # Champion
}

def calculate_points_for_pick(user_team, truth_team, round_idx):
    """
    Calculate points for a single pick.
    
    Args:
        user_team (dict): Team picked by the user
        truth_team (dict): Correct team from the truth bracket
        round_idx (int): Round index (0-6)
        
    Returns:
        int: Points earned for this pick
    """
    # If user's pick matches the truth bracket
    if (user_team and truth_team and 
        user_team.get('name') == truth_team.get('name') and 
        user_team.get('seed') == truth_team.get('seed')):
        
        # Calculate base points based on the round
        base_points = POINTS_MAP.get(round_idx, 0)
        
        # Check for upset bonus (higher seed beating lower seed)
        # Note: In basketball, lower seed number means higher rank
        # (e.g., a 10 seed beating a 2 seed is an upset)
        seed = user_team.get('seed', 0)
        if seed > 4:  # 5 or higher seeds are considered underdogs
            upset_bonus = base_points  # Double points for upset picks
            return base_points + upset_bonus
        
        return base_points
    
    # No points if the pick doesn't match
    return 0

def compare_with_truth(user_bracket, truth_bracket):
    """
    Compare a user's bracket with the truth bracket and calculate total points.
    
    Args:
        user_bracket (dict): The user's bracket
        truth_bracket (dict): The truth bracket
        
    Returns:
        dict: Results containing total points, correct picks, and region breakdowns
    """
    # Deep copy to avoid modifying the original brackets
    user = copy.deepcopy(user_bracket) if user_bracket else {}
    truth = copy.deepcopy(truth_bracket) if truth_bracket else {}
    
    # Ensure both brackets are valid dictionaries
    if not isinstance(user, dict) or not isinstance(truth, dict):
        print(f"Warning: Invalid bracket format - user_bracket: {type(user)}, truth_bracket: {type(truth)}")
        # Return default results with zero points
        return {
            'total_points': 0,
            'correct_picks': 0,
            'incorrect_picks': 0,
            'regions': {},
            'rounds': {}
        }
    
    # Initialize results
    results = {
        'total_points': 0,
        'correct_picks': 0,
        'incorrect_picks': 0,
        'regions': {},
        'rounds': defaultdict(lambda: {'points': 0, 'correct': 0, 'incorrect': 0})
    }
    
    # Process each region (east, west, south, midwest)
    regions = ['east', 'west', 'south', 'midwest']
    for region in regions:
        # Skip if region doesn't exist in either bracket
        if region not in user or region not in truth:
            continue
            
        # Verify that regions are lists/arrays, not strings or other types
        if not isinstance(user[region], list) or not isinstance(truth[region], list):
            print(f"Warning: Invalid region format for {region} - user: {type(user[region])}, truth: {type(truth[region])}")
            continue
        
        region_results = {
            'points': 0,
            'correct': 0,
            'incorrect': 0,
            'rounds': defaultdict(lambda: {'points': 0, 'correct': 0, 'incorrect': 0})
        }
        
        # Process each round in the region
        for round_idx in range(min(len(user[region]), len(truth[region]))):
            # Skip if this round is missing or empty in either bracket
            if round_idx >= len(truth[region]) or not truth[region][round_idx] or round_idx >= len(user[region]) or not user[region][round_idx]:
                continue
                
            # Verify round data is a list
            if not isinstance(user[region][round_idx], list) or not isinstance(truth[region][round_idx], list):
                print(f"Warning: Invalid round format for {region} round {round_idx}")
                continue
                
            # Get the length of the shorter list to avoid index errors
            max_games = min(len(user[region][round_idx]), len(truth[region][round_idx]))
            
            # Compare each game in this round
            for game_idx in range(max_games):
                user_team = user[region][round_idx][game_idx]
                truth_team = truth[region][round_idx][game_idx]
                
                # Calculate points for this pick
                points = calculate_points_for_pick(user_team, truth_team, round_idx)
                
                # Update results
                if points > 0:
                    results['correct_picks'] += 1
                    region_results['correct'] += 1
                    region_results['rounds'][round_idx]['correct'] += 1
                    results['rounds'][round_idx]['correct'] += 1
                else:
                    results['incorrect_picks'] += 1
                    region_results['incorrect'] += 1
                    region_results['rounds'][round_idx]['incorrect'] += 1
                    results['rounds'][round_idx]['incorrect'] += 1
                
                # Add points to all relevant totals
                results['total_points'] += points
                region_results['points'] += points
                region_results['rounds'][round_idx]['points'] += points
                results['rounds'][round_idx]['points'] += points
        
        # Store region results
        results['regions'][region] = region_results
    
    # Process Final Four (round 4)
    # Map regions to Final Four slots
    region_to_ff = {
        'midwest': 0,
        'west': 1, 
        'south': 2,
        'east': 3
    }
    
    round_idx = 4  # Final Four is round 4
    for region, ff_idx in region_to_ff.items():
        # Check if region winner is in the Final Four
        if ff_idx < len(user['finalFour']) and ff_idx < len(truth['finalFour']):
            user_team = user['finalFour'][ff_idx]
            truth_team = truth['finalFour'][ff_idx]
            
            # Calculate points for this pick
            points = calculate_points_for_pick(user_team, truth_team, round_idx)
            
            # Update results
            if points > 0:
                results['correct_picks'] += 1
                results['rounds'][round_idx]['correct'] += 1
            else:
                results['incorrect_picks'] += 1
                results['rounds'][round_idx]['incorrect'] += 1
            
            # Add points to totals
            results['total_points'] += points
            results['rounds'][round_idx]['points'] += points
    
    # Process Championship (round 5)
    round_idx = 5
    for game_idx in range(2):  # 2 championship slots
        if game_idx < len(user['championship']) and game_idx < len(truth['championship']):
            user_team = user['championship'][game_idx]
            truth_team = truth['championship'][game_idx]
            
            # Calculate points for this pick
            points = calculate_points_for_pick(user_team, truth_team, round_idx)
            
            # Update results
            if points > 0:
                results['correct_picks'] += 1
                results['rounds'][round_idx]['correct'] += 1
            else:
                results['incorrect_picks'] += 1
                results['rounds'][round_idx]['incorrect'] += 1
            
            # Add points to totals
            results['total_points'] += points
            results['rounds'][round_idx]['points'] += points
    
    # Process Champion (round 6)
    round_idx = 6
    user_team = user['champion']
    truth_team = truth['champion']
    
    # Calculate points for champion pick
    points = calculate_points_for_pick(user_team, truth_team, round_idx)
    
    # Update results
    if points > 0:
        results['correct_picks'] += 1
        results['rounds'][round_idx]['correct'] += 1
    else:
        results['incorrect_picks'] += 1
        results['rounds'][round_idx]['incorrect'] += 1
    
    # Add points to totals
    results['total_points'] += points
    results['rounds'][round_idx]['points'] += points
    
    # Convert defaultdicts to regular dicts for better JSON serialization
    results['rounds'] = dict(results['rounds'])
    for region in results['regions']:
        results['regions'][region]['rounds'] = dict(results['regions'][region]['rounds'])
    
    return results

def calculate_rankings(user_brackets, truth_bracket):
    """
    Calculate rankings for all users based on their bracket scores.
    
    Args:
        user_brackets (dict): Dictionary of username: bracket for all users
        truth_bracket (dict): The truth bracket
        
    Returns:
        list: List of dictionaries with rankings, sorted by points
    """
    rankings = []
    
    # Calculate scores for each user
    for username, bracket in user_brackets.items():
        # Compare with truth bracket
        results = compare_with_truth(bracket, truth_bracket)
        
        # Create ranking entry
        ranking = {
            'username': username,
            'total_points': results['total_points'],
            'correct_picks': results['correct_picks'],
            'incorrect_picks': results['incorrect_picks'],
            'round_points': {str(k): v['points'] for k, v in results['rounds'].items()},
            'region_points': {k: v['points'] for k, v in results['regions'].items()}
        }
        
        rankings.append(ranking)
    
    # Sort by total points (descending)
    rankings.sort(key=lambda x: x['total_points'], reverse=True)
    
    # Assign ranks (handling ties)
    current_rank = 1
    prev_points = None
    
    for i, ranking in enumerate(rankings):
        if i > 0 and ranking['total_points'] < prev_points:
            current_rank = i + 1
        
        ranking['rank'] = current_rank
        prev_points = ranking['total_points']
    
    return rankings

def save_rankings(rankings, output_file):
    """
    Save rankings to a JSON file.
    
    Args:
        rankings (list): Rankings data
        output_file (str): Path to save the file
        
    Returns:
        str: Path to the saved file
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(rankings, f, indent=2)
    
    print(f"Saved rankings to {output_file}")
    return output_file

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
def compare_with_truth(bracket, truth_bracket=None):
    """
    Compare a bracket with the truth bracket and add CSS classes.
    
    Args:
        bracket: The bracket to compare
        truth_bracket: Optional truth bracket to compare against. If None,
                      the most recent truth bracket will be loaded.
    """
    if truth_bracket is None:
        truth_bracket = get_most_recent_truth_bracket()
    if not truth_bracket or not bracket:
        return bracket
        
    # Deep copy the bracket to avoid modifying the original
    result_bracket = copy.deepcopy(bracket)
    
    # Try to get the chalk bracket for bonus calculations
    chalk_bracket = get_chalk_bracket()
    # print(f"Chalk bracket loaded: {chalk_bracket is not None}")
    
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
                                    # print(f"Added bonus of {bonus} to {team['name']} in {region} round {round_idx} position {i}")
                                else:
                                    team["bonus"] = 0  # Explicitly set to zero instead of None
                                    # print(f"Set bonus to 0 for {team['name']} in {region} round {round_idx} (no upset)")
                        
                        # If truth team is None (future round), we're done with this team
                        if not truth_team:
                            # Check if this team is in the eliminated teams set before continuing
                            if team["name"] in eliminated_teams:
                                team["classes"] += " incorrect"
                                team["correct"] = False
                                team["isEliminated"] = True
                                # print(f"Marked future pick {team['name']} in {region} round {round_idx} as eliminated")
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
                            # print(f"Added Final Four bonus of {bonus} to {team['name']} (pos {i})")
                        else:
                            team["bonus"] = 0
                
                # Skip comparison if truth team doesn't exist yet
                if not truth_team:
                    # Check if this team is in the eliminated teams set before continuing
                    if team["name"] in eliminated_teams:
                        team["classes"] += " incorrect"
                        team["correct"] = False
                        team["isEliminated"] = True
                        # print(f"Marked future pick {team['name']} in Final Four as eliminated")
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
                            # print(f"Added Championship bonus of {bonus} to {team['name']} (pos {i})")
                        else:
                            team["bonus"] = 0
                
                # Skip comparison if truth team doesn't exist yet
                if not truth_team:
                    # Check if this team is in the eliminated teams set before continuing
                    if team["name"] in eliminated_teams:
                        team["classes"] += " incorrect"
                        team["correct"] = False
                        team["isEliminated"] = True
                        # print(f"Marked future pick {team['name']} in Championship as eliminated")
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
                        # print(f"Added Champion bonus of {bonus} to {result_bracket['champion']['name']}")
                    else:
                        result_bracket["champion"]["bonus"] = 0
            
            # Skip comparison if truth champion doesn't exist yet
            if not truth_champion:
                # Check if this team is in the eliminated teams set before continuing
                if result_bracket["champion"] and result_bracket["champion"]["name"] in eliminated_teams:
                    result_bracket["champion"]["classes"] += " incorrect"
                    result_bracket["champion"]["correct"] = False
                    result_bracket["champion"]["isEliminated"] = True
                    # print(f"Marked future pick {result_bracket['champion']['name']} as Champion as eliminated")
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
                        # print(f"Marked future pick {team['name']} in {region} round {round_idx} as eliminated")
    
    # Check Final Four for eliminated teams
    for i in range(len(result_bracket["finalFour"])):
        team = result_bracket["finalFour"][i]
        if team and isinstance(team, dict) and "correct" not in team:
            if team["name"] in eliminated_teams:
                team["classes"] += " incorrect"
                team["correct"] = False
                team["isEliminated"] = True
                # print(f"Marked future pick {team['name']} in Final Four as eliminated")
                
    # Check Championship for eliminated teams
    for i in range(len(result_bracket["championship"])):
        team = result_bracket["championship"][i]
        if team and isinstance(team, dict) and "correct" not in team:
            if team["name"] in eliminated_teams:
                team["classes"] += " incorrect"
                team["correct"] = False
                team["isEliminated"] = True
                # print(f"Marked future pick {team['name']} in Championship as eliminated")
                
    # Check Champion for eliminated teams
    if result_bracket["champion"] and isinstance(result_bracket["champion"], dict) and "correct" not in result_bracket["champion"]:
        if result_bracket["champion"]["name"] in eliminated_teams:
            result_bracket["champion"]["classes"] += " incorrect"
            result_bracket["champion"]["correct"] = False
            result_bracket["champion"]["isEliminated"] = True
            # print(f"Marked future pick {result_bracket['champion']['name']} as Champion as eliminated")
    
    return result_bracket

if __name__ == "__main__":
    # Example usage
    from utils.bracket_utils import get_most_recent_truth_bracket, get_all_user_brackets
    
    # Load truth bracket
    truth_file = get_most_recent_truth_bracket()
    if truth_file:
        with open(truth_file, 'r') as f:
            truth_bracket = json.load(f)
        
        # Load user brackets
        user_brackets = get_all_user_brackets()
        
        # Calculate rankings
        rankings = calculate_rankings(user_brackets, truth_bracket)
        
        # Print rankings
        print("\nRankings:")
        for ranking in rankings:
            print(f"{ranking['rank']}. {ranking['username']}: {ranking['total_points']} points") 