"""
Monte Carlo Simulation Engine

This module provides functionality to run Monte Carlo simulations for 
March Madness bracket analysis, including generating many random brackets
and managing the simulation process.
"""

import os
import json
import time
from datetime import datetime
import multiprocessing
from tqdm import tqdm

# Import local modules
from simulation.bracket_generator import generate_random_completion, save_simulations, load_simulations

# Define the batch generation function outside of class methods for pickling
def run_batch(args):
    """
    Run a batch of simulations.
    
    Args:
        args (tuple): Tuple containing (batch_idx, truth_bracket, batch_size)
        
    Returns:
        tuple: (batch_brackets, batch_time)
    """
    batch_idx, truth_bracket, batch_size = args
    batch_start = time.time()
    batch_brackets = generate_random_completion(
        truth_bracket=truth_bracket, 
        count=batch_size
    )
    batch_time = time.time() - batch_start
    return batch_brackets, batch_time

class MonteCarloSimulation:
    """Class that manages running Monte Carlo simulations for bracket analysis."""
    
    def __init__(self, truth_bracket=None, truth_file=None, output_dir='data/simulations'):
        """
        Initialize the Monte Carlo simulation engine.
        
        Args:
            truth_bracket (dict, optional): The truth bracket to use as a base
            truth_file (str, optional): Path to the truth bracket file
            output_dir (str): Directory to save simulation results
        """
        self.truth_bracket = truth_bracket
        self.truth_file = truth_file
        self.output_dir = output_dir
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def run_simulation(self, num_simulations=10000, batch_size=1000, num_processes=None):
        """
        Run a Monte Carlo simulation, generating num_simulations random brackets.
        
        Args:
            num_simulations (int): Total number of simulations to run
            batch_size (int): Number of simulations per batch/process
            num_processes (int, optional): Number of processes to use for parallelization.
                                          If None, will use available CPU cores.
                                          
        Returns:
            str: Path to the file containing the simulation results
        """
        start_time = time.time()
        
        # Determine number of processes to use
        if num_processes is None:
            num_processes = max(1, multiprocessing.cpu_count() - 1)  # Leave one core free
        
        # Adjust batch size if num_simulations is smaller
        if num_simulations < batch_size:
            batch_size = num_simulations
        
        # Calculate batches
        num_batches = (num_simulations + batch_size - 1) // batch_size
        actual_simulations = min(num_batches * batch_size, num_simulations)
        
        print(f"Running {actual_simulations} simulations ({num_batches} batches of {batch_size}) using {num_processes} processes")
        
        # Prepare batch arguments
        batch_args = []
        remaining = num_simulations
        
        for batch_idx in range(num_batches):
            # For the last batch, adjust size if needed
            current_batch_size = min(batch_size, remaining)
            batch_args.append((batch_idx, self.truth_bracket, current_batch_size))
            remaining -= current_batch_size
        
        # Run the batches in parallel
        all_brackets = []
        total_batch_time = 0
        
        # Create a process pool
        with multiprocessing.Pool(processes=num_processes) as pool:
            # Map the run_batch function to the batch arguments with progress tracking
            results = list(tqdm(
                pool.imap(run_batch, batch_args),
                total=num_batches,
                desc="Generating simulations"
            ))
            
            # Collect all the results
            for batch_brackets, batch_time in results:
                all_brackets.extend(batch_brackets)
                total_batch_time += batch_time
        
        # Extract truth file identifier (round_X_game_Y) if available
        truth_id = "custom"
        if hasattr(self, 'truth_file') and self.truth_file:
            # Extract the basename without extension
            basename = os.path.basename(self.truth_file)
            if basename.startswith("round_") and "_game_" in basename:
                truth_id = os.path.splitext(basename)[0]  # Remove extension
        
        # Generate filename based on timestamp and truth bracket
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sim_count = len(all_brackets)
        output_file = f"{self.output_dir}/brackets_{truth_id}_{sim_count}_{timestamp}.bin"
        
        # Save the simulations
        save_simulations(all_brackets, output_file)
        
        # Print summary
        elapsed = time.time() - start_time
        print(f"Simulation completed in {elapsed:.2f} seconds")
        print(f"Average batch processing time: {total_batch_time / num_batches:.2f} seconds")
        print(f"Generated {len(all_brackets)} brackets")
        print(f"Saved to: {output_file}")
        
        return output_file
    
    @staticmethod
    def generate_simulation_file(truth_bracket=None, num_simulations=10000):
        """
        Convenience method to generate a simulation file in a single call.
        
        Args:
            truth_bracket (dict, optional): The truth bracket to use as a base
            num_simulations (int): Number of simulations to generate
            
        Returns:
            str: Path to the generated simulation file
        """
        simulator = MonteCarloSimulation(truth_bracket)
        return simulator.run_simulation(num_simulations)

def run_monte_carlo(truth_bracket_file=None, num_simulations=10000):
    """
    Run a Monte Carlo simulation from a truth bracket file.
    
    Args:
        truth_bracket_file (str, optional): Path to the truth bracket file.
                                           If None, the most recent truth bracket will be used.
        num_simulations (int): Number of simulations to generate
        
    Returns:
        str: Path to the generated simulation file
    """
    # Load the truth bracket if provided
    truth_bracket = None
    if truth_bracket_file and os.path.exists(truth_bracket_file):
        with open(truth_bracket_file, 'r') as f:
            truth_bracket = json.load(f)
            
    # Run the simulation
    simulator = MonteCarloSimulation(truth_bracket, truth_file=truth_bracket_file)
    return simulator.run_simulation(num_simulations)

if __name__ == "__main__":
    # Example usage
    import sys
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        truth_file = sys.argv[1]
    else:
        truth_file = None
        
    if len(sys.argv) > 2:
        try:
            num_sims = int(sys.argv[2])
        except ValueError:
            print(f"Invalid number of simulations: {sys.argv[2]}")
            num_sims = 1000
    else:
        num_sims = 1000
        
    print(f"Running {num_sims} simulations...")
    run_monte_carlo(truth_file, num_sims) 