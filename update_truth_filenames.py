#!/usr/bin/env python3
"""
Update Truth Bracket Filenames

This script updates the filenames of truth bracket files to include information
about the most recent game result in the format 'round_x_game_y_W_defeats_Z.json'.
"""

import os
import json
import argparse
import copy
import shutil
from datetime import datetime

from utils.bracket_utils import get_sorted_truth_files

# Team name shortcuts for more concise filenames
TEAM_NAME_SHORTCUTS = {
    "UNC Wilmington": "UNC Wilm.",
    "Texas/Xavier": "Xavier",
    "AL St/St Francis U": "AL St",
    "AU/Mt St Mary's": "Mt St Mary's",
    "San Diego St/NC": "UNC",
    "Mississppi St": "Miss. St",
}

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Update truth bracket filenames to include recent game results'
    )
    parser.add_argument(
        '--truth-dir',
        type=str,
        default='truth_brackets',
        help='Directory containing truth bracket files (default: truth_brackets)'
    )
    parser.add_argument(
        '--backup-dir',
        type=str,
        default='truth_brackets/backup',
        help='Directory to store backup of original files (default: truth_brackets/backup)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    return parser.parse_args()


def find_recent_game_difference(current_bracket, previous_bracket):
    """
    Find the most recent game that was updated between the previous and current bracket.
    
    Args:
        current_bracket (dict): The current bracket state
        previous_bracket (dict): The previous bracket state
        
    Returns:
        tuple: (region, round_idx, game_idx, winner_name, winner_seed, loser_name, loser_seed) or None if no difference found
    """
    # Check each region first
    regions = ['midwest', 'west', 'south', 'east']
    for region in regions:
        # Check each round
        for round_idx in range(4):  # 0-3 for region rounds
            if round_idx >= len(current_bracket[region]) or round_idx >= len(previous_bracket[region]):
                continue
                
            current_round = current_bracket[region][round_idx]
            previous_round = previous_bracket[region][round_idx]
            
            # Check each game in the round
            for game_idx in range(len(current_round)):
                if game_idx >= len(previous_round):
                    continue
                    
                # If the current game has a winner but previous didn't, this is our change
                if current_round[game_idx] and not previous_round[game_idx]:
                    winner = current_round[game_idx]
                    
                    # Now find the loser - need to look at the previous round
                    if round_idx > 0:
                        prev_round_idx = round_idx - 1
                        team1_idx = game_idx * 2
                        team2_idx = game_idx * 2 + 1
                        
                        if team1_idx < len(current_bracket[region][prev_round_idx]) and team2_idx < len(current_bracket[region][prev_round_idx]):
                            team1 = current_bracket[region][prev_round_idx][team1_idx]
                            team2 = current_bracket[region][prev_round_idx][team2_idx]
                            
                            # The loser is the team that's not the winner
                            loser = team2 if winner == team1 else team1
                            
                            if winner and loser:
                                winner_seed = winner.get('seed', 'X')
                                loser_seed = loser.get('seed', 'X')
                                return (region, round_idx, game_idx, winner['name'], winner_seed, loser['name'], loser_seed)
    
    # Check Final Four
    if 'finalFour' in current_bracket and 'finalFour' in previous_bracket:
        for game_idx in range(len(current_bracket['finalFour'])):
            if game_idx >= len(previous_bracket['finalFour']):
                continue
                
            if current_bracket['finalFour'][game_idx] and not previous_bracket['finalFour'][game_idx]:
                winner = current_bracket['finalFour'][game_idx]
                
                # Find the loser - this is trickier for Final Four
                # For simplicity, we'll just note the winner with its seed
                if winner:
                    winner_seed = winner.get('seed', 'X')
                    return ('finalFour', 4, game_idx, winner['name'], winner_seed, "opponent", "X")
    
    # Check Championship
    if 'championship' in current_bracket and 'championship' in previous_bracket:
        for game_idx in range(len(current_bracket['championship'])):
            if game_idx >= len(previous_bracket['championship']):
                continue
                
            if current_bracket['championship'][game_idx] and not previous_bracket['championship'][game_idx]:
                winner = current_bracket['championship'][game_idx]
                
                # To find loser, look at finalFour teams
                if 'finalFour' in current_bracket:
                    ff_teams = [team for team in current_bracket['finalFour'] if team]
                    possible_losers = [team for team in ff_teams if team != winner]
                    
                    if winner and possible_losers:
                        winner_seed = winner.get('seed', 'X')
                        return ('championship', 5, game_idx, winner['name'], winner_seed, "finalist", "X")
    
    # Check Champion
    if 'champion' in current_bracket and 'champion' in previous_bracket:
        if current_bracket['champion'] and not previous_bracket['champion']:
            winner = current_bracket['champion']
            
            # To find runner-up, look at championship teams
            if 'championship' in current_bracket:
                championship_teams = [team for team in current_bracket['championship'] if team]
                possible_losers = [team for team in championship_teams if team != winner]
                
                if winner and possible_losers:
                    winner_seed = winner.get('seed', 'X')
                    loser_seed = possible_losers[0].get('seed', 'X')
                    return ('champion', 6, 0, winner['name'], winner_seed, possible_losers[0]['name'], loser_seed)
    
    return None

def _canonicalize_team_name(team_name):
    """
    Canonicalize a team name by removing slashes, underscores, periods, and apostrophes.
    """
    team_name = TEAM_NAME_SHORTCUTS.get(team_name, team_name)
    return team_name.replace('_', ' ').replace('.', '').replace("'", "").strip()

def generate_new_filename(old_filename, difference):
    """
    Generate a new filename that includes the game result with seeds.
    
    Args:
        old_filename (str): Original filename
        difference (tuple): (region, round_idx, game_idx, winner_name, winner_seed, loser_name, loser_seed)
        
    Returns:
        str: New filename with game result included
    """
    # Parse existing filename structure if it exists
    basename = os.path.basename(old_filename)
    dirname = os.path.dirname(old_filename)
    
    # Extract the original round and game indices from the filename if they exist
    original_round_idx = None
    original_game_idx = None
    
    if basename.startswith("round_"):
        # Get the round index
        round_part = basename.split("_game_")[0]
        if round_part.startswith("round_"):
            round_str = round_part.replace("round_", "")
            if round_str.isdigit():
                original_round_idx = int(round_str)
        
        # Get the game index
        if "_game_" in basename:
            parts = basename.split("_game_")
            if len(parts) > 1:
                game_part = parts[1].split(".")[0].split("_")[0]
                if game_part.isdigit():
                    original_game_idx = int(game_part)
    
    # Unpack the difference tuple
    region, round_idx, game_idx, winner_name, winner_seed, loser_name, loser_seed = difference
    
    # Use the original indices if available, otherwise use the indices from the difference
    if original_round_idx is not None:
        round_idx = original_round_idx
    if original_game_idx is not None:
        game_idx = original_game_idx
    
    winner_name = _canonicalize_team_name(winner_name)
    loser_name = _canonicalize_team_name(loser_name)

    new_filename = f"round_{round_idx}_game_{game_idx} {winner_seed} {winner_name} defeats {loser_seed} {loser_name}.json"
    
    return os.path.join(dirname, new_filename)


def main():
    """Main function to run the script."""
    args = parse_arguments()
    
    # Create backup directory if specified and not in dry run mode
    if not args.dry_run and args.backup_dir:
        os.makedirs(args.backup_dir, exist_ok=True)
    
    # Get all truth bracket files sorted by time (oldest first)
    all_truth_files = get_sorted_truth_files(args.truth_dir)
    
    # Sort files by modification time to ensure chronological order
    all_truth_files.sort(key=os.path.getmtime)
    
    if not all_truth_files:
        print("No truth bracket files found in directory:", args.truth_dir)
        return 1
    
    print(f"Found {len(all_truth_files)} truth bracket files")
    print("Processing files in chronological order by modification time")
    
    # Process each file
    previous_bracket = None
    files_processed = 0
    files_renamed = 0
    files_skipped = 0
    
    for i, file_path in enumerate(all_truth_files):
        print(f"\nProcessing file {i+1}/{len(all_truth_files)}: {file_path}")
        files_processed += 1
        
        # Skip files that already have the new naming format
        basename = os.path.basename(file_path)
        if ' defeats ' in basename and any(str(seed) in basename for seed in range(1, 17)):
            print(f"  Skipping file already in new format: {basename}")
            files_skipped += 1
            continue
        
        # Load the current bracket
        with open(file_path, 'r') as f:
            current_bracket = json.load(f)
        
        # Skip if this is the first file (no previous bracket to compare)
        if previous_bracket is None:
            previous_bracket = copy.deepcopy(current_bracket)
            print("  Skipping first file (no previous bracket to compare)")
            files_skipped += 1
            continue
        
        # Find the difference between this bracket and the previous one
        difference = find_recent_game_difference(current_bracket, previous_bracket)
        
        # If no difference found, skip this file
        if not difference:
            print("  No new game results found in this bracket")
            previous_bracket = copy.deepcopy(current_bracket)
            files_skipped += 1
            continue
        
        # Generate new filename
        new_filename = generate_new_filename(file_path, difference)
        
        print(f"  Found result: {difference[4]} {difference[3]} defeats {difference[6]} {difference[5]}")
        print(f"  Old filename: {os.path.basename(file_path)}")
        print(f"  New filename: {os.path.basename(new_filename)}")
        
        # Update the file
        if not args.dry_run:
            # Backup the original file if requested
            if args.backup_dir:
                backup_path = os.path.join(args.backup_dir, os.path.basename(file_path))
                shutil.copy2(file_path, backup_path)
                print(f"  Created backup: {backup_path}")
            
            # Rename the file
            if os.path.exists(new_filename):
                print(f"  Warning: File already exists: {new_filename}")
            else:
                os.rename(file_path, new_filename)
                print(f"  Renamed file successfully")
                files_renamed += 1
        else:
            files_renamed += 1  # Count as renamed for dry run
        
        # Update previous bracket for next iteration
        previous_bracket = copy.deepcopy(current_bracket)
        

    
    # Print summary
    print("\nProcessing complete!")
    print(f"Total files: {len(all_truth_files)}")
    print(f"Files processed: {files_processed}")
    print(f"Files renamed: {files_renamed}")
    print(f"Files skipped: {files_skipped}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 