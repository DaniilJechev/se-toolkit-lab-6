#!/bin/bash
# Qwen Code API Setup Script for VM
# Run this on your VM: bash ~/se-toolkit-lab-6/setup-qwen-api.sh

set -e

echo "========================================"
echo "Qwen Code API Setup Script"
echo "========================================"
echo ""

# Step 1: Clone qwen-code-oai-proxy
echo "Step 1: Cloning qwen-code-oai-proxy..."
cd ~
if [ -d "qwen-code-oai-proxy" ]; then
    echo "Directory qwen-code-oai-proxy already exists."
else
    git clone https://github.com/sgo0/qwen-code-oai-proxy.git
    echo "Repository cloned."
fi

cd ~/qwen-code-oai-proxy

# Step 2: Create .env file
echo ""
echo "Step 2: Creating .env file..."
cat > .env << 'EOF'
# Qwen Code API Configuration
# Get your API key from: https://chat.qwen.ai/
QWEN_API_KEY=REPLACE_WITH_YOUR_QWEN_API_KEY
PORT=8080
EOF

echo ".env file created at ~/qwen-code-oai-proxy/.env"
echo ""
echo "IMPORTANT: Edit .env and set your QWEN_API_KEY"
echo "Get your key from: https://chat.qwen.ai/"
echo ""

# Step 3: Install dependencies and run
echo "Step 3: Installing dependencies..."
npm install

echo ""
echo "Step 4: Starting Qwen API proxy..."
echo "The service will start on http://localhost:8080/v1"
echo ""
echo "To run in background, use: nohup npm start &"
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit ~/qwen-code-oai-proxy/.env and set QWEN_API_KEY"
echo "2. Run: cd ~/qwen-code-oai-proxy && npm start"
echo "3. Test: curl http://localhost:8080/v1/chat/completions ..."
