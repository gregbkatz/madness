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