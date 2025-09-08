# Test script to verify deployment readiness
param(
    [string]$DeploymentUrl = "https://your-akash-url.com"
)

Write-Host "🧪 Testing Akash Deployment: $DeploymentUrl" -ForegroundColor Green

# Test 1: Health Check
Write-Host "`n1️⃣ Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$DeploymentUrl/api/v1/health" -Method GET
    Write-Host "✅ Health Check: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health Check Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Frontend
Write-Host "`n2️⃣ Testing Frontend..." -ForegroundColor Yellow
try {
    $frontend = Invoke-WebRequest -Uri "$DeploymentUrl/" -Method GET
    if ($frontend.StatusCode -eq 200) {
        Write-Host "✅ Frontend: Accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: API with Authentication
Write-Host "`n3️⃣ Testing API Endpoint..." -ForegroundColor Yellow
try {
    $headers = @{
        "X-API-Key" = "hackodisha-cpu-deploy-2025-secure-key"
        "Content-Type" = "application/json"
    }
    $body = @{
        "text" = "The party hereby agrees to indemnify and hold harmless."
    } | ConvertTo-Json
    
    $api = Invoke-RestMethod -Uri "$DeploymentUrl/api/simplify" -Method POST -Headers $headers -Body $body
    Write-Host "✅ API Simplify: Working" -ForegroundColor Green
} catch {
    Write-Host "❌ API Test Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎉 Deployment Test Complete!" -ForegroundColor Green
Write-Host "If all tests pass, your deployment is working correctly." -ForegroundColor Cyan
