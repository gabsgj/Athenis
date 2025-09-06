Param(
  [switch]$UseRealModel
)

$ErrorActionPreference = 'Stop'

Write-Host "==> Dev startup (no Docker)"

# Load .env if present
$envFile = Join-Path (Get-Location) ".env"
if (Test-Path $envFile) {
  Write-Host "Loading .env ..."
  Get-Content $envFile | ForEach-Object {
    if (-not [string]::IsNullOrWhiteSpace($_) -and -not $_.Trim().StartsWith('#')) {
      $kv = $_.Split('=',2)
      if ($kv.Length -eq 2) {
        $name = $kv[0].Trim()
        $val = $kv[1].Trim()
        # Remove surrounding quotes if any
        if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Trim('"') }
        if ($val.StartsWith("'") -and $val.EndsWith("'")) { $val = $val.Trim("'") }
        Set-Item -Path ("Env:" + $name) -Value $val
      }
    }
  }
}

if (-not $env:API_KEY) { $env:API_KEY = "dev-key" }
if (-not $env:MODEL_NAME) { $env:MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" }
if (-not $env:QUANTIZE) { $env:QUANTIZE = "8bit" }
$env:GOFR_URL = "http://localhost:8090"
if ($UseRealModel) {
  $env:FAST_TEST = "0"
} else {
  # Use stub generation to avoid heavy model downloads for dev
  $env:FAST_TEST = "1"
}

# Setup Python venv
if (-not (Test-Path ".venv")) {
  Write-Host "Creating Python venv ..."
  python -m venv .venv
}

$venvActivate = ".venv/Scripts/Activate.ps1"
if (-not (Test-Path $venvActivate)) {
  Write-Error "Virtual env activation script not found at $venvActivate"
  exit 1
}
. $venvActivate

# Install Python deps
Write-Host "Installing Python dependencies ..."
python -m pip install --upgrade pip

if ($UseRealModel) {
  # Install PyTorch (CPU) explicitly on Windows to avoid CUDA wheel issues
  Write-Host "Installing torch (CPU) ..."
  pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
} else {
  Write-Host "FAST_TEST mode: skipping torch install."
}

# Install Flask and core libs early
pip install flask==3.0.3 flask-cors==4.0.0 prometheus-client==0.20.0 structlog==24.1.0 loguru==0.7.2 python-dotenv==1.0.1 requests==2.32.3
# Ensure numpy is present for embeddings fallback (prefer a recent wheel)
pip install "numpy>=2.1.0"

# Install remaining requirements
$tmpReq = Join-Path (Get-Location) ".req-dev-nobnb.txt"
if (-not $UseRealModel) {
  Write-Host "FAST_TEST mode: filtering out heavy ML deps (torch/transformers/etc)."
  Get-Content requirements.txt |
    Where-Object { $_ -notmatch '^(\s*(torch|bitsandbytes|transformers|accelerate|sentence-transformers)\b)' } |
    Set-Content $tmpReq
} else {
  Get-Content requirements.txt | Set-Content $tmpReq
}
pip install -r $tmpReq

# Sanity check imports (PowerShell-friendly)
$pyCheck = @'
import sys
print("Python", sys.version)
try:
  import flask
  print("Flask OK", flask.__version__)
except Exception as e:
  print("Flask import failed:", e)
try:
  import transformers
  print("Transformers OK", transformers.__version__)
except Exception as e:
  print("Transformers import failed:", e)
'@
$tmpPy = Join-Path $env:TEMP ("sanity_check_" + (Get-Random) + ".py")
$pyCheck | Out-File -FilePath $tmpPy -Encoding utf8 -Force
python $tmpPy
Remove-Item $tmpPy -ErrorAction SilentlyContinue

# Verify Go (optional)
$NoGo = $false
try { go version | Out-Null } catch { Write-Warning "Go not found in PATH. Upload via Go service will be disabled. Paste text to test."; $NoGo = $true }

# Start Go ingestion service in background job (if available)
Write-Host "Starting Go ingestion service on :8090 ..."
$repoRoot = (Get-Location).Path
if (-not $NoGo) {
  $goJob = Start-Job -Name gofr -ScriptBlock {
    param($root)
    Set-Location $root
    & go run .\gofr\main.go
  } -ArgumentList $repoRoot
  Start-Sleep -Seconds 2
} else {
  Write-Host "Skipping Go service startup."
}

# Start Flask app (foreground)
Write-Host "Starting Flask app on :8080 ..."
$env:PORT = "8080"
python -m app.app

# On exit, stop background job if running
if ($goJob -and $goJob.State -eq 'Running') {
  Write-Host "Stopping Go job ..."
  Stop-Job $goJob | Out-Null
  Remove-Job $goJob | Out-Null
}
