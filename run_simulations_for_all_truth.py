#!/usr/bin/env python3
"""
Run Monte Carlo Simulations for All Truth Files

This script runs Monte Carlo simulations for all truth bracket files, 
skipping any that already have existing simulation and analysis files.
"""

import os
import argparse
import subprocess
import time
from datetime import datetime

from utils.bracket_utils import get_sorted_truth_files

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run Monte Carlo simulations for all truth files'
    )
    parser.add_argument(
        '--count', 
        type=int, 
        default=1000,
        help='Number of simulations to generate for each truth file (default: 1000)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/simulations',
        help='Directory to save simulation results (default: data/simulations)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration even if files already exist'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output from each simulation'
    )
    parser.add_argument(
        '--start-from',
        type=int,
        default=0,
        help='Start from this index in the truth files list (0-based)'
    )
    
    return parser.parse_args()

def get_expected_filenames(truth_file, count, output_dir):
    """Get the expected filenames for simulation and analysis files."""
    # Extract the base info from the truth file
    basename = os.path.basename(truth_file)
    if basename.startswith("round_") and "_game_" in basename:
        truth_id = os.path.splitext(basename)[0]  # Remove extension
    else:
        truth_id = "custom"
    
    # Expected filenames
    sim_file = f"{output_dir}/brackets_{truth_id}_{count}.bin"
    analysis_file = f"{output_dir}/round_{truth_id}_{count}_brackets.json"
    
    # Handle 'custom' case for analysis file
    if truth_id == "custom":
        timestamp = datetime.now().strftime("%Y%m%d")
        analysis_file = f"{output_dir}/monte_carlo_{timestamp}_{count}_brackets.json"
    
    return sim_file, analysis_file

def run_simulation(truth_file, count, output_dir, verbose=False):
    """Run Monte Carlo simulation for a single truth file."""
    # Build the command
    cmd = ["python", "run_monte_carlo_pipeline.py", 
           "--count", str(count), 
           "--truth-file", truth_file,
           "--output-dir", output_dir]
    
    # Run the command
    start_time = time.time()
    try:
        if verbose:
            # Run with output displayed
            result = subprocess.run(cmd, check=True)
            success = result.returncode == 0
        else:
            # Run silently
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            success = True
        
        elapsed = time.time() - start_time
        return success, elapsed
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"Error running simulation: {e}")
        if not verbose and e.stdout:
            print(e.stdout)
        if not verbose and e.stderr:
            print(e.stderr)
        return False, elapsed

def main():
    """Main function to run simulations for all truth files."""
    args = parse_arguments()
    
    # Get all truth files
    truth_files = get_sorted_truth_files()
    if not truth_files:
        print("Error: No truth files found")
        return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Found {len(truth_files)} truth files")
    print(f"Will generate {args.count} simulations for each file that needs it")
    print(f"Starting from index {args.start_from}")
    
    # Skip files before the start index
    if args.start_from > 0:
        truth_files = truth_files[args.start_from:]
        print(f"Skipped {args.start_from} files, {len(truth_files)} files remaining")
    
    # Count for statistics
    total_files = len(truth_files)
    files_processed = 0
    files_skipped = 0
    files_failed = 0
    
    for i, truth_file in enumerate(truth_files):
        print(f"\n[{i + args.start_from + 1}/{total_files + args.start_from}] Processing: {truth_file}")
        
        # Get expected filenames
        sim_file, analysis_file = get_expected_filenames(truth_file, args.count, args.output_dir)
        
        # Check if files already exist
        if not args.force and os.path.exists(sim_file) and os.path.exists(analysis_file):
            print(f"  Skipping: Files already exist")
            print(f"  Simulation file: {sim_file}")
            print(f"  Analysis file: {analysis_file}")
            files_skipped += 1
            continue
        
        # Run the simulation
        print(f"  Running simulation...")
        success, elapsed = run_simulation(truth_file, args.count, args.output_dir, args.verbose)
        
        if success:
            print(f"  Completed in {elapsed:.2f} seconds")
            files_processed += 1
        else:
            print(f"  Failed after {elapsed:.2f} seconds")
            files_failed += 1
    
    # Print summary
    print(f"\nProcess completed:")
    print(f"  Total files: {total_files}")
    print(f"  Files processed: {files_processed}")
    print(f"  Files skipped (already exist): {files_skipped}")
    print(f"  Files failed: {files_failed}")
    
    if files_failed > 0:
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 