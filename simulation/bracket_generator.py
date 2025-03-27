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
        
        # Update winners for rendering
        bracket = update_winners(bracket)
        
        return bracket
    
    def _complete_region(self, bracket, region):
        """
        Complete a single region with random selections.
        
        Args:
            bracket (dict): The bracket to complete
            region (str): The region to complete ('east', 'west', 'south', 'midwest')
        """
        # Process each round (0-indexed)
        for round_idx in range(4):  # 4 rounds in a region (1st, 2nd, Sweet 16, Elite Eight)
            # Skip round 0 (first round) as it's always filled
            if round_idx == 0:
                continue
                
            games_in_round = 2 ** (3 - round_idx)
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
                    
                    # Randomly choose a winner (50/50 chance for now)
                    # Could be enhanced later to use seed-based probabilities
                    if team1 and team2:
                        winner = random.choice([team1, team2])
                        bracket[region][next_round_idx][game_idx] = winner
                    elif team1:
                        bracket[region][next_round_idx][game_idx] = team1
                    elif team2:
                        bracket[region][next_round_idx][game_idx] = team2
    
    def _complete_final_four(self, bracket):
        """
        Complete the Final Four round with random selections.
        
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
                elite_eight_winner = bracket[region][3][0] if bracket[region][3] and len(bracket[region][3]) > 0 else None
                if elite_eight_winner:
                    bracket['finalFour'][ff_idx] = elite_eight_winner
        
        # Now complete the Championship matchups
        # First semifinal: midwest vs west (slots 0 and 1)
        if bracket['championship'][0] is None:
            team1 = bracket['finalFour'][0]  # midwest
            team2 = bracket['finalFour'][1]  # west
            if team1 and team2:
                winner = random.choice([team1, team2])
                bracket['championship'][0] = winner
        
        # Second semifinal: south vs east (slots 2 and 3)
        if bracket['championship'][1] is None:
            team1 = bracket['finalFour'][2]  # south
            team2 = bracket['finalFour'][3]  # east
            if team1 and team2:
                winner = random.choice([team1, team2])
                bracket['championship'][1] = winner
    
    def _complete_championship(self, bracket):
        """
        Complete the Championship game with a random selection.
        
        Args:
            bracket (dict): The bracket to complete
        """
        # Check if the champion is already determined in the truth bracket
        if bracket['champion'] is None:
            team1 = bracket['championship'][0]
            team2 = bracket['championship'][1]
            
            if team1 and team2:
                champion = random.choice([team1, team2])
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