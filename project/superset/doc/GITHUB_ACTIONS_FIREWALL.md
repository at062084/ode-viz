# GitHub Actions and Firewall IP Whitelisting

## The Challenge

GitHub Actions runners use **dynamic IP addresses** from Microsoft Azure's infrastructure. The IP changes with each workflow run, making traditional IP whitelisting difficult.

## ✅ Recommended: Self-Hosted Runner (Already Configured!)

**Good news!** This repository is now configured to use a **self-hosted runner** on PULPHOST. This completely eliminates the firewall issue because the runner is already on your server.

👉 See [SELF_HOSTED_RUNNER_SETUP.md](SELF_HOSTED_RUNNER_SETUP.md) for setup instructions.

No SSH required, no IP whitelisting needed - everything runs locally!

---

## Alternative Solutions

If you prefer to use GitHub's hosted runners instead, here are the options:

## Solution Options

### Option 1: Whitelist GitHub's IP Ranges (Recommended for most cases)

GitHub publishes their IP ranges via an API. You can whitelist all of them.

#### Get the IP Ranges

```bash
# Fetch GitHub's current IP ranges
curl https://api.github.com/meta | jq -r '.actions[]'
```

This returns IP ranges like:
```
4.175.114.51/32
13.64.0.0/16
13.65.0.0/16
... (and many more)
```

#### Add to Firewall (UFW example)

```bash
# On your PULPHOST server
# Download and whitelist GitHub Actions IPs
curl -s https://api.github.com/meta | \
  jq -r '.actions[]' | \
  while read ip; do
    sudo ufw allow from $ip to any port 22 comment 'GitHub Actions'
  done

# Verify rules
sudo ufw status numbered
```

#### Automatic Script

Save this script on your server as `update-github-ips.sh`:

```bash
#!/bin/bash
# Update GitHub Actions IP whitelist

echo "Fetching GitHub Actions IP ranges..."

# Get current IPs
GITHUB_IPS=$(curl -s https://api.github.com/meta | jq -r '.actions[]')

# Remove old GitHub Actions rules
echo "Removing old GitHub Actions firewall rules..."
sudo ufw status numbered | grep 'GitHub Actions' | awk '{print $1}' | tac | while read num; do
  yes | sudo ufw delete $num
done

# Add new rules
echo "Adding new GitHub Actions firewall rules..."
for ip in $GITHUB_IPS; do
  sudo ufw allow from $ip to any port 22 comment 'GitHub Actions'
done

echo "Done! GitHub Actions IPs updated."
sudo ufw reload
```

Make it executable and run:
```bash
chmod +x update-github-ips.sh
sudo ./update-github-ips.sh
```

**Note:** GitHub's IP ranges can change, so run this script periodically (monthly recommended).

---

### Option 2: Use a Jump Host/Bastion (Best Security)

Set up a small jump host with a fixed IP that GitHub connects to, which then connects to your PULPHOST.

#### Architecture:
```
GitHub Actions → Jump Host (fixed IP) → PULPHOST (IP restricted)
```

#### Setup:

1. **Create a small VPS** (e.g., AWS EC2 t2.micro, DigitalOcean Droplet $6/mo)
   - Get a static IP
   - This will be your jump host

2. **Configure Jump Host:**
   ```bash
   # On jump host - enable SSH forwarding
   sudo nano /etc/ssh/sshd_config
   # Add: AllowTcpForwarding yes
   sudo systemctl restart sshd
   ```

3. **Whitelist Jump Host on PULPHOST:**
   ```bash
   # On PULPHOST
   sudo ufw allow from JUMP_HOST_IP to any port 22
   ```

4. **Update GitHub Action** to use ProxyJump:

   Create `.github/workflows/deploy-superset.yml`:
   ```yaml
   - name: Setup SSH with Jump Host
     run: |
       mkdir -p ~/.ssh
       echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
       chmod 600 ~/.ssh/id_rsa

       # SSH config for jump host
       cat >> ~/.ssh/config <<EOF
       Host jumphost
         HostName ${{ secrets.JUMP_HOST_IP }}
         User ${{ secrets.JUMP_USER }}
         IdentityFile ~/.ssh/id_rsa
         StrictHostKeyChecking no

       Host pulphost
         HostName ${{ secrets.PULPHOST }}
         User ${{ secrets.SSH_USER }}
         IdentityFile ~/.ssh/id_rsa
         ProxyJump jumphost
         StrictHostKeyChecking no
       EOF

   - name: Deploy via Jump Host
     run: |
       ssh pulphost "cd ~/superset-deployment && docker compose up -d"
   ```

   **Additional Secrets Needed:**
   - `JUMP_HOST_IP`: Your jump host's IP
   - `JUMP_USER`: Username on jump host

---

### Option 3: Self-Hosted Runner (Full Control)

Run your own GitHub Actions runner on your network with a known IP.

#### Benefits:
- Complete control over IP address
- Faster deployments (no file transfers needed)
- Free for private repos

#### Setup:

1. **On a machine in your network** (could be PULPHOST itself):
   ```bash
   # Create a directory for the runner
   mkdir actions-runner && cd actions-runner

   # Download the runner
   curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
     https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

   tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
   ```

2. **Configure the runner:**
   - Go to your GitHub repo → Settings → Actions → Runners
   - Click "New self-hosted runner"
   - Follow the configuration commands shown

3. **Update workflow** to use self-hosted runner:
   ```yaml
   jobs:
     build-and-deploy:
       runs-on: self-hosted  # Changed from ubuntu-latest
       steps:
         # ... rest of your workflow
   ```

4. **Whitelist your runner's IP** on PULPHOST:
   ```bash
   sudo ufw allow from RUNNER_IP to any port 22
   ```

---

### Option 4: Tailscale/WireGuard VPN (Modern Approach)

Use a VPN to create a secure tunnel without IP whitelisting.

#### With Tailscale (Easiest):

1. **Install on PULPHOST:**
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2. **Create Tailscale auth key:**
   - Go to https://login.tailscale.com/admin/settings/keys
   - Create a reusable auth key

3. **Use in GitHub Actions:**
   ```yaml
   - name: Connect to Tailscale
     uses: tailscale/github-action@v2
     with:
       authkey: ${{ secrets.TAILSCALE_AUTHKEY }}

   - name: Deploy via Tailscale
     run: |
       ssh ${{ secrets.SSH_USER }}@TAILSCALE_HOSTNAME ...
   ```

4. **No firewall changes needed!** - Tailscale creates encrypted peer-to-peer connections

---

### Option 5: Temporary Firewall Rule (Quick Test)

For testing, temporarily open SSH to all IPs, then restrict after confirming it works.

```bash
# On PULPHOST - temporarily allow all SSH
sudo ufw allow 22

# Test your GitHub Action

# Then restrict again with chosen solution above
```

---

## Comparison

| Solution | Security | Cost | Complexity | Recommended For |
|----------|----------|------|------------|-----------------|
| **GitHub IP Ranges** | Good | Free | Low | Small teams, budget-conscious |
| **Jump Host** | Excellent | ~$5-10/mo | Medium | Production, high security |
| **Self-Hosted Runner** | Excellent | Free* | Medium | Control needs, frequent deploys |
| **Tailscale VPN** | Excellent | Free** | Low | Modern approach, multiple servers |

\* Requires hardware/VM to run runner
\** Free tier: up to 100 devices, 3 users

---

## Recommended Approach

**For your situation, I recommend:**

1. **Short term:** Use GitHub IP Ranges (Option 1) - Quick to implement
2. **Long term:** Consider Tailscale (Option 4) - Best balance of security and simplicity

---

## Quick Implementation: GitHub IP Ranges

Run this on your PULPHOST right now:

```bash
# Install jq if needed
sudo apt-get update && sudo apt-get install -y jq

# Whitelist GitHub Actions IPs
curl -s https://api.github.com/meta | jq -r '.actions[]' | while read ip; do
  sudo ufw allow from $ip to any port 22 comment 'GitHub Actions'
done

# Verify
sudo ufw status | grep 'GitHub Actions' | wc -l
echo "Added GitHub Actions IP rules (should see ~20-30 ranges)"
```

---

## Verify Which IP GitHub Uses

To see which IP GitHub Actions is connecting from, add this step to your workflow:

```yaml
- name: Show GitHub Actions IP
  run: |
    echo "GitHub Actions is connecting from:"
    curl -s https://ifconfig.me
    echo ""
```

This will display in the Actions logs which IP was used for that run.

---

## Keeping IP Ranges Updated

GitHub's IP ranges change occasionally. To stay updated:

1. **Manual:** Run the update script monthly
2. **Automated:** Set up a cron job:
   ```bash
   # Add to crontab
   sudo crontab -e
   # Add line:
   0 0 1 * * /path/to/update-github-ips.sh
   ```
   This runs on the 1st of each month

3. **GitHub API Webhook:** Set up monitoring of GitHub's meta API changes (advanced)

---

## Need Help Deciding?

Answer these questions:

1. **How many servers do you manage?**
   - One: Use GitHub IP Ranges
   - Multiple: Use Tailscale

2. **How often do you deploy?**
   - Rarely: Use GitHub IP Ranges
   - Frequently: Self-hosted runner

3. **What's your budget?**
   - $0: GitHub IP Ranges or Self-hosted runner
   - $5-10/mo: Jump host or Tailscale (for teams)

4. **Security requirements?**
   - Standard: GitHub IP Ranges
   - High: Jump host or Self-hosted runner
