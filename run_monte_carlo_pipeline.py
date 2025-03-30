#!/usr/bin/env python3
"""
Run Monte Carlo Pipeline

This script runs the entire Monte Carlo simulation pipeline, including:
1. Generating simulations
2. Analyzing simulation results
3. Integrating results with the main application

This is designed to be a one-stop solution for running the entire Monte Carlo analysis.
"""

import os
import argparse
import subprocess
import json
import time
import shutil
from datetime import datetime

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run the entire Monte Carlo simulation pipeline'
    )
    parser.add_argument(
        '--count', 
        type=int, 
        default=1000,
        help='Number of simulations to generate (default: 1000)'
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
        '--user-brackets-dir',
        type=str,
        default='saved_brackets',
        help='Directory containing user brackets (default: saved_brackets)'
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Generate visualizations of the results'
    )
    parser.add_argument(
        '--skip-generation',
        action='store_true',
        help='Skip the simulation generation step (use existing simulations)'
    )
    parser.add_argument(
        '--skip-analysis',
        action='store_true',
        help='Skip the analysis step'
    )
    parser.add_argument(
        '--processes',
        type=int,
        default=None,
        help='Number of processes to use for simulation generation'
    )
    
    return parser.parse_args()

def run_generation(args):
    """Run the simulation generation step."""
    print("\n===== Step 1: Generating Simulations =====\n")
    
    # Build the command
    cmd = ["python", "generate_simulations.py"]
    
    # Add arguments
    cmd.extend(["--count", str(args.count)])
    
    if args.truth_file:
        cmd.extend(["--truth-file", args.truth_file])
    
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    
    if args.processes:
        cmd.extend(["--processes", str(args.processes)])
    
    # Run the generation script
    start_time = time.time()
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Extract the output file from the output
        output_file = None
        for line in result.stdout.split('\n'):
            if line.startswith("Results saved to:"):
                output_file = line.split(":", 1)[1].strip()
                break
        
        elapsed = time.time() - start_time
        print(f"Generation completed in {elapsed:.2f} seconds")
        
        return output_file
    
    except subprocess.CalledProcessError as e:
        print("Error generating simulations:")
        print(e.stderr)
        return None

def run_analysis(args, simulation_file):
    """Run the simulation analysis step."""
    print("\n===== Step 2: Analyzing Simulation Results =====\n")
    
    # Generate a descriptive filename for the analysis results
    if args.truth_file:
        # Extract a descriptive part from the truth file name
        basename = os.path.basename(args.truth_file)
        if basename.startswith("round_") and "_game_" in basename:
            # If it's using the round_X_game_Y format
            desc_part = basename.split(" ")[0]
            file_name = f"analysis_{desc_part}_{args.count}_brackets.json"
        else:
            # For non-standard truth files, use the timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            file_name = f"monte_carlo_{timestamp}_{args.count}_brackets.json"
    else:
        # Fallback to a generic filename if no truth file provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"analysis_{timestamp}.json"
    
    # Set the specific output file
    output_file = os.path.join(args.output_dir, file_name)
    
    # Build the command
    cmd = ["python", "analyze_simulations.py"]
    
    # Add arguments
    cmd.extend(["--simulation-file", simulation_file])
    cmd.extend(["--output-dir", args.output_dir])
    cmd.extend(["--output-file", file_name])  # Use our descriptive filename
    
    if args.user_brackets_dir:
        cmd.extend(["--user-brackets-dir", args.user_brackets_dir])
    
    if args.visualize:
        cmd.append("--visualize")
    
    # Run the analysis script
    start_time = time.time()
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        elapsed = time.time() - start_time
        print(f"Analysis completed in {elapsed:.2f} seconds")
        
        return output_file
    
    except subprocess.CalledProcessError as e:
        print("Error analyzing simulations:")
        print(e.stderr)
        return None

def find_most_recent_simulation_file(output_dir):
    """Find the most recent simulation file in the output directory."""
    if not os.path.exists(output_dir):
        return None
        
    sim_files = []
    for filename in os.listdir(output_dir):
        if filename.startswith("brackets_") and filename.endswith(".bin"):
            file_path = os.path.join(output_dir, filename)
            sim_files.append((file_path, os.path.getmtime(file_path)))
    
    if not sim_files:
        return None
        
    # Sort by modification time (newest first)
    sim_files.sort(key=lambda x: x[1], reverse=True)
    
    return sim_files[0][0]

def main():
    """Main function to run the Monte Carlo pipeline."""
    args = parse_arguments()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Step 1: Generate simulations
    simulation_file = None
    
    if args.skip_generation:
        print("\nSkipping simulation generation step")
        # Find the most recent simulation file
        simulation_file = find_most_recent_simulation_file(args.output_dir)
        if simulation_file:
            print(f"Using existing simulation file: {simulation_file}")
        else:
            print("Error: No existing simulation files found")
            return 1
    else:
        simulation_file = run_generation(args)
        if not simulation_file:
            print("Generation step failed")
            return 1
    
    # Step 2: Analyze results
    if args.skip_analysis:
        print("\nSkipping analysis step")
    else:
        analysis_file = run_analysis(args, simulation_file)
        if not analysis_file:
            print("Analysis step failed")
            return 1
    
    print("\n===== Monte Carlo Pipeline Completed Successfully =====")
    return 0

if __name__ == "__main__":
    exit(main()) 