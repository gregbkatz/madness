#!/usr/bin/env python3
"""
Generate Monte Carlo Simulations

This script generates Monte Carlo simulations of the tournament based on
the current truth bracket. It creates a specified number of random bracket
completions and saves them to a file for later analysis.
"""

import os
import argparse
import json
from datetime import datetime

from simulation.monte_carlo import run_monte_carlo
from utils.bracket_utils import get_most_recent_truth_bracket, get_sorted_truth_files

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate Monte Carlo simulations for March Madness brackets'
    )
    parser.add_argument(
        '--count', 
        type=int, 
        default=10000,
        help='Number of simulations to generate (default: 10000)'
    )
    parser.add_argument(
        '--truth-file',
        type=str,
        help='Path to truth bracket file (default: most recent truth file)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/simulations',
        help='Directory to save simulation results (default: data/simulations)'
    )
    parser.add_argument(
        '--processes',
        type=int,
        default=None,
        help='Number of processes to use (default: CPU count - 1)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size for parallel processing (default: 1000)'
    )
    
    return parser.parse_args()

def main():
    """Main function to run the simulation generation."""
    args = parse_arguments()
    
    # Get the truth bracket file
    truth_file = args.truth_file
    if not truth_file:
        truth_file = get_most_recent_truth_bracket()
        if not truth_file:
            print("Error: No truth bracket file found")
            print("Please specify a truth bracket file with --truth-file")
            return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Generating {args.count} simulations using truth file: {truth_file}")
    
    # Run the simulation
    try:
        # Load the truth bracket
        with open(truth_file, 'r') as f:
            truth_bracket = json.load(f)
            
        # Special case for very small simulation counts
        # When we only need 1-3 simulations, use a direct approach without multiprocessing
        if args.count <= 3:
            # Import directly to avoid circular imports
            from simulation.bracket_generator import generate_random_completion, save_simulations
            
            print(f"Generating {args.count} simulations directly (no multiprocessing)")
            simulations = generate_random_completion(truth_bracket, count=args.count)
            
            # Make sure simulations is a list
            if args.count == 1:
                simulations = [simulations]
                
            # Generate filename 
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            basename = os.path.basename(truth_file)
            if basename.startswith("round_") and "_game_" in basename:
                truth_id = os.path.splitext(basename)[0]  # Remove extension
            else:
                truth_id = "custom"
                
            output_file = f"{args.output_dir}/brackets_{truth_id}_{args.count}_{timestamp}.bin"
            
            # Save the simulations
            save_simulations(simulations, output_file)
            print(f"Saved {args.count} simulations to: {output_file}")
        else:
            # For larger counts, use the regular multiprocessing approach
            from simulation.monte_carlo import run_monte_carlo
            
            output_file = run_monte_carlo(
                truth_bracket_file=truth_file,
                num_simulations=args.count
            )
        
        print("\nSimulation generation completed successfully!")
        print(f"Results saved to: {output_file}")
        
        return 0
    except Exception as e:
        print(f"Error generating simulations: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 