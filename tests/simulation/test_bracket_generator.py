#!/usr/bin/env python3
"""
Unit tests for the bracket generator module.
"""

import unittest
import sys
import os
from unittest.mock import patch
import random

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Now we can import from the project root
from simulation.bracket_generator import BracketGenerator

class TestBracketGenerator(unittest.TestCase):
    """Test case for the BracketGenerator class."""
    
    def setUp(self):
        """Set up the test fixture."""
        # Create a simple truth bracket for testing
        self.truth_bracket = {
            'midwest': [[{}, {}], [None, None], [None], [None]],
            'west': [[{}, {}], [None, None], [None], [None]],
            'south': [[{}, {}], [None, None], [None], [None]],
            'east': [[{}, {}], [None, None], [None], [None]],
            'finalFour': [None, None, None, None],
            'championship': [None, None],
            'champion': None
        }
        
        # Initialize generator with test bracket
        self.generator = BracketGenerator(self.truth_bracket)
    
    def test_calculate_win_probability_same_seed(self):
        """Test that teams with the same seed have a 50/50 chance."""
        team1 = {'name': 'Team A', 'seed': 5}
        team2 = {'name': 'Team B', 'seed': 5}
        
        prob = self.generator._calculate_win_probability(team1, team2)
        
        self.assertAlmostEqual(prob, 0.5, "Teams with the same seed should have 50% win probability")
    
        # Reverse the teams
        team1, team2 = team2, team1
        prob = self.generator._calculate_win_probability(team1, team2)
        self.assertAlmostEqual(prob, 0.5, "Teams with the same seed should have 50% win probability")
        
    def test_calculate_win_probability_max_difference(self):
        """Test that a 1 seed vs 16 seed gives the 1 seed a 99% chance to win."""
        team1 = {'name': 'Team A', 'seed': 1}
        team2 = {'name': 'Team B', 'seed': 16}
        
        # Team1 should have 99% chance to win
        prob = self.generator._calculate_win_probability(team1, team2)
        self.assertAlmostEqual(prob, 0.99, places=2,
            msg="1 seed vs 16 seed should give 1 seed 99% chance to win")
        
        # Reverse the teams, Team1 should have 1% chance to win
        team1, team2 = team2, team1
        prob = self.generator._calculate_win_probability(team1, team2)
        self.assertAlmostEqual(prob, 0.01, places=2,
            msg="16 seed vs 1 seed should give 16 seed 1% chance to win")
    
    def test_calculate_win_probability_midway(self):
        """Test a seed difference of 7 (about halfway between 0 and 15)."""
        team1 = {'name': 'Team A', 'seed': 3}
        team2 = {'name': 'Team B', 'seed': 10}
        
        prob = self.generator._calculate_win_probability(team1, team2)
        
        self.assertAlmostEqual(prob, 0.729, places=2,
            msg="Seed difference of 7 should give appropriate interpolated probability")
        
        prob = self.generator._calculate_win_probability(team2, team1)
        self.assertAlmostEqual(prob, 0.271, places=2,
            msg="Seed difference of 7 should give appropriate interpolated probability")
        
    @patch('random.random')
    def test_weighted_choice_team1_wins(self, mock_random):
        """Test weighted choice when team1 should win."""
        team1 = {'name': 'Team A', 'seed': 1}
        team2 = {'name': 'Team B', 'seed': 16}
        
        # Mock random.random to return a value that ensures team1 wins
        # Team1 has ~99% chance to win, so any value below 0.99 should pick team1
        mock_random.return_value = 0.5
        
        result = self.generator._weighted_choice(team1, team2)
        
        self.assertEqual(result, team1, "Team1 should win with random value of 0.5")
    
    @patch('random.random')
    def test_weighted_choice_team2_wins(self, mock_random):
        """Test weighted choice when team2 should win."""
        team1 = {'name': 'Team A', 'seed': 1}
        team2 = {'name': 'Team B', 'seed': 16}
        
        # Mock random.random to return a value that ensures team2 wins
        # Team1 has ~99% chance to win, so any value above 0.99 should pick team2
        mock_random.return_value = 0.995
        
        result = self.generator._weighted_choice(team1, team2)
        
        self.assertEqual(result, team2, "Team2 should win with random value of 0.995")
    
    def test_weighted_choice_missing_team(self):
        """Test that if one team is missing, the other team is selected."""
        team1 = {'name': 'Team A', 'seed': 5}
        team2 = None
        
        result = self.generator._weighted_choice(team1, team2)
        self.assertEqual(result, team1, "If team2 is None, team1 should always be selected")
        
        team1 = None
        team2 = {'name': 'Team B', 'seed': 8}
        
        result = self.generator._weighted_choice(team1, team2)
        self.assertEqual(result, team2, "If team1 is None, team2 should always be selected")

    def test_weighted_choice_statistical_accuracy(self):
        """Test that weighted choice produces statistically accurate results over many trials."""
        # Setup teams with a significant seed difference
        team1 = {'name': 'Team A', 'seed': 1}  # 1 seed
        team2 = {'name': 'Team B', 'seed': 8}  # 8 seed
        
        # Calculate expected probability
        expected_prob = self.generator._calculate_win_probability(team1, team2)
        
        # Run many trials
        num_trials = 10000
        team1_wins = 0
        
        for _ in range(num_trials):
            result = self.generator._weighted_choice(team1, team2)
            if result == team1:
                team1_wins += 1
                
        # Calculate actual win percentage
        actual_prob = team1_wins / num_trials
        
        # Allow for statistical variation (within 3% of expected)
        margin = 0.03
        self.assertTrue(abs(actual_prob - expected_prob) < margin,
            msg=f"Expected probability {expected_prob:.4f}, actual {actual_prob:.4f} over {num_trials} trials")

if __name__ == '__main__':
    unittest.main() 