"""
Bracket Utilities Module

This module provides utility functions for working with bracket files,
including loading, saving, and manipulating bracket data.
"""

import os
import json
import glob
from datetime import datetime

def get_sorted_truth_files(truth_dir="truth_brackets"):
    """
    Get a sorted list of truth bracket files from newest to oldest.
    
    Args:
        truth_dir (str): Directory containing truth bracket files
        
    Returns:
        list: Sorted list of truth bracket file paths (newest first)
    """
    # Get all JSON files in the truth_brackets directory
    json_files = glob.glob(os.path.join(truth_dir, "*.json"))
    
    # Sort files by modification time (newest first)
    sorted_files = sorted(json_files, key=os.path.getmtime, reverse=True)
    
    return sorted_files

def get_most_recent_truth_bracket(truth_dir="truth_brackets"):
    """
    Get the most recent truth bracket file.
    
    Args:
        truth_dir (str): Directory containing truth bracket files
        
    Returns:
        str: Path to the most recent truth bracket file, or None if no files exist
    """
    sorted_files = get_sorted_truth_files(truth_dir)
    
    if sorted_files:
        return sorted_files[0]
    
    return None

def extract_timestamp_from_filename(filename):
    """
    Extract a timestamp from a bracket filename.
    
    Args:
        filename (str): Bracket filename (format: bracket_username_YYYYMMDD_HHMMSS.json)
        
    Returns:
        datetime: Extracted timestamp, or None if the format is invalid
    """
    try:
        # Extract the timestamp part (assuming the format is bracket_username_YYYYMMDD_HHMMSS.json)
        parts = os.path.basename(filename).split('_')
        if len(parts) >= 3:
            # The timestamp could be split into date and time parts
            date_str = parts[-2]
            time_str = parts[-1].split('.')[0]  # Remove .json extension
            
            # Try to parse as YYYYMMDD_HHMMSS
            try:
                timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                return timestamp
            except ValueError:
                # If that format fails, try alternatives
                pass
    except Exception:
        pass
    
    # If all parsing attempts fail, return None
    return None

def get_user_bracket_for_user(username, brackets_dir="saved_brackets"):
    """
    Get the most recent bracket for a specific user.
    
    Args:
        username (str): Username to find bracket for
        brackets_dir (str): Directory containing saved brackets
        
    Returns:
        dict: The user's bracket, or None if no bracket exists
    """
    most_recent_file = None
    most_recent_time = 0
    
    # Check if the directory exists
    if not os.path.exists(brackets_dir):
        print(f"Directory does not exist: {brackets_dir}")
        return None
    
    # Find the most recent bracket for this user
    for filename in os.listdir(brackets_dir):
        if filename.startswith(f'bracket_{username}_') and filename.endswith('.json'):
            # Extract the username from the filename to ensure exact match (for usernames with underscores)
            parts = filename.split('_')
            if len(parts) >= 4:  # We need at least 4 parts: 'bracket', username parts, date, time
                file_username = '_'.join(parts[1:-2])
                if file_username != username:
                    continue
                    
            file_path = os.path.join(brackets_dir, filename)
            file_time = os.path.getmtime(file_path)
            
            if file_time > most_recent_time:
                most_recent_time = file_time
                most_recent_file = file_path
    
    # Load the bracket if found
    if most_recent_file:
        try:
            with open(most_recent_file, 'r') as f:
                bracket = json.load(f)
            print(f"Loaded bracket for {username} from {most_recent_file}")
            return bracket
        except Exception as e:
            print(f"Error loading bracket for {username}: {str(e)}")
    else:
        print(f"No bracket found for user: {username}")
    
    return None

def get_all_user_brackets(brackets_dir="saved_brackets"):
    """
    Get the most recent bracket for all users.
    
    Args:
        brackets_dir (str): Directory containing saved brackets
        
    Returns:
        dict: Dictionary of user brackets {username: bracket}
    """
    user_brackets = {}
    
    # Check if the directory exists
    if not os.path.exists(brackets_dir):
        print(f"Directory does not exist: {brackets_dir}")
        return user_brackets
    
    # Get a list of all users by looking at bracket filenames
    users = set()
    for filename in os.listdir(brackets_dir):
        if filename.startswith('bracket_') and filename.endswith('.json'):
            # Extract username from filename format: bracket_username_timestamp.json
            parts = filename.split('_')
            if len(parts) >= 4:  # We need at least 4 parts: 'bracket', username parts, date, time
                # Username is everything between 'bracket_' and the timestamp (date_time)
                username = '_'.join(parts[1:-2])  # Join all parts except 'bracket', date and time
                users.add(username)
    
    # For each user, find their most recent bracket
    for username in users:
        # Skip 'anonymous' user
        if username == 'anonymous':
            continue
            
        bracket = get_user_bracket_for_user(username, brackets_dir)
        if bracket:
            user_brackets[username] = bracket
    
    print(f"Loaded brackets for {len(user_brackets)} users")
    return user_brackets

def save_bracket(bracket, username, brackets_dir="saved_brackets"):
    """
    Save a bracket to a file.
    
    Args:
        bracket (dict): The bracket to save
        username (str): Username to associate with the bracket
        brackets_dir (str): Directory to save the bracket in
        
    Returns:
        str: Path to the saved file
    """
    # Ensure the directory exists
    os.makedirs(brackets_dir, exist_ok=True)
    
    # Create a filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{brackets_dir}/bracket_{username}_{timestamp}.json"
    
    # Write the bracket to the file
    with open(filename, 'w') as f:
        json.dump(bracket, f, indent=2)
    
    print(f"Saved bracket to {filename}")
    return filename

if __name__ == "__main__":
    # Example usage
    most_recent = get_most_recent_truth_bracket()
    if most_recent:
        print(f"Most recent truth bracket: {most_recent}")
        
    all_user_brackets = get_all_user_brackets()
    print(f"Found brackets for {len(all_user_brackets)} users") 