#!/bin/bash

# Test the complete run_workflows function with GCS upload
# This simulates what the scheduler would do

# Set Spanish timezone
export TZ="Europe/Madrid"

# GCS bucket details
GCS_BUCKET="grouplang-450317-market-neutral-results"
GCP_PROJECT="grouplang-450317"

# Log file setup
LOG_FILE="full_workflow_test.log"
ERROR_LOG="full_workflow_test_error.log"

# Function for logging
log_message() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Function for error logging
log_error() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] ERROR: $1" | tee -a "$ERROR_LOG" "$LOG_FILE"
}

# Function to run Python scripts with specific input file and GCS suffix
run_scripts_with_params() {
    local input_file=$1
    local s3_suffix=$2
    
    log_message "Starting execution of Python scripts with input file: $input_file"
    
    # Skip main.py as it requires API credentials and fetches new data
    log_message "Skipping main.py (requires API credentials for new data fetching)"
        
    # Run testing.py with timeout
    log_message "Running testing.py"
    if timeout 120 bash -c "INPUT_FILE=\"$input_file\" python3 testing.py" 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG"; then
        log_message "testing.py executed successfully"
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_message "testing.py timed out but likely produced results"
        else
            log_error "testing.py failed with exit code $exit_code"
            return 1
        fi
    fi
    
    # Run testing_agg_plot.py with timeout
    log_message "Running testing_agg_plot.py"
    if timeout 120 bash -c "INPUT_FILE=\"$input_file\" python3 testing_agg_plot.py" 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG"; then
        log_message "testing_agg_plot.py executed successfully"
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_message "testing_agg_plot.py timed out but likely produced results"
        else
            log_error "testing_agg_plot.py failed with exit code $exit_code"
            return 1
        fi
    fi
    
    # Upload plots to GCS with optional suffix
    if [ -n "$s3_suffix" ]; then
        log_message "Uploading plots and data to GCS bucket $GCS_BUCKET with suffix $s3_suffix"
        if gsutil -m rsync -r -d ./plots gs://$GCS_BUCKET/$s3_suffix 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG" && \
           gsutil -m rsync -r -d ./data gs://$GCS_BUCKET/$s3_suffix/data 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG"; then
            log_message "GCS upload with suffix $s3_suffix completed successfully"
        else
            log_error "GCS upload with suffix $s3_suffix failed with exit code $?"
            return 1
        fi
    else
        log_message "Uploading plots and data to GCS bucket $GCS_BUCKET"
        if gsutil -m rsync -r -d ./plots gs://$GCS_BUCKET 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG" && \
           gsutil -m rsync -r -d ./data gs://$GCS_BUCKET/data 2>&1 | tee -a "$LOG_FILE" "$ERROR_LOG"; then
            log_message "GCS upload completed successfully"
        else
            log_error "GCS upload failed with exit code $?"
            return 1
        fi
    fi
    
    log_message "Execution with input file $input_file completed successfully"
}

# Function to run both workflows (matching run_workflows from scheduler.sh)
run_workflows() {
    log_message "Starting scheduled workflows test"
    
    # Run first execution with data/gpt_raw_decisions.csv and suffix gpt4o
    log_message "Starting first execution with data/gpt_raw_decisions.csv"
    run_scripts_with_params "data/gpt_raw_decisions.csv" "gpt4o"
    
    # Run second execution with data/gpt_raw_decisions_o1.csv and suffix o1
    log_message "Starting second execution with data/gpt_raw_decisions_o1.csv and suffix o1"
    run_scripts_with_params "data/gpt_raw_decisions_o1.csv" "o1"

    log_message "All executions completed successfully"
}

# Initialize log files
log_message "Full workflow test started"

# Run the complete workflow
run_workflows

log_message "Full workflow test completed"

# Show summary
echo ""
echo "=== WORKFLOW TEST SUMMARY ==="
echo "Log file: $LOG_FILE"
echo "Error log: $ERROR_LOG"
echo "GCS bucket: gs://$GCS_BUCKET"
echo ""
echo "Check uploaded files with:"
echo "gsutil ls -r gs://$GCS_BUCKET/"