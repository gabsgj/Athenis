# Build and push Docker image (after installing Docker Desktop)

# Option 1: Match deploy-cpu.yaml naming
docker build -t ghcr.io/gabsgj/hackodisha/athenis:latest .
docker push ghcr.io/gabsgj/hackodisha/athenis:latest

# Option 2: Use your preferred naming (update YAML files accordingly)
# docker build -t ghcr.io/gabsgj/athenis/athenis:latest .
# docker push ghcr.io/gabsgj/athenis/athenis:latest

# Alternative: Use a public base image with git clone (no Docker build needed)
# This is used in deploy-cpu-working.yaml and works immediately!
