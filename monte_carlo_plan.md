# Monte Carlo Simulation Implementation Plan

## Phase 1: Code Structure and Organization

1. **Directory Structure**
   ```
   /madness
     /utils                      # Already created with refactored functions
       __init__.py
       scoring.py                # Contains compare_with_truth, calculate_points_for_pick, calculate_rankings
       bracket_utils.py          # Contains get_most_recent_truth_bracket, get_sorted_truth_files
     /simulation
       __init__.py
       bracket_generator.py      # Random bracket generation logic
       monte_carlo.py            # Core simulation engine
       simulation_analyzer.py    # Statistical analysis of simulation results
     /data
       /simulations              # Directory to store simulation results
   ```

2. **Shared Constants**
   - Define shared constants for points calculation, upset bonuses, etc.
   - These should be accessible to both main app and simulation code

## Phase 2: Pipeline Scripts

1. **Script: generate_simulations.py**
   - **Purpose**: Generate thousands of random tournament completions
   - **Input**: Truth bracket file path and number of simulations
   - **Output**: Compressed binary file of simulated brackets
   - **Key Functions**:
     - `generate_random_completion(truth_bracket)` - Generate one random bracket
     - `generate_batch(truth_file, count=10000)` - Generate multiple simulations
     - `save_simulations(simulations, output_file)` - Save to compressed binary format

2. **Script: calculate_simulation_scores.py**
   - **Purpose**: Score each user bracket against each simulated outcome
   - **Input**: User brackets + Simulated brackets from Step 1
   - **Output**: Compressed binary file with scores matrix
   - **Key Functions**:
     - `load_user_brackets()` - Load all user brackets
     - `load_simulations(sim_file)` - Load simulated brackets
     - `calculate_scores(user_brackets, simulations)` - Calculate score matrix
     - `save_scores(scores, output_file)` - Save score matrix to compressed file

3. **Script: analyze_simulation_results.py**
   - **Purpose**: Analyze scores to calculate statistics
   - **Input**: Scores matrix from Step 2
   - **Output**: Compressed file with analysis results
   - **Key Functions**:
     - `load_scores(scores_file)` - Load score matrix
     - `calculate_rankings(scores)` - Convert scores to rankings (handling ties)
     - `analyze_rankings(rankings)` - Calculate statistics for each user
     - `save_analysis(analysis, output_file)` - Save analysis to compressed file

4. **Script: run_monte_carlo_pipeline.py**
   - **Purpose**: Master script to run all steps
   - **Features**:
     - Check for existence of output files at each step
     - Only run necessary steps
     - Command-line options to force rerun or run specific steps
     - Progress tracking

## Phase 3: Core Simulation Components

1. **Random Bracket Generator (bracket_generator.py)**
   - **Features**:
     - 50/50 random completion of undecided games
     - Flexible design to allow future enhancements (seed-based probabilities)
     - Respects existing game results in the truth bracket
   - **Key Functions**:
     - `generate_random_bracket(truth_bracket)` - Main generation function
     - Helper functions for each tournament stage

2. **Monte Carlo Engine (monte_carlo.py)**
   - **Features**:
     - Manages generation of many random brackets
     - Handles parallelization for performance
     - Provides progress tracking
   - **Key Functions**:
     - `MonteCarloSimulation` class to manage simulations
     - Loading/saving simulations with compression

3. **Simulation Analyzer (simulation_analyzer.py)**
   - **Features**:
     - Calculates rankings from scores with proper tie handling
     - Computes key statistics (% first place, best/worst rank, etc.)
     - Efficient implementation using NumPy
   - **Key Functions**:
     - `BracketAnalyzer` class to analyze results
     - Statistical functions for different metrics

## Phase 4: Data Storage

1. **Data Format**
   - Use compressed binary formats:
     - Simulated brackets: `data/simulations/brackets_{truth_file}_{count}.bin`
     - Scores: `data/simulations/scores_{truth_file}_{count}.bin`
     - Analysis results: `data/simulations/analysis_{truth_file}_{count}.bin`

2. **Compression**
   - Use pickle with compression protocol for Python objects
   - Use NumPy's compressed format (NPZ) for large numerical arrays
   - Implement utility functions for saving/loading compressed data

## Phase 5: Integration with Main App

1. **App.py Integration**
   - Add code to load analysis results in users_list route
   - Pass analysis data to template
   - Add flag to indicate if Monte Carlo data is available

2. **UI Enhancement**
   - Update users_list.html template to display Monte Carlo statistics
   - Add columns for % first place, best/worst rank, etc.
   - Add visual indicators (progress bars, color coding)

## Phase 6: Implementation Timeline

1. **Week 1: Simulation Core**
   - Implement bracket_generator.py
   - Create basic monte_carlo.py
   - Set up data storage formats

2. **Week 2: Pipeline Scripts**
   - Implement the three main pipeline scripts
   - Create master script
   - Test end-to-end pipeline

3. **Week 3: Analysis & Optimization**
   - Implement simulation_analyzer.py
   - Optimize performance
   - Add multiprocessing support

4. **Week 4: Integration & UI**
   - Integrate with main app
   - Enhance UI to display results
   - Add final polish and testing

## Phase 7: Testing & Validation

1. **Unit Tests**
   - Test bracket generation logic
   - Test score calculation
   - Test ranking algorithm (especially tie handling)

2. **Performance Testing**
   - Measure memory usage
   - Optimize for large numbers of simulations
   - Test on different hardware configurations

3. **Data Validation**
   - Verify correctness of statistical calculations
   - Check edge cases (all ties, no ties, etc.)
   - Validate against manually calculated examples

## Technical Considerations

1. **Tie Handling**
   - Ensure proper handling of ties in rankings (users with same score get same rank)
   - Last place may not equal the number of users due to ties

2. **Performance Optimization**
   - Use NumPy vectorization for efficient calculations
   - Implement multiprocessing for simulation generation
   - Optimize memory usage with efficient data structures

3. **Extensibility**
   - Design for future enhancements like seed-based win probabilities
   - Maintain clear separation between generation, scoring, and analysis components 