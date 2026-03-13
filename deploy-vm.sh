#!/bin/bash
# Deploy to VM script
VM_USER="student"
VM_IP="10.93.26.28"
VM_PATH="~/se-toolkit-lab-6"

echo "Deploying to VM: $VM_IP"

# Create directory on VM
ssh ${VM_USER}@${VM_IP} "mkdir -p ${VM_PATH}"

# Copy files
scp -r * ${VM_USER}@${VM_IP}:${VM_PATH}/

echo "Files copied. Setting up environment..."

# Setup environment on VM
ssh ${VM_USER}@${VM_IP} << 'ENDSSH'
cd ~/se-toolkit-lab-6

# Create .env.docker.secret
cp .env.docker.example .env.docker.secret

# Set credentials
sed -i 's/AUTOCHECKER_EMAIL=.*/AUTOCHECKER_EMAIL=d.zhechev@innopolis.university/' .env.docker.secret
sed -i 's/AUTOCHECKER_PASSWORD=.*/AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG/' .env.docker.secret
sed -i 's/LMS_API_KEY=.*/LMS_API_KEY=Abcd1234/' .env.docker.secret

echo "Environment configured. Starting containers..."

# Start containers
docker compose --env-file .env.docker.secret up --build -d

# Wait for containers
sleep 30

# Run ETL pipeline
echo "Running ETL pipeline..."
curl -X POST http://localhost:42002/pipeline/sync \
  -H 'Authorization: Bearer Abcd1234' \
  -H 'Content-Type: application/json' \
  -d '{}'

echo "Verifying deployment..."
curl -s http://localhost:42002/items/ \
  -H 'Authorization: Bearer Abcd1234' | head -c 200

echo ""
echo "Deployment complete!"
ENDSSH

echo "Done!"
