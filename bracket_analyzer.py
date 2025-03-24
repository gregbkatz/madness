import json
import os
import glob
import shutil
from datetime import datetime

def analyze_bracket(json_file_path):
    """
    Analyze a bracket JSON file to determine the number of rounds and games with results.
    
    Args:
        json_file_path (str): Path to the bracket JSON file
        
    Returns:
        dict: Dictionary containing information about the bracket:
            - rounds: Total number of rounds in the tournament
            - completed_games: Number of games that have results
    """
    try:
        with open(json_file_path, 'r') as f:
            bracket = json.load(f)
        
        # Initialize counters
        completed_games = 0
        max_round = 0
        
        # Count completed games in each region for rounds 0-3
        regions = ['midwest', 'west', 'south', 'east']
        for region in regions:
            if region not in bracket:
                continue
                
            for round_idx, round_data in enumerate(bracket[region]):
                if round_idx == 0:
                    continue
                if round_idx > max_round and any(round_data):
                    max_round = round_idx
                    
                for team in round_data:
                    if team:  # If there's a team in this slot, a game has been completed
                        completed_games += 1
        
        # Check Final Four
        if 'finalFour' in bracket and any(bracket['finalFour']):
            if max_round < 4:
                max_round = 4
            for team in bracket['finalFour']:
                if team:
                    completed_games += 1
        
        # Check Championship
        if 'championship' in bracket and any(bracket['championship']):
            if max_round < 5:
                max_round = 5
            for team in bracket['championship']:
                if team:
                    completed_games += 1
        
        # Check Champion
        if 'champion' in bracket and bracket['champion']:
            if max_round < 6:
                max_round = 6
            completed_games += 1
        
        new_filename = f"round_{max_round}_game_{completed_games}.json"

        return {
            'rounds': max_round,
            'completed_games': completed_games,
            'new_filename': new_filename
        }
    
    except Exception as e:
        print(f"Error analyzing bracket file {json_file_path}: {str(e)}")
        return {'rounds': 0, 'completed_games': 0}

def process_bracket_files(directory_path, output_directory=None, analyze_only=False):
    """
    Process bracket files - analyze and optionally rename them.
    
    Args:
        directory_path (str): Path to directory containing bracket JSON files
        output_directory (str, optional): Directory to save renamed files. If None, rename in place.
        analyze_only (bool): If True, only analyze files without renaming
    """
    if not os.path.exists(directory_path):
        print(f"Directory {directory_path} does not exist.")
        return
    
    if output_directory and not os.path.exists(output_directory) and not analyze_only:
        os.makedirs(output_directory)
    
    # Get all JSON files in the directory
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    
    # Sort files by modification time to process in chronological order
    json_files.sort(key=os.path.getmtime)
    
    # Track game numbers by round
    game_counter = {}
    
    # Print header
    if analyze_only:
        print("\nFile Analysis (sorted by modification time):")
    else:
        print("\nFile Renaming Plan (Old Name → New Name):")
    print("-" * 60)
    
    for json_file in json_files:
        filename = os.path.basename(json_file)
        
        # Skip files that are already in the desired format if we're renaming
        if not analyze_only and filename.startswith("round_") and "_game_" in filename:
            continue
        
        # Analyze the bracket
        analysis = analyze_bracket(json_file)
        round_num = analysis['rounds']
        
        # Skip files with round 0 (these likely don't have any completed games)
        if round_num == 0:
            if analyze_only:
                print(f"{filename}: No completed rounds")
            else:
                print(f"{filename} → [SKIPPED - no completed rounds]")
            continue

        new_filename = analysis['new_filename']

        # Show the renaming mapping
        print(f"{filename} → {new_filename}")
        
        # Display analysis or renaming plan
        if analyze_only:
            continue

        # Perform the renaming if not in analyze_only mode
        if not analyze_only:
            if output_directory:
                new_path = os.path.join(output_directory, new_filename)
                shutil.copy2(json_file, new_path)
            else:
                new_path = os.path.join(directory_path, new_filename)
                # Don't overwrite existing files
                if os.path.exists(new_path) and json_file != new_path:
                    print(f"  File already exists: {new_path})")
                    continue
                
                if json_file != new_path:
                    os.rename(json_file, new_path)
    
    print("-" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze and rename bracket JSON files")
    parser.add_argument("--directory", "-d", required=True, help="Directory containing bracket JSON files")
    parser.add_argument("--output", "-o", help="Output directory for renamed files (if not specified, files are renamed in place)")
    parser.add_argument("--analyze-only", "-a", action="store_true", help="Only analyze files without renaming")
    
    args = parser.parse_args()
    
    # Process the bracket files
    process_bracket_files(args.directory, args.output, args.analyze_only) 