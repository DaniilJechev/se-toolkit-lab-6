#!/bin/bash
# Run this on VM after connecting:
# ssh student@10.93.26.28 'bash -s' < deploy-vm-remote.sh

set -e

cd ~

echo "=== Cloning repository ==="
if [ -d "se-toolkit-lab-6" ]; then
    echo "Directory exists, pulling latest..."
    cd ~/se-toolkit-lab-6
    git pull
else
    git clone https://github.com/DaniilJechev/se-toolkit-lab-6.git
    cd ~/se-toolkit-lab-6
fi

echo "=== Configuring environment ==="
cp .env.docker.example .env.docker.secret

# Set credentials using sed
sed -i 's/AUTOCHECKER_EMAIL=.*/AUTOCHECKER_EMAIL=d.zhechev@innopolis.university/' .env.docker.secret
sed -i 's/AUTOCHECKER_PASSWORD=.*/AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG/' .env.docker.secret
sed -i 's/LMS_API_KEY=.*/LMS_API_KEY=Abcd1234/' .env.docker.secret

echo "=== Starting Docker containers ==="
docker compose --env-file .env.docker.secret up --build -d

echo "=== Waiting for containers (30 seconds) ==="
sleep 30

echo "=== Running ETL pipeline ==="
curl -X POST http://localhost:42002/pipeline/sync \
  -H 'Authorization: Bearer Abcd1234' \
  -H 'Content-Type: application/json' \
  -d '{}'

echo ""
echo "=== Verifying deployment ==="
curl -s http://localhost:42002/items/ \
  -H 'Authorization: Bearer Abcd1234' | head -c 200

echo ""
echo "=== Deployment Complete! ==="
echo "Frontend: http://$VM_IP:42002/"
echo "Swagger: http://$VM_IP:42002/docs"
echo "API Key: Abcd1234"
