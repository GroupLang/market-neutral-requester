#!/bin/bash

# Scheduler script for market-neutral-requester
# Runs Python scripts at midnight Spanish time with specified input files and uploads results to S3

# Set Spanish timezone
export TZ="Europe/Madrid"

# Log file setup
LOG_FILE="scheduler.log"
ERROR_LOG="scheduler_error.log"

# S3 bucket details
S3_BUCKET="market-neutral-results"
S3_REGION="eu-west-1"

# Function for logging
log_message() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Function for error logging
log_error() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ERROR: $1" | tee -a "$ERROR_LOG" "$LOG_FILE"
}

# Function to run Python scripts with specific input file and S3 suffix
run_scripts_with_params() {
    local input_file=$1
    local s3_suffix=$2
    
    log_message "Starting execution of Python scripts with input file: $input_file"
    
    # Run main.py with input file environment variable
    log_message "Running main.py with input file: $input_file"
    if INPUT_FILE="$input_file" python3 main.py 2>> "$ERROR_LOG" | tee -a "$LOG_FILE"; then
        log_message "main.py executed successfully"
        
        # Run testing.py
        log_message "Running testing.py"
        if INPUT_FILE="$input_file" python3 testing.py 2>> "$ERROR_LOG" | tee -a "$LOG_FILE"; then
            log_message "testing.py executed successfully"
        else
            log_error "testing.py failed with exit code $?"
        fi
        
        # Run testing_agg_plot.py
        log_message "Running testing_agg_plot.py"
        if INPUT_FILE="$input_file" python3 testing_agg_plot.py 2>> "$ERROR_LOG" | tee -a "$LOG_FILE"; then
            log_message "testing_agg_plot.py executed successfully"
        else
            log_error "testing_agg_plot.py failed with exit code $?"
        fi
        
        # Upload plots to S3 with optional suffix
        if [ -n "$s3_suffix" ]; then
            log_message "Uploading plots and data to S3 bucket $S3_BUCKET with suffix $s3_suffix"
            sleep 2  # Ensure file writes complete
            if aws s3 sync ./plots s3://$S3_BUCKET/$s3_suffix --region $S3_REGION --exact-timestamps --delete 2>> "$ERROR_LOG" | tee -a "$LOG_FILE" && \
               aws s3 sync ./data s3://$S3_BUCKET/$s3_suffix/data --region $S3_REGION --exact-timestamps --delete 2>> "$ERROR_LOG" | tee -a "$LOG_FILE"; then
                log_message "S3 upload with suffix $s3_suffix completed successfully"
            else
                log_error "S3 upload with suffix $s3_suffix failed with exit code $?"
            fi
        else
            log_message "Uploading plots and data to S3 bucket $S3_BUCKET"
            sleep 2  # Ensure file writes complete
            if aws s3 sync ./plots s3://$S3_BUCKET --region $S3_REGION --exact-timestamps --delete 2>> "$ERROR_LOG" | tee -a "$LOG_FILE" && \
               aws s3 sync ./data s3://$S3_BUCKET/data --region $S3_REGION --exact-timestamps --delete 2>> "$ERROR_LOG" | tee -a "$LOG_FILE"; then
                log_message "S3 upload completed successfully"
            else
                log_error "S3 upload failed with exit code $?"
            fi
        fi
    else
        log_error "main.py failed with exit code $?, skipping subsequent scripts and S3 upload"
    fi
    
    log_message "Execution with input file $input_file completed"
}

# Function to run both workflows
run_workflows() {
    log_message "Starting scheduled workflows at midnight"
    
    # Run second execution with data/gpt_raw_decisions_o2.csv and no suffix
    log_message "Starting second execution with data/gpt_raw_decisions.csv"
    run_scripts_with_params "data/gpt_raw_decisions.csv" "gpt4o"
    # Run first execution with data/gpt_raw_decisions_o1.csv and suffix_o1
    log_message "Starting first execution with data/gpt_raw_decisions_o1.csv and suffix_o1"
    run_scripts_with_params "data/gpt_raw_decisions_o1.csv" "o1"


    log_message "All executions completed successfully"
}

# Initialize log files
log_message "Scheduler started"
log_message "Checking for midnight (00:00) every 30 seconds in Spanish timezone (Europe/Madrid)"


run_workflows
# Main loop
while true; do
    # Get current hour and minute in Spanish timezone
    CURRENT_HOUR=$(date +"%H")
    CURRENT_MINUTE=$(date +"%M")
    
    # Check if it's midnight (00:00)
    if [ "$CURRENT_HOUR" == "00" ] && [ "$CURRENT_MINUTE" == "10" ]; then
        log_message "It's midnight! Starting script execution"
        run_workflows
        
        # Wait ~24 hours before checking again (23 hours and 55 minutes)
        # This prevents running twice if the script execution takes a few minutes
        log_message "Waiting ~24 hours before next execution check"
        sleep 23h 55m
    fi

    # Sleep for 30 seconds before checking again
    sleep 30
done
