# 🚀 Akash Network Deployment Guide

This guide will help you deploy your Legal Document Simplifier on Akash Network.

## Prerequisites

✅ **Already Available in Your Project:**
- ✅ Akash CLI (`akash_cli/akash_0.20.0_windows_amd64/akash.exe`)
- ✅ Deployment files (`deploy-cpu.yaml`, `deploy-gpu.yaml`)
- ✅ Docker configuration
- ✅ Fixed application bugs

**What You Need:**
- 🔑 Akash wallet with AKT tokens (minimum 5-10 AKT for deployment)
- 🐳 Docker Hub or GitHub Container Registry account
- 🔧 Docker installed (optional, for local testing)

## 🎯 Deployment Options

### Option 1: 🏃‍♂️ Quick Deploy (Akash Sandbox) - **RECOMMENDED FOR TESTING**

**Fastest way to get started - No Docker build required!**

1. **Go to Akash Console:** https://console.akash.network/
2. **Create New Deployment → Sandbox**
3. **Fill in the form:**

```yaml
# Base Configuration
Image: python:3.11-slim
Container Port: 8080
Expose As: 80
Global Access: Yes

# Environment Variables
API_KEY=your-secret-key-here
FAST_TEST=1
CORS_ORIGINS=*
LOG_LEVEL=info

# Command (copy exactly):
/bin/sh -lc "
apt-get update && apt-get install -y --no-install-recommends git curl && \
git clone https://github.com/gabsgj/hackOdisha.git /app && \
cd /app && pip install --no-cache-dir flask flask-cors werkzeug prometheus-client requests gunicorn && \
gunicorn -w 2 -k gthread -b 0.0.0.0:8080 app.wsgi:application
"

# Resources
CPU: 1 vCPU
Memory: 2 GB
Storage: 5 GB
```

4. **Deploy and wait** for the URL
5. **Test immediately** - No AI dependencies needed!

### Option 2: 🏗️ Production Deploy (Custom Docker)

**For production use with full AI capabilities**

#### Step 1: Build and Push Docker Image

```powershell
# 1. Build the Docker image
docker build -t your-dockerhub-username/legal-simplifier:latest .

# 2. Push to Docker Hub
docker login
docker push your-dockerhub-username/legal-simplifier:latest
```

#### Step 2: Update Deployment File

Edit `deploy-cpu.yaml` or `deploy-gpu.yaml`:

```yaml
services:
  athenis:
    image: your-dockerhub-username/legal-simplifier:latest  # ← Change this
    env:
      - API_KEY=your-production-api-key-here
      - EXTERNAL_LLM_API_URL=https://api.openai.com/v1/chat/completions  # Optional
      - EXTERNAL_LLM_API_KEY=your-openai-key  # Optional
      - RATE_LIMIT_PER_MIN=60
```

#### Step 3: Deploy with Akash CLI

```powershell
# Navigate to project directory
cd d:\hackOdisha

# Set up Akash CLI
$env:PATH += ";d:\hackOdisha\akash_cli\akash_0.20.0_windows_amd64"

# Create wallet (if you don't have one)
akash keys add my-wallet

# Fund your wallet (get AKT tokens from an exchange)
# Send at least 10 AKT to your wallet address

# Create deployment
akash tx deployment create deploy-cpu.yaml --from my-wallet --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2

# Get deployment ID from output, then bid
akash query deployment list --owner $(akash keys show my-wallet -a) --node https://rpc.akash.forbole.com:443

# List bids for your deployment
akash query market bid list --node https://rpc.akash.forbole.com:443

# Create lease (choose a provider)
akash tx market lease create --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --from my-wallet --dseq YOUR_DEPLOYMENT_ID --provider PROVIDER_ADDRESS

# Send manifest
akash provider send-manifest deploy-cpu.yaml --node https://rpc.akash.forbole.com:443 --from my-wallet --provider PROVIDER_ADDRESS

# Get service status and URL
akash provider lease-status --node https://rpc.akash.forbole.com:443 --from my-wallet --provider PROVIDER_ADDRESS
```

## 🔧 Configuration Options

### For Fast Testing (No AI)
```bash
API_KEY=your-secret-key
FAST_TEST=1
CORS_ORIGINS=*
```

### For External LLM (Recommended)
```bash
API_KEY=your-secret-key
EXTERNAL_LLM_API_URL=https://api.openai.com/v1/chat/completions
EXTERNAL_LLM_API_KEY=your-openai-key
EXTERNAL_LLM_FORMAT=openai
RATE_LIMIT_PER_MIN=60
```

### For Local AI (GPU Required)
```bash
API_KEY=your-secret-key
MODEL_NAME=TinyLlama/TinyLlama-1.1B-Chat-v1.0
QUANTIZE=8bit
RATE_LIMIT_PER_MIN=20
```

## 🧪 Testing Your Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-akash-url.com/api/v1/health

# Document simplification
curl -X POST https://your-akash-url.com/api/simplify \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "The party of the first part hereby agrees to indemnify the party of the second part."}'

# File upload
curl -X POST https://your-akash-url.com/gofr/ingest \
  -H "X-API-Key: your-secret-key" \
  -F "file=@sample-contract.pdf"
```

## 💰 Cost Estimation

| Resource Tier | CPU | Memory | Storage | Est. Cost/Month |
|---------------|-----|---------|---------|-----------------|
| **Minimal**   | 1   | 2GB     | 5GB     | ~$5-10 AKT     |
| **Standard**  | 2   | 4GB     | 10GB    | ~$15-25 AKT    |
| **GPU**       | 4   | 8GB     | 20GB+GPU| ~$50-100 AKT   |

## 🚨 Troubleshooting

### Common Issues:

1. **"Image not found"** → Make sure Docker image is public and pushed correctly
2. **"Port 8080 not accessible"** → Check expose configuration in deployment YAML
3. **"API returns 500"** → Check logs with `akash provider lease-logs`
4. **"Out of AKT"** → Ensure wallet has sufficient balance for deployment + fees

### Getting Logs:
```bash
akash provider lease-logs --node https://rpc.akash.forbole.com:443 --from my-wallet --provider PROVIDER_ADDRESS
```

## 🎯 Recommended Deployment Path

**For First-Time Users:**

1. ✅ **Start with Sandbox** (Option 1) - Get it working in 5 minutes
2. ✅ **Test all endpoints** with your API key  
3. ✅ **If satisfied, upgrade** to Production (Option 2)
4. ✅ **Add external LLM** for real AI capabilities

**Result:** A fully functional legal document simplifier running on decentralized infrastructure! 🎉

## 📞 Support

- **Akash Network:** https://discord.gg/akash
- **Documentation:** https://docs.akash.network/
- **Console:** https://console.akash.network/

---

**Ready to deploy? Start with the Sandbox option above! 🚀**
