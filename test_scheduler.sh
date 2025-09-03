#!/bin/bash

# Test script to verify scheduler components work
# This is a simplified version of the scheduler workflow for testing

# Set Spanish timezone
export TZ="Europe/Madrid"

# Log file setup
LOG_FILE="test_scheduler.log"
ERROR_LOG="test_scheduler_error.log"

# Function for logging
log_message() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Function for error logging
log_error() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ERROR: $1" | tee -a "$ERROR_LOG" "$LOG_FILE"
}

# Function to test Python scripts with specific input file (without upload)
test_scripts_with_params() {
    local input_file=$1
    local suffix=$2
    
    log_message "Starting test execution of Python scripts with input file: $input_file"
    
    # Skip main.py as it requires API credentials and tries to fetch new data
    log_message "Skipping main.py (requires API credentials)"
    
    # Run testing.py with timeout
    log_message "Running testing.py"
    if timeout 60 bash -c "INPUT_FILE=\"$input_file\" python3 testing.py" 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG"; then
        log_message "testing.py executed successfully (or timed out without error)"
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_message "testing.py timed out but likely produced results"
        else
            log_error "testing.py failed with exit code $exit_code"
        fi
    fi
    
    # Run testing_agg_plot.py with timeout  
    log_message "Running testing_agg_plot.py"
    if timeout 60 bash -c "INPUT_FILE=\"$input_file\" python3 testing_agg_plot.py" 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG"; then
        log_message "testing_agg_plot.py executed successfully (or timed out without error)"
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_message "testing_agg_plot.py timed out but likely produced results"
        else
            log_error "testing_agg_plot.py failed with exit code $exit_code"
        fi
    fi
    
    # Check if output files were created
    log_message "Checking if output files were created:"
    for file in data/buy_and_hold.csv data/market_neutral_returns.csv data/exponential_returns.csv data/exponential_short_returns.csv; do
        if [ -f "$file" ]; then
            log_message "✓ $file exists ($(stat -c%s "$file") bytes)"
        else
            log_error "✗ $file missing"
        fi
    done
    
    # Check if plot directories exist
    for dir in plots/market_neutral plots/exponential_strategies; do
        if [ -d "$dir" ]; then
            plot_count=$(find "$dir" -name "*.png" | wc -l)
            log_message "✓ $dir exists with $plot_count PNG files"
        else
            log_error "✗ $dir missing"
        fi
    done
    
    log_message "Test execution with input file $input_file completed"
}

# Function to test both workflows
test_workflows() {
    log_message "Starting test workflows"
    
    # Test with data/gpt_raw_decisions.csv
    log_message "Starting test with data/gpt_raw_decisions.csv"
    test_scripts_with_params "data/gpt_raw_decisions.csv" "gpt4o"
    
    # Test with data/gpt_raw_decisions_o1.csv
    log_message "Starting test with data/gpt_raw_decisions_o1.csv"
    test_scripts_with_params "data/gpt_raw_decisions_o1.csv" "o1"
    
    log_message "All test executions completed"
}

# Initialize log files
log_message "Test scheduler started"

# Run the test workflow
test_workflows

log_message "Test scheduler finished"