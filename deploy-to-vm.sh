#!/bin/bash
# Lab 6 VM Deployment Script
# Usage: bash deploy-to-vm.sh

set -e

VM_USER="student"
VM_IP="10.93.26.28"
VM_PATH="~/se-toolkit-lab-6"

echo "========================================"
echo "Lab 6 VM Deployment Script"
echo "========================================"
echo ""

# Step 1: Copy files to VM
echo "Step 1: Copying files to VM..."
scp -r ./* ${VM_USER}@${VM_IP}:${VM_PATH}/
echo "Files copied successfully."

# Step 2: SSH to VM and setup
echo ""
echo "Step 2: Setting up environment on VM..."
ssh ${VM_USER}@${VM_IP} << 'ENDSSH'
cd ~/se-toolkit-lab-6

# Create .env.docker.secret
cp .env.docker.example .env.docker.secret

# Edit credentials (using sed for non-interactive edit)
sed -i 's/AUTOCHECKER_EMAIL=.*/AUTOCHECKER_EMAIL=d.zhechev@innopolis.university/' .env.docker.secret
sed -i 's/AUTOCHECKER_PASSWORD=.*/AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG/' .env.docker.secret
sed -i 's/LMS_API_KEY=.*/LMS_API_KEY=Abcd1234/' .env.docker.secret

echo "Environment file configured."

# Start Docker containers
echo "Starting Docker containers..."
docker compose --env-file .env.docker.secret up --build -d

# Wait for containers to be ready
echo "Waiting for containers to start (30 seconds)..."
sleep 30

# Populate database
echo "Populating database..."
curl -X POST http://localhost:42002/pipeline/sync \
  -H "Authorization: Bearer Abcd1234" \
  -H "Content-Type: application/json" \
  -d '{}'

echo ""
echo "Verifying deployment..."
curl -s http://localhost:42002/items/ -H "Authorization: Bearer Abcd1234" | head -c 200

echo ""
echo "Deployment complete!"
ENDSSH

echo ""
echo "========================================"
echo "VM Deployment Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Set up Qwen Code API on VM: ~/qwen-code-oai-proxy/"
echo "2. Update .env.agent.secret with QWEN_API_KEY"
echo "3. Test the agent locally"
