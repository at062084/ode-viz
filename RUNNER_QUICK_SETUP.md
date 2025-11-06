# Self-Hosted Runner - Quick Setup Commands

## ⚡ Quick Command Reference

You've already installed the runner. Here's what to do next:

### 1. Install as Service

```bash
# Switch to docker user (if not already)
su - docker

# Navigate to runner directory
cd ~/actions-runner

# Install service
sudo ./svc.sh install docker
```

### 2. Start and Enable

```bash
# Start the service
sudo ./svc.sh start

# Enable auto-start on boot
sudo systemctl enable actions.runner.*
```

### 3. Verify

```bash
# Check service status
sudo ./svc.sh status

# Or using systemctl
sudo systemctl status actions.runner.*

# Should show: "Active: active (running)"
```

### 4. Check on GitHub

1. Go to: https://github.com/at062084/ode-viz/settings/actions/runners
2. You should see your runner with a green dot (Idle)

## ✅ That's It!

The workflow is already configured to use your self-hosted runner.

## 🔧 Common Commands

```bash
# View logs
sudo journalctl -u actions.runner.* -f

# Restart
sudo ./svc.sh restart

# Stop
sudo ./svc.sh stop
```

## 📊 Service Status Quick Check

```bash
# All-in-one status check
echo "Service Status:" && sudo ./svc.sh status && \
echo -e "\nEnabled on boot:" && sudo systemctl is-enabled actions.runner.* && \
echo -e "\nRecent logs:" && sudo journalctl -u actions.runner.* -n 10
```

## 🚀 Test Your Setup

After the service is running:

1. Go to GitHub Actions tab
2. Click "Run workflow"
3. Select your branch
4. Watch it deploy!

## 💡 Benefits of Self-Hosted Runner

✅ **No SSH setup needed** - Runs directly on the server
✅ **No IP whitelisting** - Already on your network
✅ **Faster deployments** - No image transfers
✅ **Free** - No minute limits

See [SELF_HOSTED_RUNNER_SETUP.md](SELF_HOSTED_RUNNER_SETUP.md) for complete documentation.
