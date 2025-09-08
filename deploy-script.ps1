# 🚀 AKASH DEPLOYMENT - COPY & PASTE COMMANDS

# Step 1: Verify CLI
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" version

# Step 2: Create wallet (run once)
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" keys add hackodisha-wallet

# Step 3: Get wallet address (send 15 AKT here)
$WALLET_ADDRESS = & "akash_cli\akash_0.20.0_windows_amd64\akash.exe" keys show hackodisha-wallet -a
Write-Host "🏦 Send 15+ AKT to: $WALLET_ADDRESS"
Write-Host "⏳ Press Enter after funding wallet..."
Read-Host

# Step 4: Verify balance
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" query bank balances $WALLET_ADDRESS --node https://rpc.akash.forbole.com:443

# Step 5: Create deployment
Write-Host "🚀 Creating deployment..."
$DEPLOY_OUTPUT = & "akash_cli\akash_0.20.0_windows_amd64\akash.exe" tx deployment create deploy-cpu-working.yaml --from hackodisha-wallet --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --gas auto --gas-adjustment 1.5 --fees 10000uakt --yes

# Extract DSEQ from output
$DSEQ = ($DEPLOY_OUTPUT | Select-String "dseq: (\d+)").Matches.Groups[1].Value
Write-Host "📋 Deployment ID (DSEQ): $DSEQ"

# Step 6: Wait for bids
Write-Host "⏳ Waiting 60 seconds for bids..."
Start-Sleep 60

# Step 7: List bids
Write-Host "📋 Available bids:"
$BIDS = & "akash_cli\akash_0.20.0_windows_amd64\akash.exe" query market bid list --node https://rpc.akash.forbole.com:443 --dseq $DSEQ

# Extract first provider (you can choose different one)
$PROVIDER = ($BIDS | Select-String "provider: (.+)").Matches.Groups[1].Value | Select-Object -First 1
Write-Host "🏢 Selected provider: $PROVIDER"

# Step 8: Create lease
Write-Host "📝 Creating lease..."
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" tx market lease create --node https://rpc.akash.forbole.com:443 --chain-id akashnet-2 --from hackodisha-wallet --dseq $DSEQ --provider $PROVIDER --gas auto --gas-adjustment 1.5 --fees 10000uakt --yes

# Step 9: Send manifest
Write-Host "📦 Sending manifest..."
& "akash_cli\akash_0.20.0_windows_amd64\akash.exe" provider send-manifest deploy-cpu-working.yaml --node https://rpc.akash.forbole.com:443 --from hackodisha-wallet --provider $PROVIDER --dseq $DSEQ

# Step 10: Wait for deployment
Write-Host "⏳ Waiting 3 minutes for deployment..."
Start-Sleep 180

# Step 11: Get service URL
Write-Host "🌐 Getting service URL..."
$STATUS = & "akash_cli\akash_0.20.0_windows_amd64\akash.exe" provider lease-status --node https://rpc.akash.forbole.com:443 --from hackodisha-wallet --provider $PROVIDER --dseq $DSEQ

# Extract URL
$URL = ($STATUS | Select-String "uri: (.+)").Matches.Groups[1].Value
Write-Host "🎉 Your app is live at: $URL" -ForegroundColor Green

# Test deployment
Write-Host "🧪 Testing deployment..."
curl "$URL/api/v1/health"

Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "📋 Save these details:"
Write-Host "   DSEQ: $DSEQ"
Write-Host "   Provider: $PROVIDER" 
Write-Host "   URL: $URL"
