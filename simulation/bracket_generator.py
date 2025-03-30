"""
Bracket Generator Module

This module provides functionality to generate random bracket completions
based on a partially completed truth bracket.
"""

import copy
import random
import json
import os
from pprint import pprint

# Import bracket utility functions
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.bracket_utils import get_most_recent_truth_bracket
from bracket_logic import initialize_bracket, update_winners

class BracketGenerator:
    """Class that handles random bracket generation for Monte Carlo simulations."""
    
    def __init__(self, truth_bracket=None):
        """
        Initialize the bracket generator.
        
        Args:
            truth_bracket (dict, optional): A truth bracket to use as a base. 
                                           If None, the most recent truth bracket will be used.
        """
        self.truth_bracket = truth_bracket
        if self.truth_bracket is None:
            # Get the most recent truth bracket
            truth_file = get_most_recent_truth_bracket()
            if truth_file:
                with open(truth_file, 'r') as f:
                    self.truth_bracket = json.load(f)
            else:
                # If no truth bracket is available, initialize an empty one
                self.truth_bracket = initialize_bracket()
    
    def generate_random_bracket(self):
        """
        Generate a random bracket completion based on the truth bracket.
        
        Returns:
            dict: A randomly completed bracket
        """
        # Make a deep copy of the truth bracket to avoid modifying the original
        bracket = copy.deepcopy(self.truth_bracket)
        
        # Complete each region
        for region in ['east', 'west', 'south', 'midwest']:
            self._complete_region(bracket, region)
        
        # Complete the Final Four and Championship
        self._complete_final_four(bracket)
        self._complete_championship(bracket)
                
        return bracket
    
    def _calculate_win_probability(self, team1, team2):
        """
        Calculate the probability of team1 winning based on seed difference.
        
        Args:
            team1 (dict): First team
            team2 (dict): Second team
            
        Returns:
            float: Probability of team1 winning (between 0.01 and 0.99)
        """
        # Default to 50/50 if either team is missing or doesn't have seed
        if not team1 or not team2 or 'seed' not in team1 or 'seed' not in team2:
            return 0.5
            
        # Extract seeds
        seed1 = team1['seed']
        seed2 = team2['seed']
        
        # Calculate seed difference (absolute value)
        seed_diff = abs(seed1 - seed2)
            
        # Determine which team has the lower seed (lower is better)
        lower_seed_is_team1 = seed1 < seed2
        
        # Maximum seed difference is 15 (1 vs 16)
        # At max difference, the better team has 99% chance of winning
        # Linear interpolation between 50% and 99%
        max_diff = 15.0
        min_prob = 0.50  # Minimum probability of better seed (equal seed)
        max_prob = 0.99  # Maximum probability of better seed (for much better seed)
        
        # Calculate probability for the better seeded team
        # Linear interpolation: prob = min_prob + (seed_diff / max_diff) * (max_prob - min_prob)
        better_team_prob = min_prob + (seed_diff / max_diff) * (max_prob - min_prob)
        
        # Cap probability between min_prob and max_prob
        assert better_team_prob >= min_prob and better_team_prob <= max_prob, f"Better team probability {better_team_prob} is out of range"
        
        # Return probability for team1
        return better_team_prob if lower_seed_is_team1 else 1.0 - better_team_prob
    
    def _weighted_choice(self, team1, team2):
        """
        Make a weighted random choice between two teams based on seed.
        
        Args:
            team1 (dict): First team
            team2 (dict): Second team
            
        Returns:
            dict: The selected team
        """
        # Calculate probability of team1 winning
        team1_prob = self._calculate_win_probability(team1, team2)
        
        # Make a weighted random choice
        return team1 if random.random() < team1_prob else team2

    def _complete_region(self, bracket, region):
        """
        Complete a single region with random selections based on seed probabilities.
        
        Args:
            bracket (dict): The bracket to complete
            region (str): The region to complete ('east', 'west', 'south', 'midwest')
        """
        # Process each round (0-indexed)
        for round_idx in range(4):  # 4 rounds in a region (1st, 2nd, Sweet 16, Elite Eight)
            # Skip round 0 (first round) as it's always filled
            if round_idx == 0:
                continue
                
            games_in_round = 2 ** (4 - round_idx)
            next_round_idx = round_idx
            
            # For each game in the current round
            for game_idx in range(games_in_round):
                # Only fill in games that haven't been decided in the truth bracket
                if bracket[region][next_round_idx][game_idx] is None:
                    # Get the two teams from the previous round that would play in this game
                    prev_round_idx = next_round_idx - 1
                    team1_idx = game_idx * 2
                    team2_idx = game_idx * 2 + 1
                    
                    team1 = bracket[region][prev_round_idx][team1_idx]
                    team2 = bracket[region][prev_round_idx][team2_idx]
                    
                    # Use weighted choice based on seed differences
                    if team1 and team2:
                        winner = self._weighted_choice(team1, team2)
                        bracket[region][next_round_idx][game_idx] = winner
                    elif team1:
                        bracket[region][next_round_idx][game_idx] = team1
                    elif team2:
                        bracket[region][next_round_idx][game_idx] = team2
    
    def _complete_final_four(self, bracket):
        """
        Complete the Final Four round with seed-based probability selections.
        
        Args:
            bracket (dict): The bracket to complete
        """
        # Map regions to Final Four slots
        region_to_ff = {
            'midwest': 0,
            'west': 1, 
            'south': 2,
            'east': 3
        }
        
        # First, ensure each region's Elite Eight winner is in the Final Four
        for region, ff_idx in region_to_ff.items():
            # Check if this Final Four slot is already filled in the truth bracket
            if bracket['finalFour'][ff_idx] is None:
                # Get the Elite Eight winner for this region
                bracket['finalFour'][ff_idx] = self._weighted_choice(bracket[region][3][0], bracket[region][3][1])
        
        # Now complete the Championship matchups
        # First semifinal: south vs west
        if bracket['championship'][0] is None:
            team1 = bracket['finalFour'][region_to_ff['south']]  
            team2 = bracket['finalFour'][region_to_ff['west']]  
            if team1 and team2:
                winner = self._weighted_choice(team1, team2)
                bracket['championship'][0] = winner
        
        # Second semifinal: east vs midwest
        if bracket['championship'][1] is None:
            team1 = bracket['finalFour'][region_to_ff['east']]  
            team2 = bracket['finalFour'][region_to_ff['midwest']]  
            if team1 and team2:
                winner = self._weighted_choice(team1, team2)
                bracket['championship'][1] = winner
    
    def _complete_championship(self, bracket):
        """
        Complete the Championship game with a seed-based probability selection.
        
        Args:
            bracket (dict): The bracket to complete
        """
        # Check if the champion is already determined in the truth bracket
        if bracket['champion'] is None:
            team1 = bracket['championship'][0]
            team2 = bracket['championship'][1]
            
            if team1 and team2:
                champion = self._weighted_choice(team1, team2)
                bracket['champion'] = champion

def generate_random_completion(truth_bracket=None, count=1):
    """
    Generate one or more random bracket completions.
    
    Args:
        truth_bracket (dict, optional): The truth bracket to use as a base
        count (int, optional): Number of brackets to generate
        
    Returns:
        list: A list of randomly completed brackets
    """
    generator = BracketGenerator(truth_bracket)
    brackets = []
    
    for _ in range(count):
        brackets.append(generator.generate_random_bracket())
    
    return brackets if count > 1 else brackets[0]

def save_simulations(simulations, output_file=None):
    """
    Save a list of simulated brackets to a file.
    
    Args:
        simulations (list): List of simulated brackets
        output_file (str, optional): Path to save the file. If None, a default path will be used.
        
    Returns:
        str: Path to the saved file
    """
    import pickle
    
    if output_file is None:
        # Create the simulations directory if it doesn't exist
        os.makedirs('data/simulations', exist_ok=True)
        
        # Generate a default filename based on the current time
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/simulations/brackets_{timestamp}.bin"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save the simulations to a compressed pickle file
    with open(output_file, 'wb') as f:
        pickle.dump(simulations, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"Saved {len(simulations)} simulations to {output_file}")
    return output_file

def load_simulations(input_file):
    """
    Load simulated brackets from a file.
    
    Args:
        input_file (str): Path to the file containing simulated brackets
        
    Returns:
        list: List of simulated brackets
    """
    import pickle
    
    with open(input_file, 'rb') as f:
        simulations = pickle.load(f)
    
    print(f"Loaded {len(simulations)} simulations from {input_file}")
    return simulations

if __name__ == "__main__":
    # Simple test to generate and print a random bracket
    random_bracket = generate_random_completion()
    print("Generated random bracket:")
    pprint(random_bracket["champion"])
    
    # Optionally save to a file for testing
    # save_simulations([random_bracket]) 