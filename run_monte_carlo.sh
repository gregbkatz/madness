#!/bin/bash
# Run the entire Monte Carlo simulation pipeline with reasonable default settings

# Set default parameters
SIM_COUNT=10000
VISUALIZE=false
SKIP_GEN=false
SKIP_ANALYSIS=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --count=*)
      SIM_COUNT="${1#*=}"
      shift
      ;;
    --count)
      SIM_COUNT="$2"
      shift 2
      ;;
    --visualize)
      VISUALIZE=true
      shift
      ;;
    --skip-generation)
      SKIP_GEN=true
      shift
      ;;
    --skip-analysis)
      SKIP_ANALYSIS=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--count NUMBER] [--visualize] [--skip-generation] [--skip-analysis]"
      echo ""
      echo "Options:"
      echo "  --count NUMBER        Number of simulations to generate (default: 10000)"
      echo "  --visualize           Generate visualizations"
      echo "  --skip-generation     Skip generation step (use existing simulations)"
      echo "  --skip-analysis       Skip analysis step"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Build command
CMD="python run_monte_carlo_pipeline.py --count $SIM_COUNT"

if [ "$VISUALIZE" = true ]; then
  CMD="$CMD --visualize"
fi

if [ "$SKIP_GEN" = true ]; then
  CMD="$CMD --skip-generation"
fi

if [ "$SKIP_ANALYSIS" = true ]; then
  CMD="$CMD --skip-analysis"
fi

echo "Running Monte Carlo pipeline with $SIM_COUNT simulations"
echo "Command: $CMD"
echo ""

# Run the pipeline
eval $CMD

# Make the script executable
chmod +x "$0" 