import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil

def run(cmd):
    """Run a system command and print output in real-time"""
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end="")
    process.wait()

def install_akash():
    print("🔹 Downloading Akash CLI binary for Windows...")
    url = "https://github.com/ovrclk/akash/releases/download/v0.20.0/akash_0.20.0_windows_amd64.zip"
    zip_path = "akash.zip"
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall("akash_cli")

    bin_path = os.path.abspath("akash_cli/akash.exe")
    print(f"✅ Akash installed at {bin_path}")

    # Add to PATH
    os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]

    return bin_path

def setup_wallet(bin_path):
    print("🔹 Setting up Akash wallet...")
    run(f"{bin_path} keys add mywallet --recover")

def fund_wallet(bin_path):
    print("🔹 Requesting testnet tokens...")
    run(f"curl -X POST https://faucet.testnet.akash.network/faucet?address=$({bin_path} keys show mywallet -a)")

def deploy(bin_path):
    print("🔹 Creating deployment...")
    run(f"{bin_path} tx deployment create deploy.yml --from mywallet --node https://rpc.testnet.akash.network:443 --chain-id=akash-testnet-9 --gas auto --fees 5000uakt -y")

if __name__ == "__main__":
    bin_path = install_akash()
    setup_wallet(bin_path)
    fund_wallet(bin_path)
    deploy(bin_path)
    print("🎉 Deployment process finished. Check Akash status.")
