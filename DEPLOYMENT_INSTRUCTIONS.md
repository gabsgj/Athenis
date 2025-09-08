# 🚀 AKASH CPU DEPLOYMENT - STEP BY STEP GUIDE

## ✅ Prerequisites Check

**What you need:**
- ✅ Akash wallet with 10+ AKT tokens
- ✅ Akash CLI (already available: `akash_cli\akash_0.20.0_windows_amd64\akash.exe`)
- ✅ Your app code (ready in this repository)

## 🎯 OPTION 1: Quick Deploy (Console) - RECOMMENDED

### Step 1: Go to Akash Console
1. Visit: **https://console.akash.network/**
2. Connect Keplr wallet
3. Ensure wallet has 10+ AKT

### Step 2: Deploy via Console
1. Click **"Deploy"** → **"Build Your Template"**
2. **Copy these exact settings:**

```
Docker Image: python:3.11-slim
Container Port: 8080
Expose As: 80
Global Access: ✅ Enabled
```

**Environment Variables:**
```
API_KEY=hackodisha-cpu-deploy-2025-secure-key
FAST_TEST=1
CORS_ORIGINS=*
LOG_LEVEL=info
PORT=8080
RATE_LIMIT_PER_MIN=30
```

**Startup Command:**
```
/bin/sh -c "apt-get update && apt-get install -y git curl && git clone https://github.com/gabsgj/athenis.git /app && cd /app && pip install --no-cache-dir flask flask-cors werkzeug prometheus-client requests gunicorn python-dotenv pdfminer.six python-docx && gunicorn --bind 0.0.0.0:8080 --workers 2 --worker-class gthread app.wsgi:application"
```

**Resources:**
- CPU: 1000 millicores (1 vCPU)
- Memory: 2048 MB (2GB)
- Storage: 8192 MB (8GB)

### Step 3: Deploy & Test
1. Click **"Create Deployment"**
2. Wait 3-5 minutes
3. Get your URL
4. Test: `https://your-url/api/v1/health`

---

## 🎯 OPTION 2: CLI Deploy (Advanced)

### Step 1: Setup CLI
```powershell
# Test CLI
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" version

# Create wallet (if needed)
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" keys add my-deployment-wallet

# Show wallet address
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" keys show my-deployment-wallet -a
```

### Step 2: Fund Wallet
1. **Copy wallet address** from above
2. **Send 15+ AKT** to this address (from exchange)
3. **Verify balance:**
```powershell
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" query bank balances $(& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" keys show my-deployment-wallet -a) --node https://rpc.akash.forbole.com:443
```

### Step 3: Deploy
```powershell
# Create deployment
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" tx deployment create deploy-cpu-working.yaml --from my-deployment-wallet --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --gas auto --gas-adjustment 1.5 --fees 10000uakt

# Get deployment ID (copy DSEQ number from output)
$DSEQ = "YOUR_DEPLOYMENT_ID_HERE"

# Wait 30 seconds for bids, then list them
Start-Sleep 30
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" query market bid list --node https://rpc.akash.forbole.com:443 --dseq $DSEQ

# Create lease with lowest bidder (replace PROVIDER_ADDRESS)
$PROVIDER = "PROVIDER_ADDRESS_FROM_BID_LIST"
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" tx market lease create --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --from my-deployment-wallet --dseq $DSEQ --provider $PROVIDER --gas auto --gas-adjustment 1.5 --fees 10000uakt

# Send manifest
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" provider send-manifest deploy-cpu-working.yaml --node https://rpc.akash.forbole.com:443 --from my-deployment-wallet --provider $PROVIDER --dseq $DSEQ

# Get service URL (wait 2-3 minutes first)
Start-Sleep 180
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" provider lease-status --node https://rpc.akash.forbole.com:443 --from my-deployment-wallet --provider $PROVIDER --dseq $DSEQ
```

---

## 🧪 Testing Your Deployment

Once deployed, test these endpoints:

```powershell
# Set your deployment URL
$URL = "https://your-akash-url.com"

# Health check
curl "$URL/api/v1/health"

# Frontend
curl "$URL/"

# API test with authentication
curl -X POST "$URL/api/simplify" -H "X-API-Key: hackodisha-cpu-deploy-2025-secure-key" -H "Content-Type: application/json" -d '{\"text\": \"The party hereby agrees to indemnify and hold harmless the other party.\"}'

# File upload test
curl -X POST "$URL/gofr/ingest" -F "file=@sample.txt"

# Risk analysis
curl -X POST "$URL/api/full-analysis" -H "X-API-Key: hackodisha-cpu-deploy-2025-secure-key" -H "Content-Type: application/json" -d '{\"text\": \"This contract automatically renews unless terminated 30 days prior.\"}'
```

**Expected Health Response:**
```json
{
  "ok": true,
  "status": "ready",
  "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "device": "cpu"
}
```

---

## 🎯 What Gets Deployed

Your deployment includes:

✅ **Full Flask Application**
- All API endpoints (`/api/*`)
- Frontend UI at root (`/`)
- File upload capability
- Risk detection
- Document processing

✅ **Working in Fast Test Mode**
- No AI dependencies needed
- Instant responses
- All features functional

✅ **Production Ready**
- Gunicorn WSGI server
- Error handling
- Rate limiting
- CORS enabled

---

## 💰 Cost Estimate

**Resources:** 1 CPU + 2GB RAM + 8GB Storage
**Estimated Cost:** ~$6-12 USD/month (12,000 uAKT)

---

## 🚨 Troubleshooting

### Deployment Issues:
```powershell
# Check deployment status
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" query deployment get --dseq $DSEQ --node https://rpc.akash.forbole.com:443

# Check logs
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" provider lease-logs --node https://rpc.akash.forbole.com:443 --from my-deployment-wallet --provider $PROVIDER --dseq $DSEQ
```

### Common Issues:
1. **"No bids received"** → Increase pricing in YAML
2. **"App not starting"** → Check logs for errors
3. **"Git clone failed"** → Ensure repo is public
4. **"Port not accessible"** → Wait 3-5 minutes for startup

---

## 🎉 Success Checklist

After deployment, you should have:

✅ **Working Health Endpoint:** `GET /api/v1/health`  
✅ **Functional Frontend:** `GET /` (HTML interface)  
✅ **Document Simplification:** `POST /api/simplify`  
✅ **Risk Analysis:** `POST /api/full-analysis`  
✅ **File Upload:** `POST /gofr/ingest`  
✅ **Rate Limiting:** Built-in protection  
✅ **Global Access:** Available worldwide  

---

## 🚀 QUICK START COMMANDS

**For Console Deployment (Easiest):**
1. Go to https://console.akash.network/
2. Copy settings from Option 1 above
3. Deploy in 5 minutes

**For CLI Deployment:**
```powershell
# Quick deployment script
$wallet = "my-deployment-wallet"
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" keys add $wallet
# Fund wallet with 15 AKT
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" tx deployment create deploy-cpu-working.yaml --from $wallet --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --gas auto --gas-adjustment 1.5 --fees 10000uakt
```

**Your app will be live and functional within 5-10 minutes! 🎯**
