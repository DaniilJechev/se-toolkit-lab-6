# VM Deployment - Copy and Paste Commands

## Step 1: Connect to VM

Open PowerShell and run:
```powershell
ssh root@10.93.26.28
# Password: Abcd1234
```

## Step 2: Clone and Setup (copy all commands below)

Once connected to VM, copy and paste these commands:

```bash
cd ~

# Clone repository
git clone https://github.com/DaniilJechev/se-toolkit-lab-6.git
cd ~/se-toolkit-lab-6

# Configure environment
cp .env.docker.example .env.docker.secret

# Set credentials
sed -i 's/AUTOCHECKER_EMAIL=.*/AUTOCHECKER_EMAIL=d.zhechev@innopolis.university/' .env.docker.secret
sed -i 's/AUTOCHECKER_PASSWORD=.*/AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG/' .env.docker.secret
sed -i 's/LMS_API_KEY=.*/LMS_API_KEY=Abcd1234/' .env.docker.secret

# Verify config
cat .env.docker.secret | grep -E "AUTOCHECKER_EMAIL|AUTOCHECKER_PASSWORD|LMS_API_KEY"

# Start Docker containers
docker compose --env-file .env.docker.secret up --build -d

# Wait for containers
echo "Waiting 30 seconds for containers to start..."
sleep 30

# Check container status
docker compose --env-file .env.docker.secret ps

# Run ETL pipeline
curl -X POST http://localhost:42002/pipeline/sync \
  -H 'Authorization: Bearer Abcd1234' \
  -H 'Content-Type: application/json' \
  -d '{}'

# Verify data loaded
curl -s http://localhost:42002/items/ -H 'Authorization: Bearer Abcd1234' | head -c 200

echo ""
echo "=== Local Deployment Complete! ==="
echo "Frontend: http://localhost:42002/"
echo "Swagger: http://localhost:42002/docs"
echo "API Key: Abcd1234"
```

## Step 3: Setup Qwen Code API (Optional for now)

```bash
cd ~

# Clone Qwen proxy
git clone https://github.com/sgo0/qwen-code-oai-proxy.git
cd ~/qwen-code-oai-proxy

# Get API key from https://chat.qwen.ai/
# Then create .env file:
nano .env
```

Add this content to `.env`:
```
QWEN_API_KEY=YOUR_KEY_FROM_QWEN
PORT=8080
```

Then run:
```bash
npm install
nohup npm start &
```

## Step 4: Update Local .env.agent.secret

On your local machine, edit:
`c:\Users\gigachaDick\se-toolkit-lab-6\se-toolkit-lab-6\.env.agent.secret`

Set:
```
LLM_API_KEY=your-qwen-api-key
LLM_API_BASE=http://10.93.26.28:8080/v1
LLM_MODEL=qwen3-coder-plus
```
