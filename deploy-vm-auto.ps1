$VM_PASSWORD = "Abcd1234"
$VM_USER = "root"
$VM_IP = "10.93.26.28"

# Script to run on VM
$remoteScript = @'
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

sed -i 's/AUTOCHECKER_EMAIL=.*/AUTOCHECKER_EMAIL=d.zhechev@innopolis.university/' .env.docker.secret
sed -i 's/AUTOCHECKER_PASSWORD=.*/AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG/' .env.docker.secret
sed -i 's/LMS_API_KEY=.*/LMS_API_KEY=Abcd1234/' .env.docker.secret

echo "=== Starting Docker containers ==="
docker compose --env-file .env.docker.secret up --build -d

echo "=== Waiting for containers (30 seconds) ==="
sleep 30

echo "=== Running ETL pipeline ==="
curl -X POST http://localhost:42002/pipeline/sync -H 'Authorization: Bearer Abcd1234' -H 'Content-Type: application/json' -d '{}'

echo ""
echo "=== Verifying deployment ==="
curl -s http://localhost:42002/items/ -H 'Authorization: Bearer Abcd1234' | head -c 200

echo ""
echo "=== Deployment Complete! ==="
'@

# Write script to temp file on VM and execute
$remoteScript | ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_IP} "cat > /tmp/deploy.sh && chmod +x /tmp/deploy.sh && bash /tmp/deploy.sh"
