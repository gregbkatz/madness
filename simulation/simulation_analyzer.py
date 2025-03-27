"""
Simulation Analyzer Module

This module provides functionality to analyze Monte Carlo simulation results,
calculating statistics on bracket performance across many simulations.
"""

import os
import json
import numpy as np
import pickle
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime

# Import scoring functions
from utils.scoring import compare_with_truth, calculate_points_for_pick

class BracketAnalyzer:
    """Class for analyzing Monte Carlo simulation results"""
    
    def __init__(self, simulations=None, user_brackets=None):
        """
        Initialize the bracket analyzer.
        
        Args:
            simulations (list, optional): List of simulated brackets
            user_brackets (dict, optional): Dictionary of user brackets {username: bracket}
        """
        self.simulations = simulations
        self.user_brackets = user_brackets
        self.scores = None
        self.rankings = None
        self.analysis_results = None
        
    def load_simulations(self, simulation_file):
        """
        Load simulations from a file.
        
        Args:
            simulation_file (str): Path to the simulation file
            
        Returns:
            list: The loaded simulations
        """
        with open(simulation_file, 'rb') as f:
            self.simulations = pickle.load(f)
        print(f"Loaded {len(self.simulations)} simulations from {simulation_file}")
        return self.simulations
    
    def load_user_brackets(self, user_brackets_dir='saved_brackets'):
        """
        Load all user brackets from the saved_brackets directory.
        
        Args:
            user_brackets_dir (str): Directory containing user brackets
            
        Returns:
            dict: Dictionary of user brackets {username: bracket}
        """
        user_brackets = {}
        
        # Get a list of all users by looking at bracket filenames
        users = set()
        for filename in os.listdir(user_brackets_dir):
            if filename.startswith('bracket_') and filename.endswith('.json'):
                # Extract username from filename format: bracket_username_timestamp.json
                parts = filename.split('_')
                if len(parts) >= 3:  # We need at least 3 parts: bracket, username, timestamp
                    # The timestamp part is the last two segments (YYYYMMDD_HHMMSS)
                    # So the username is all parts between 'bracket_' and the timestamp
                    # This handles usernames with underscores like "MiloPiPi_bandwagon"
                    username = '_'.join(parts[1:-2])
                    users.add(username)
        
        # For each user, find their most recent bracket
        for username in users:
            # Skip 'anonymous' user
            if username == 'anonymous':
                continue
                
            most_recent_file = None
            most_recent_time = 0
            
            # Find the most recent bracket for this user
            for filename in os.listdir(user_brackets_dir):
                # Need to reconstruct proper file pattern for usernames with underscores
                # e.g. 'bracket_MiloPiPi_bandwagon_20230326_123456.json'
                if filename.startswith(f'bracket_{username}_') and filename.endswith('.json'):
                    # Make sure this is the exact username and not a prefix of another username
                    # by extracting the username from the filename and comparing
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        file_username = '_'.join(parts[1:-2])
                        if file_username != username:
                            continue
                    
                    file_path = os.path.join(user_brackets_dir, filename)
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time > most_recent_time:
                        most_recent_time = file_time
                        most_recent_file = file_path
            
            # Load the most recent bracket
            if most_recent_file:
                try:
                    with open(most_recent_file, 'r') as f:
                        bracket = json.load(f)
                    user_brackets[username] = bracket
                except Exception as e:
                    print(f"Error loading bracket for {username}: {str(e)}")
        
        self.user_brackets = user_brackets
        print(f"Loaded brackets for {len(user_brackets)} users")
        return user_brackets
    
    def calculate_scores(self):
        """
        Calculate scores for all user brackets against all simulations.
        
        Returns:
            numpy.ndarray: 2D array of scores [users, simulations]
        """
        if not self.simulations or not self.user_brackets:
            raise ValueError("Simulations and user brackets must be loaded first")
        
        # Create a 2D array to store scores [users, simulations]
        num_users = len(self.user_brackets)
        num_simulations = len(self.simulations)
        scores = np.zeros((num_users, num_simulations), dtype=np.int32)
        
        # Convert user_brackets dict to list for indexing
        usernames = list(self.user_brackets.keys())
        
        # For each simulation
        for sim_idx, simulation in enumerate(self.simulations):
            if sim_idx % 100 == 0:
                print(f"Processing simulation {sim_idx}/{num_simulations}")
                
            # For each user
            for user_idx, username in enumerate(usernames):
                user_bracket = self.user_brackets[username]
                
                # Calculate score using the compare_with_truth function
                result = compare_with_truth(user_bracket, simulation)
                scores[user_idx, sim_idx] = result['total_points']
        
        self.scores = scores
        self.usernames = usernames
        return scores
    
    def calculate_rankings(self):
        """
        Calculate rankings for all users across all simulations.
        Properly handles ties (users with the same score get the same rank).
        
        Returns:
            numpy.ndarray: 2D array of rankings [users, simulations]
        """
        if self.scores is None:
            self.calculate_scores()
        
        # Create a 2D array to store rankings
        num_users = len(self.usernames)
        num_simulations = self.scores.shape[1]
        
        print(f"Calculating rankings for {num_users} users across {num_simulations} simulations")
        
        # Handle edge case: if we have zero users, return empty array
        if num_users == 0:
            print("Warning: No users found. Returning empty rankings.")
            self.rankings = np.array([], dtype=np.int32)
            return self.rankings
            
        # Handle edge case: if we have only one user, they always rank 1st
        if num_users == 1:
            print("Only one user found. Setting rank to 1 for all simulations.")
            self.rankings = np.ones((1, num_simulations), dtype=np.int32)
            return self.rankings
        
        # Create array to store rankings [users, simulations]
        rankings = np.zeros((num_users, num_simulations), dtype=np.int32)
        
        # For each simulation, calculate rankings
        for sim_idx in range(num_simulations):
            # Get scores for this simulation
            sim_scores = self.scores[:, sim_idx]
            
            # Calculate rankings with tie handling
            # First, sort scores in descending order
            sorted_indices = np.argsort(-sim_scores)
            sorted_scores = sim_scores[sorted_indices]
            
            # Initialize ranks
            ranks = np.zeros(num_users, dtype=np.int32)
            
            # Assign ranks
            current_rank = 1
            for i in range(num_users):
                if i > 0 and sorted_scores[i] < sorted_scores[i-1]:
                    current_rank = i + 1
                ranks[sorted_indices[i]] = current_rank
            
            # Store rankings for this simulation
            rankings[:, sim_idx] = ranks
        
        self.rankings = rankings
        return rankings
    
    def analyze_results(self):
        """
        Analyze the rankings to compute statistics for each user.
        
        Returns:
            dict: Dictionary mapping usernames to statistics
        """
        if self.rankings is None:
            self.calculate_rankings()
            
        # Initialize result dictionary
        self.analysis_results = {}
        
        # Number of users and simulations
        num_users = len(self.usernames)
        num_simulations = len(self.simulations)
        
        # Check array shapes to understand structure
        rankings_shape = self.rankings.shape
        scores_shape = self.scores.shape
        
        print(f"DEBUG: Rankings shape: {rankings_shape}, Scores shape: {scores_shape}")
        print(f"DEBUG: Number of users: {num_users}, Number of simulations: {num_simulations}")
        
        # For each user, calculate rank statistics
        for i, username in enumerate(self.usernames):
            # Skip if user index is out of bounds
            if i >= rankings_shape[0]:
                print(f"Warning: User index {i} out of bounds for rankings with shape {rankings_shape}")
                continue
                
            # Extract all rankings for this user across simulations
            try:
                # Different handling based on array dimensions and sizes
                if num_simulations == 1:
                    # For a single simulation
                    if rankings_shape[1] == 1:
                        # If we have a 2D array with shape [num_users, 1]
                        user_rankings = [self.rankings[i, 0]]
                        user_scores = [self.scores[i, 0]]
                    else:
                        # If we have a 2D array with ranks for each user
                        user_rankings = [self.rankings[i, j] for j in range(min(num_simulations, rankings_shape[1]))]
                        user_scores = [self.scores[i, j] for j in range(min(num_simulations, scores_shape[1]))]
                else:
                    # For multiple simulations
                    user_rankings = []
                    user_scores = []
                    for j in range(min(num_simulations, rankings_shape[1])):
                        user_rankings.append(self.rankings[i, j])
                        user_scores.append(self.scores[i, j])
            except Exception as e:
                print(f"Error extracting data for user {username} (index {i}): {str(e)}")
                # Use empty data as fallback
                user_rankings = [1]  # Default to first place
                user_scores = [0]    # Default to zero score
                
            # Calculate the average rank
            avg_rank = np.mean(user_rankings)
            
            # Calculate the median rank
            median_rank = np.median(user_rankings)
            
            # Calculate the percentage of simulations where the user ranks first
            pct_first_place = (np.array(user_rankings) == 1).sum() / num_simulations * 100
            
            # Calculate the percentage of simulations where the user ranks last
            pct_last_place = (np.array(user_rankings) == num_users).sum() / num_simulations * 100
            
            # Find the best (minimum) and worst (maximum) ranks
            min_rank = np.min(user_rankings)
            max_rank = np.max(user_rankings)
            
            # Find the maximum and minimum scores
            max_score = np.max(user_scores)
            min_score = np.min(user_scores)
            
            # Store the statistics
            self.analysis_results[username] = {
                'avg_rank': avg_rank,
                'median_rank': median_rank,
                'pct_first_place': pct_first_place,
                'pct_last_place': pct_last_place,
                'min_rank': min_rank,
                'max_rank': max_rank,
                'max_score': max_score,
                'min_score': min_score
            }
        
        return self.analysis_results
    
    def save_analysis(self, output_file=None):
        """
        Save analysis results to a file.
        
        Args:
            output_file (str, optional): Path to save the file
            
        Returns:
            str: Path to the saved file
        """
        if self.analysis_results is None:
            self.analyze_results()
        
        if output_file is None:
            # Create the simulations directory if it doesn't exist
            os.makedirs('data/simulations', exist_ok=True)
            
            # Generate a default filename based on current time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_count = len(self.simulations)
            output_file = f"data/simulations/analysis_{sim_count}_{timestamp}.json"
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Convert numpy values to Python native types for JSON serialization
        serializable_results = {}
        for username, stats in self.analysis_results.items():
            serializable_stats = {}
            for key, value in stats.items():
                if isinstance(value, np.integer):
                    serializable_stats[key] = int(value)
                elif isinstance(value, np.floating):
                    serializable_stats[key] = float(value)
                elif isinstance(value, np.ndarray):
                    serializable_stats[key] = value.tolist()
                else:
                    serializable_stats[key] = value
            serializable_results[username] = serializable_stats
        
        # Save the analysis results to a JSON file
        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Saved analysis results to {output_file}")
        return output_file
    
    def visualize_rank_distribution(self, username=None, output_file=None):
        """
        Visualize the rank distribution for a user or all users.
        
        Args:
            username (str, optional): Username to visualize. If None, visualize all users.
            output_file (str, optional): Path to save the visualization
            
        Returns:
            matplotlib.figure.Figure: The visualization figure
        """
        if self.analysis_results is None:
            self.analyze_results()
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Determine the users to visualize
        if username:
            if username not in self.analysis_results:
                raise ValueError(f"Username '{username}' not found in analysis results")
            users_to_plot = [username]
        else:
            # Limit to top 10 users if visualizing all
            users_to_plot = list(self.analysis_results.keys())[:10]
        
        # Plot the rank distribution for each user
        x = np.arange(1, len(self.usernames) + 1)
        width = 0.8 / len(users_to_plot)
        
        for i, user in enumerate(users_to_plot):
            user_data = self.analysis_results[user]
            distribution = user_data['rank_distribution']
            
            # Convert distribution to array
            y = np.zeros(len(self.usernames))
            for rank, count in distribution.items():
                if int(rank) <= len(y):
                    y[int(rank) - 1] = count / len(self.simulations) * 100
            
            # Plot the distribution
            offset = (i - len(users_to_plot)/2 + 0.5) * width
            ax.bar(x + offset, y, width, label=user)
        
        # Add labels and legend
        ax.set_xlabel('Rank')
        ax.set_ylabel('Percentage of Simulations (%)')
        ax.set_title('Rank Distribution Across Simulations')
        ax.set_xticks(x)
        ax.set_xticklabels(x)
        ax.legend()
        
        # Save the figure if requested
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Saved visualization to {output_file}")
        
        return fig

# Standalone functions for simpler use cases

def analyze_simulations(simulation_file, users_dir='saved_brackets', output_file=None):
    """
    Analyze a simulation file and calculate statistics for all users.
    
    Args:
        simulation_file (str): Path to the simulation file
        users_dir (str): Directory containing user brackets
        output_file (str, optional): Path to save the analysis results
        
    Returns:
        dict: Analysis results
    """
    analyzer = BracketAnalyzer()
    analyzer.load_simulations(simulation_file)
    analyzer.load_user_brackets(users_dir)
    analyzer.calculate_scores()
    analyzer.calculate_rankings()
    results = analyzer.analyze_results()
    
    if output_file:
        analyzer.save_analysis(output_file)
    
    return results

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        simulation_file = sys.argv[1]
        
        # Analyze the simulations
        results = analyze_simulations(simulation_file)
        
        # Print a summary of the results
        print("\nMonte Carlo Simulation Analysis Results:")
        print("----------------------------------------")
        print(f"Number of simulations: {len(results)}")
        
        # Sort users by name
        sorted_users = sorted(results.items(), key=lambda x: x[0].lower())
        
        # Print a full table of all users
        print("\nFull User Analysis Results (sorted by name):")
        # Define column widths
        username_width = 15
        numeric_width = 10
        rank_width = 6
        
        # Calculate total table width
        table_width = (username_width + 2) + (numeric_width + 2) * 4 + (rank_width + 2) * 2 + 1
        
        print("-" * table_width)
        print(f"| {'USERNAME':<{username_width}} | {'AVG RANK':<{numeric_width}} | {'WIN %':<{numeric_width}} | {'LAST %':<{numeric_width}} | {'BEST':<{rank_width}} | {'WORST':<{rank_width}} | {'MIN SCORE':<{numeric_width}} | {'MAX SCORE':<{numeric_width}} |")
        print(f"|{'-' * (username_width + 2)}|{'-' * (numeric_width + 2)}|{'-' * (numeric_width + 2)}|{'-' * (numeric_width + 2)}|{'-' * (rank_width + 2)}|{'-' * (rank_width + 2)}|{'-' * (numeric_width + 2)}|{'-' * (numeric_width + 2)}|")
        
        for username, stats in sorted_users:
            # Format avg_rank to 1 decimal place
            avg_rank_str = f"{stats['avg_rank']:.1f}"
            
            # Format percentages - show as integers unless between 0 and 1
            def format_percentage(pct):
                if 0 < pct < 1:
                    return "<1"
                else:
                    return f"{int(pct)}"
                    
            win_pct_str = format_percentage(stats['pct_first_place'])
            last_pct_str = format_percentage(stats['pct_last_place'])
            
            print(f"| {username:<{username_width}} | {avg_rank_str:<{numeric_width}} | {win_pct_str:<{numeric_width}} | {last_pct_str:<{numeric_width}} | {stats['min_rank']:<{rank_width}} | {stats['max_rank']:<{rank_width}} | {stats['min_score']:<{numeric_width}} | {stats['max_score']:<{numeric_width}} |")
        
        print("-" * table_width)
    else:
        print("Please provide a simulation file")
        print("Usage: python simulation_analyzer.py <simulation_file>") 