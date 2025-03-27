#!/bin/bash
# Run the entire Monte Carlo simulation pipeline with reasonable default settings

# Default parameters
SIM_COUNT=10000
TRUTH_FILE=""
VISUALIZE=false
SKIP_GENERATION=false
SKIP_ANALYSIS=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --count=*) SIM_COUNT="${1#*=}" ;;
        --count) SIM_COUNT="$2"; shift ;;
        --truth-file=*) TRUTH_FILE="${1#*=}" ;;
        --truth-file) TRUTH_FILE="$2"; shift ;;
        --visualize) VISUALIZE=true ;;
        --skip-generation) SKIP_GENERATION=true ;;
        --skip-analysis) SKIP_ANALYSIS=true ;;
        --help)
            echo "Usage: ./run_monte_carlo.sh [OPTIONS]"
            echo "Options:"
            echo "  --count=NUMBER        Number of simulations to run (default: 10000)"
            echo "  --truth-file=FILE     Truth bracket file to use for simulations"
            echo "  --visualize           Generate visualizations of the results"
            echo "  --skip-generation     Skip the simulation generation step"
            echo "  --skip-analysis       Skip the simulation analysis step"
            echo "  --help                Display this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; echo "Use --help for usage information"; exit 1 ;;
    esac
    shift
done

# Build the command
CMD="python run_monte_carlo_pipeline.py --count $SIM_COUNT"

# Add options if specified
if [[ -n "$TRUTH_FILE" ]]; then
    CMD="$CMD --truth-file $TRUTH_FILE"
fi

if [[ "$VISUALIZE" = true ]]; then
    CMD="$CMD --visualize"
fi

if [[ "$SKIP_GENERATION" = true ]]; then
    CMD="$CMD --skip-generation"
fi

if [[ "$SKIP_ANALYSIS" = true ]]; then
    CMD="$CMD --skip-analysis"
fi

echo "Running Monte Carlo pipeline with $SIM_COUNT simulations"
echo "Command: $CMD"
echo ""

# Run the pipeline
eval $CMD

# Make the script executable
chmod +x "$0" 