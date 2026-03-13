# Lab 6 VM Deployment Script with Password
# Run this in PowerShell

$VM_USER = "student"
$VM_IP = "10.93.26.28"
$VM_PASSWORD = "Abcd1234"
$VM_PATH = "~/se-toolkit-lab-6"

Write-Host "========================================"
Write-Host "Lab 6 VM Deployment"
Write-Host "========================================"
Write-Host ""

# Step 1: Create directory and copy files via SCP with password
Write-Host "Step 1: Connecting to VM..."

# Use PSCP or manual copy
Write-Host "Please run these commands manually in PowerShell:"
Write-Host ""
Write-Host "ssh $VM_USER@$VM_IP"
Write-Host "# Password: $VM_PASSWORD"
Write-Host ""
Write-Host "Once connected, run:"
Write-Host "cd ~"
Write-Host "git clone https://github.com/DaniilJechev/se-toolkit-lab-6.git"
Write-Host "cd ~/se-toolkit-lab-6"
Write-Host "cp .env.docker.example .env.docker.secret"
Write-Host ""

Write-Host "========================================"
Write-Host "OR use this one-liner:"
Write-Host "========================================"
Write-Host ""
Write-Host "ssh student@10.93.26.28 'bash -s' < deploy-vm-remote.sh"
Write-Host ""
