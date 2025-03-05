#!/bin/bash

# Scheduler script for market-neutral-requester
# Runs Python scripts at midnight Spanish time and uploads results to S3

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

# Function to run Python scripts
run_scripts() {
    log_message "Starting daily execution of Python scripts"
    
    # Run main.py
    log_message "Running main.py"
    if python main.py >> "$LOG_FILE" 2>> "$ERROR_LOG"; then
        log_message "main.py executed successfully"
        
        # Run testing.py
        log_message "Running testing.py"
        if python testing.py >> "$LOG_FILE" 2>> "$ERROR_LOG"; then
            log_message "testing.py executed successfully"
        else
            log_error "testing.py failed with exit code $?"
        fi
        
        # Run testing_agg_plot.py
        log_message "Running testing_agg_plot.py"
        if python testing_agg_plot.py >> "$LOG_FILE" 2>> "$ERROR_LOG"; then
            log_message "testing_agg_plot.py executed successfully"
        else
            log_error "testing_agg_plot.py failed with exit code $?"
        fi
        
        # Upload plots to S3
        log_message "Uploading plots to S3 bucket $S3_BUCKET"
        if aws s3 sync ./plots s3://$S3_BUCKET --region $S3_REGION >> "$LOG_FILE" 2>> "$ERROR_LOG"; then
            log_message "S3 upload completed successfully"
        else
            log_error "S3 upload failed with exit code $?"
        fi
    else
        log_error "main.py failed with exit code $?, skipping subsequent scripts and S3 upload"
    fi
    
    log_message "Daily execution completed"
}

# Initialize log files
log_message "Scheduler started"
log_message "Checking for midnight (00:00) every 30 seconds in Spanish timezone (Europe/Madrid)"

# Main loop
while true; do
    # Get current hour and minute in Spanish timezone
    CURRENT_HOUR=$(date +"%H")
    CURRENT_MINUTE=$(date +"%M")
    
    # Check if it's midnight (00:00)
    if [ "$CURRENT_HOUR" == "00" ] && [ "$CURRENT_MINUTE" == "00" ]; then
        log_message "It's midnight! Starting script execution"
        run_scripts
        
        # Wait ~24 hours before checking again (23 hours and 55 minutes)
        # This prevents running twice if the script execution takes a few minutes
        log_message "Waiting ~24 hours before next execution check"
        sleep 23h 55m
    fi
    
    # Sleep for 30 seconds before checking again
    sleep 30
done
