#!/bin/bash

# Deployment script for GCP infrastructure
# Usage: ./deploy-gcp.sh

set -e

echo "Starting GCP infrastructure deployment..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Error: Terraform is not installed. Please install it first."
    echo "Visit: https://www.terraform.io/downloads.html"
    exit 1
fi

# Set project ID
PROJECT_ID="grouplang-450317"

echo "Setting up GCP project: $PROJECT_ID"

# Authenticate with GCP (if not already done)
echo "Checking GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please authenticate with GCP:"
    gcloud auth login
fi

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable iam.googleapis.com

# Create SSH key if it doesn't exist
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "Creating SSH key pair..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
fi

# Navigate to terraform directory
cd cloud/terraform

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan the deployment
echo "Planning Terraform deployment..."
terraform plan -var-file="gcp.tfvars"

# Apply the configuration
echo "Applying Terraform configuration..."
terraform apply -var-file="gcp.tfvars" -auto-approve

# Get the VM IP
VM_IP=$(terraform output -raw vm_external_ip)
BUCKET_NAME=$(terraform output -raw storage_bucket_name)

echo ""
echo "=== Deployment Complete ==="
echo "VM External IP: $VM_IP"
echo "Storage Bucket: $BUCKET_NAME"
echo ""
echo "To connect to the VM:"
echo "ssh ubuntu@$VM_IP"
echo ""
echo "Next steps:"
echo "1. Copy your code to the VM"
echo "2. Install dependencies"
echo "3. Start the scheduler service"
echo ""
echo "Example deployment commands:"
echo "scp -r . ubuntu@$VM_IP:/opt/market-neutral-scheduler/"
echo "ssh ubuntu@$VM_IP 'cd /opt/market-neutral-scheduler && pip3 install -r requirements.txt'"
echo "ssh ubuntu@$VM_IP 'sudo systemctl start market-neutral-scheduler'"