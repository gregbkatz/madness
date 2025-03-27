#!/usr/bin/env python3
"""
Generate Monte Carlo Simulations for All Truth Brackets

This script generates Monte Carlo simulations for all truth brackets,
creating a comprehensive set of simulations for different stages of the tournament.
"""

import os
import argparse
import json
from datetime import datetime
import subprocess
import time

from utils.bracket_utils import get_sorted_truth_files

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate Monte Carlo simulations for all truth brackets'
    )
    parser.add_argument(
        '--count', 
        type=int, 
        default=10,
        help='Number of simulations to generate for each truth bracket (default: 1000)'
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
    
    return parser.parse_args()

def main():
    """Main function to run the simulation generation for all truth brackets."""
    args = parse_arguments()
    
    # Get all truth bracket files
    truth_files = get_sorted_truth_files()
    
    if not truth_files:
        print("Error: No truth bracket files found")
        return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Found {len(truth_files)} truth bracket files")
    print(f"Generating {args.count} simulations for each file...")
    
    for i, truth_file in enumerate(truth_files):
        print(f"\nProcessing truth file {i+1}/{len(truth_files)}: {truth_file}")
        
        # Run the simulation for this truth file
        try:
            cmd = f"python generate_simulations.py --count {args.count} --truth-file {truth_file} --output-dir {args.output_dir}"
            print(f"Running command: {cmd}")
            
            # Run the simulation
            start_time = time.time()
            result = subprocess.run(cmd, shell=True, check=True)
            elapsed = time.time() - start_time
            
            print(f"Simulation for {os.path.basename(truth_file)} completed in {elapsed:.2f} seconds")
            
            # Run the analysis for this simulation
            # Get the most recent simulation file
            simulation_files = [f for f in os.listdir(args.output_dir) if f.endswith('.bin')]
            if simulation_files:
                simulation_files.sort(key=lambda x: os.path.getmtime(os.path.join(args.output_dir, x)), reverse=True)
                latest_sim_file = os.path.join(args.output_dir, simulation_files[0])
                
                # Run the analysis
                truth_basename = os.path.basename(truth_file)
                truth_id = os.path.splitext(truth_basename)[0]  # Remove extension
                analysis_file = os.path.join(args.output_dir, f"analysis_{truth_id}_{args.count}_brackets.json")
                
                cmd = f"python analyze_simulations.py --simulation-file {latest_sim_file} --output-dir {args.output_dir} --user-brackets-dir saved_brackets"
                print(f"\nRunning analysis command: {cmd}")
                
                start_time = time.time()
                result = subprocess.run(cmd, shell=True, check=True)
                elapsed = time.time() - start_time
                
                print(f"Analysis for {os.path.basename(truth_file)} completed in {elapsed:.2f} seconds")
                
                # Rename the analysis file to include the truth file ID
                analysis_files = [f for f in os.listdir(args.output_dir) if f.startswith('analysis_') and f.endswith('.json')]
                if analysis_files:
                    analysis_files.sort(key=lambda x: os.path.getmtime(os.path.join(args.output_dir, x)), reverse=True)
                    latest_analysis = os.path.join(args.output_dir, analysis_files[0])
                    
                    os.rename(latest_analysis, analysis_file)
                    print(f"Renamed analysis file to: {analysis_file}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error running simulation for {truth_file}: {str(e)}")
            continue
    
    print("\nAll simulations completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main()) 