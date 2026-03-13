# VM Deployment Manual Instructions

## Prerequisites
- VM IP: `10.93.26.28`
- VM User: `student`
- VM Password: `Abcd1234`

## Step 1: Clone repository on VM

Connect to VM:
```bash
ssh student@10.93.26.28
# Password: Abcd1234
```

Clone your fork:
```bash
cd ~
git clone https://github.com/DaniilJechev/se-toolkit-lab-6.git
cd ~/se-toolkit-lab-6
```

## Step 2: Configure environment

```bash
cd ~/se-toolkit-lab-6
cp .env.docker.example .env.docker.secret
```

Edit `.env.docker.secret`:
```bash
nano .env.docker.secret
```

Set these values:
```
AUTOCHECKER_EMAIL=d.zhechev@innopolis.university
AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG
LMS_API_KEY=Abcd1234
```

## Step 3: Start Docker containers

```bash
docker compose --env-file .env.docker.secret up --build -d
```

Wait 30 seconds for containers to start.

## Step 4: Run ETL pipeline

```bash
curl -X POST http://localhost:42002/pipeline/sync \
  -H 'Authorization: Bearer Abcd1234' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Expected output: `{"new_records":6323,"total_records":6323}`

## Step 5: Verify deployment

```bash
curl -s http://localhost:42002/items/ \
  -H 'Authorization: Bearer Abcd1234' | head -c 200
```

## Step 6: Set up Qwen Code API on VM

```bash
cd ~
git clone https://github.com/sgo0/qwen-code-oai-proxy.git
cd ~/qwen-code-oai-proxy
```

Get API key from https://chat.qwen.ai/

Create `.env` file:
```bash
cat > .env << 'EOF'
QWEN_API_KEY=YOUR_KEY_HERE
PORT=8080
EOF
```

Edit and set your key:
```bash
nano .env
```

Install and run:
```bash
npm install
nohup npm start &
```

## Step 7: Update local .env.agent.secret

On your local machine, edit `c:\Users\gigachaDick\se-toolkit-lab-6\se-toolkit-lab-6\.env.agent.secret`:

```
LLM_API_KEY=your-qwen-api-key-here
LLM_API_BASE=http://10.93.26.28:8080/v1
LLM_MODEL=qwen3-coder-plus
```

## Step 8: Test connection

```bash
curl -s http://10.93.26.28:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_QWEN_API_KEY" \
  -d '{"model":"qwen3-coder-plus","messages":[{"role":"user","content":"Hello!"}]}'
```
