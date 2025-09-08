# Athenis - Legal Document Simplifier
## Complete Akash Network Deployment Guide

Your app is **ready to deploy** on Akash Network! Here's everything you need:

## 🚀 Quick Deployment Steps

### 1. **Fund Your Wallet**
Your wallet address: `akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh`

**Option A: Get Testnet Tokens (Free)**
- Visit: https://faucet.akashnet.net/
- Enter your address: `akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh`
- Get free testnet AKT

**Option B: Use Mainnet (Real tokens)**
- Buy AKT from exchanges (Osmosis, Kraken, etc.)
- Send to: `akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh`
- Minimum needed: ~0.5 AKT for deployment

### 2. **Deploy Commands**

**For Testnet:**
```powershell
# Check balance
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe query bank balances akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh --node https://rpc.sandbox-01.aksh.pw:443 --chain-id sandbox-01

# Deploy to testnet
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe tx deployment create deploy-testnet.yaml --from default --node https://rpc.sandbox-01.aksh.pw:443 --chain-id sandbox-01 --gas-prices 0.025uakt --gas auto --gas-adjustment 1.15 -y
```

**For Mainnet:**
```powershell
# Check balance
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe query bank balances akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh --node https://rpc.akashnet.net:443 --chain-id akashnet-2

# Deploy to mainnet
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe tx deployment create deploy-cpu-fixed.yaml --from default --node https://rpc.akashnet.net:443 --chain-id akashnet-2 --gas-prices 0.025uakt --gas auto --gas-adjustment 1.15 -y
```

### 3. **After Deployment**

Once deployed, you'll get a deployment ID (DSEQ). Use it to:

```powershell
# Check deployment status
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe query deployment get --owner akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh --dseq <DEPLOYMENT_ID> --node https://rpc.akashnet.net:443 --chain-id akashnet-2

# View bids
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe query market bid list --owner akash1u9uh2y5ad3re9s22c36sagedlct2qhk2g58gfh --dseq <DEPLOYMENT_ID> --node https://rpc.akashnet.net:443 --chain-id akashnet-2

# Create lease (accept a bid)
.\akash_cli\akash_0.20.0_windows_amd64\akash.exe tx market lease create --from default --dseq <DEPLOYMENT_ID> --provider <PROVIDER_ADDRESS> --node https://rpc.akashnet.net:443 --chain-id akashnet-2 --gas-prices 0.025uakt --gas auto --gas-adjustment 1.15 -y
```

## 🎯 **Your App Features**

### ✅ **What Works:**
- **Document Upload**: PDF, DOCX, TXT support
- **Text Analysis**: Simplify, summarize, risk detection
- **Streaming**: Real-time results via SSE
- **Multi-language**: Auto-detect + translate
- **Export**: JSON reports and printable format
- **UI**: Modern, responsive design
- **Backend**: Flask API with full integration

### ✅ **Technical Stack:**
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python 3.11, Flask, Gunicorn
- **AI**: Configurable (FAST_TEST mode for demo)
- **Deploy**: Docker-ready, Akash Network optimized
- **Resources**: 1 CPU, 2GB RAM, 8GB storage

## 🔧 **Configuration Options**

### Environment Variables:
- `FAST_TEST=1` - Demo mode (no real AI)
- `API_KEY` - Optional API key protection
- `CORS_ORIGINS=*` - CORS configuration
- `RATE_LIMIT_PER_MIN=30` - Rate limiting

### Pricing:
- **CPU-only**: ~$6-8/month
- **Testnet**: Free for testing

## 🌐 **Access Your App**

After successful deployment:
1. Get the service URI from lease status
2. Visit: `http://<provider-uri>` 
3. Your legal document simplifier is live!

## 📝 **Next Steps**

1. **Fund wallet** with AKT tokens
2. **Run deployment command** 
3. **Accept a bid** from providers
4. **Access your live app** on Akash Network
5. **Test all features** with real documents

## 🆘 **Need Help?**

- **Akash Discord**: https://discord.akash.network/
- **Documentation**: https://docs.akash.network/
- **Faucet**: https://faucet.akashnet.net/

---

**🎉 Your app is fully ready for Akash deployment!**
All dependencies resolved, repository URLs fixed, and frontend-backend integration complete.
