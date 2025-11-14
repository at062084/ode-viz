# Setting Up Self-Hosted GitHub Actions Runner as a Service

## Current Status

✅ Runner installed and configured
✅ Running on Ubuntu 22.04/24.04 (systemd)
✅ Runner files owned by `docker` user
✅ Connected to GitHub

## Step 1: Install Runner as a Service

The runner includes a script to install itself as a systemd service.

### 1.1 Navigate to Runner Directory

```bash
cd ~/actions-runner
# Or wherever you extracted the runner
```

### 1.2 Install the Service

Run the installation script as the user who will run the service (docker user):

```bash
# Switch to docker user if not already
su - docker

# Navigate to runner directory
cd ~/actions-runner

# Install as a service
sudo ./svc.sh install docker
```

This creates a systemd service file at `/etc/systemd/system/actions.runner.*.service`

### 1.3 Start the Service

```bash
# Start the runner service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### 1.4 Enable Auto-Start on Boot

```bash
# Enable the service to start on boot
sudo systemctl enable actions.runner.$(cat .runner)
```

## Step 2: Verify the Service

### Check Service Status

```bash
# Via the svc.sh script
sudo ./svc.sh status

# Or directly via systemctl
sudo systemctl status actions.runner.*
```

You should see:
```
● actions.runner.at062084-ode-viz.pulphost.service - GitHub Actions Runner (at062084-ode-viz.pulphost)
     Loaded: loaded (/etc/systemd/system/actions.runner.at062084-ode-viz.pulphost.service; enabled)
     Active: active (running) since ...
```

### Check Runner Logs

```bash
# View live logs
sudo journalctl -u actions.runner.* -f

# View recent logs
sudo journalctl -u actions.runner.* -n 50
```

### Check on GitHub

1. Go to your repository: `https://github.com/at062084/ode-viz`
2. Settings → Actions → Runners
3. You should see your runner listed as "Idle" (green dot)

## Step 3: Update GitHub Actions Workflow

Now update your workflow to use the self-hosted runner instead of GitHub's runners.

Edit `.github/workflows/deploy-superset.yml`:

```yaml
jobs:
  build-and-deploy:
    runs-on: self-hosted  # Changed from ubuntu-latest

    steps:
      # Remove the "Show GitHub Actions IP" step - not needed anymore!
      # Your runner has a known IP (the PULPHOST IP)

      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # ... rest of your steps
```

## Step 4: Simplify Deployment (Optional)

Since the runner is ON the PULPHOST, you can simplify deployment significantly!

### Option A: Runner on PULPHOST (Recommended)

If the runner is running ON the deployment server, you don't need SSH at all:

```yaml
jobs:
  build-and-deploy:
    runs-on: self-hosted

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t superset-app:latest .

      - name: Deploy with Docker Compose
        run: |
          cd ${{ github.workspace }}

          # Create .env if it doesn't exist
          if [ ! -f .env ]; then
            cp .env.example .env
            echo "⚠️  Created .env - please update with your configuration"
          fi

          # Deploy
          docker compose down
          docker compose up -d

          # Show status
          docker compose ps

      - name: Verify deployment
        run: |
          echo "Waiting for services to be healthy..."
          sleep 10
          docker compose ps
          echo "✅ Deployment completed!"
```

### Option B: Runner on Different Machine

If runner is on a different machine, keep the SSH approach but remove IP detection:

```yaml
jobs:
  build-and-deploy:
    runs-on: self-hosted

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t superset-app:latest .

      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.PULPHOST }} >> ~/.ssh/known_hosts

      # ... rest of SSH deployment steps
```

## Service Management Commands

### Start/Stop/Restart

```bash
cd ~/actions-runner

# Start
sudo ./svc.sh start

# Stop
sudo ./svc.sh stop

# Restart
sudo ./svc.sh restart

# Check status
sudo ./svc.sh status
```

### Or use systemctl directly:

```bash
# Start
sudo systemctl start actions.runner.*

# Stop
sudo systemctl stop actions.runner.*

# Restart
sudo systemctl restart actions.runner.*

# Status
sudo systemctl status actions.runner.*

# Enable auto-start
sudo systemctl enable actions.runner.*

# Disable auto-start
sudo systemctl disable actions.runner.*
```

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u actions.runner.* -n 100
```

**Check permissions:**
```bash
# Ensure docker user owns the runner directory
ls -la ~/actions-runner
sudo chown -R docker:docker ~/actions-runner
```

### Runner Shows Offline on GitHub

**Check if service is running:**
```bash
sudo ./svc.sh status
```

**Restart the service:**
```bash
sudo ./svc.sh restart
```

**Check network connectivity:**
```bash
# Test GitHub connectivity
curl -I https://github.com
```

### Permission Errors with Docker

**Ensure docker user is in docker group:**
```bash
sudo usermod -aG docker docker
```

**Restart the service after adding to group:**
```bash
sudo ./svc.sh restart
```

### Service Fails After Reboot

**Check if service is enabled:**
```bash
sudo systemctl is-enabled actions.runner.*
```

**Enable it:**
```bash
sudo systemctl enable actions.runner.*
```

**Check boot logs:**
```bash
sudo journalctl -u actions.runner.* -b
```

## Uninstall Service (if needed)

```bash
cd ~/actions-runner

# Stop the service
sudo ./svc.sh stop

# Uninstall the service
sudo ./svc.sh uninstall

# Remove the runner
sudo rm -rf ~/actions-runner
```

## Security Considerations

### Runner Security

1. **Isolate the runner** - Consider running in a container or VM
2. **Limit repository access** - Only connect to repositories you trust
3. **Regular updates** - Keep the runner software updated
4. **Monitor logs** - Watch for suspicious activity

### Update Runner

```bash
cd ~/actions-runner

# Stop the service
sudo ./svc.sh stop

# Download new version (check https://github.com/actions/runner/releases)
curl -o actions-runner-linux-x64-2.314.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.314.0/actions-runner-linux-x64-2.314.0.tar.gz

# Extract (as docker user)
tar xzf ./actions-runner-linux-x64-2.314.0.tar.gz

# Start the service
sudo ./svc.sh start
```

## Benefits of Self-Hosted Runner

✅ **No IP whitelisting needed** - Runner has a known, fixed location
✅ **Faster deployments** - No need to transfer Docker images
✅ **More control** - Custom tools, cached dependencies
✅ **Free** - No minute limits for private repos
✅ **Direct access** - Can access local resources

## Verification Checklist

- [ ] Service is running: `sudo ./svc.sh status`
- [ ] Service is enabled: `sudo systemctl is-enabled actions.runner.*`
- [ ] Runner shows "Idle" on GitHub (Settings → Actions → Runners)
- [ ] Docker is accessible to docker user: `docker ps` (as docker user)
- [ ] Workflow updated to use `runs-on: self-hosted`
- [ ] Test workflow run successful

## Next Steps

1. Update your workflow file (see Step 3 above)
2. Commit and push the changes
3. Trigger a workflow run to test
4. Monitor the first few runs to ensure everything works

## Quick Summary

```bash
# Install as service (as docker user)
cd ~/actions-runner
sudo ./svc.sh install docker

# Start and enable
sudo ./svc.sh start
sudo systemctl enable actions.runner.*

# Verify
sudo ./svc.sh status

# Check on GitHub
# Settings → Actions → Runners → Should show "Idle"
```

That's it! Your runner will now start automatically on boot and run your GitHub Actions workflows.
