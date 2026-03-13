# Lab 6 - Setup Instructions for DaniilJechev

## Completed Steps ✅

1. **Configured `.env.docker.secret`**:
   - `AUTOCHECKER_EMAIL=d.zhechev@innopolis.university`
   - `AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG`
   - `LMS_API_KEY=Abcd1234`

2. **Created `.env.agent.secret`**:
   - `LLM_API_BASE=http://10.93.26.28:8080/v1`
   - `LLM_MODEL=qwen3-coder-plus`
   - **TODO**: Set `LLM_API_KEY` after getting Qwen API key

3. **Fixed `docker-compose.yml`**: Changed to use Docker Hub images instead of university mirrors

4. **Git push completed**: Changes pushed to https://github.com/DaniilJechev/se-toolkit-lab-6

---

## Manual Steps Required 📋

### Step 1: Start Docker Desktop (Local Machine)

1. Open Docker Desktop application
2. Wait until the status shows "Docker Desktop is running"
3. Run the setup script:
   ```cmd
   cd c:\Users\gigachaDick\se-toolkit-lab-6\se-toolkit-lab-6
   setup-local.bat
   ```

### Step 2: Verify Local Deployment

1. Open http://localhost:42002/docs in browser
2. Click "Authorize" button
3. Enter API key: `Abcd1234`
4. Run `POST /pipeline/sync`
5. Verify with `GET /items/` - should return non-empty array

### Step 3: Deploy to VM (10.93.26.28)

Run these commands in WSL/bash:

```bash
# Copy files to VM
cd ~/se-toolkit-lab-6
scp -r * student@10.93.26.28:~/se-toolkit-lab-6/

# SSH to VM and setup
ssh student@10.93.26.28 << 'EOF'
cd ~/se-toolkit-lab-6

# Configure environment
cp .env.docker.example .env.docker.secret
sed -i 's/AUTOCHECKER_EMAIL=.*/AUTOCHECKER_EMAIL=d.zhechev@innopolis.university/' .env.docker.secret
sed -i 's/AUTOCHECKER_PASSWORD=.*/AUTOCHECKER_PASSWORD=DaniilJechevBFG9KGG/' .env.docker.secret
sed -i 's/LMS_API_KEY=.*/LMS_API_KEY=Abcd1234/' .env.docker.secret

# Start containers
docker compose --env-file .env.docker.secret up --build -d

# Wait and populate DB
sleep 30
curl -X POST http://localhost:42002/pipeline/sync -H "Authorization: Bearer Abcd1234" -H "Content-Type: application/json" -d '{}'

# Verify
curl -s http://localhost:42002/items/ -H "Authorization: Bearer Abcd1234" | head -c 200
EOF
```

### Step 4: Set Up Qwen Code API on VM

On the VM (via SSH):

```bash
# Clone Qwen proxy
cd ~
git clone https://github.com/sgo0/qwen-code-oai-proxy.git
cd qwen-code-oai-proxy

# Get API key from https://chat.qwen.ai/
# Then create .env file:
cat > .env << 'ENVEOF'
QWEN_API_KEY=YOUR_KEY_HERE
PORT=8080
ENVEOF

# Install and run
npm install
nohup npm start &
```

### Step 5: Update `.env.agent.secret`

After getting Qwen API key, edit locally:
```
LLM_API_KEY=your-qwen-api-key-here
```

### Step 6: Test Agent

```bash
curl -s http://10.93.26.28:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_QWEN_API_KEY" \
  -d '{"model":"qwen3-coder-plus","messages":[{"role":"user","content":"Hello!"}]}'
```

---

## Scripts Created

- `setup-local.bat` - Local setup script (Windows)
- `deploy-to-vm.sh` - VM deployment script (bash)
- `setup-qwen-api.sh` - Qwen API setup script (bash)

---

## Credentials Summary

| Service | Value |
|---------|-------|
| VM IP | 10.93.26.28 |
| VM User | student |
| LMS API Key | Abcd1234 |
| Autochecker Email | d.zhechev@innopolis.university |
| Autochecker Password | DaniilJechevBFG9KGG |
| GitHub Token | (set in your environment) |

---

## Troubleshooting

### Docker Desktop not starting
- Restart Docker Desktop application
- Check if Hyper-V is enabled on Windows

### Port conflicts
```cmd
netstat -ano | findstr :42002
taskkill /F /PID <PID>
```

### SSH connection refused
- Check VM is accessible: `ping 10.93.26.28`
- Verify SSH key is added: `ssh-copy-id student@10.93.26.28`
