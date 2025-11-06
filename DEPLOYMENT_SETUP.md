# GitHub Actions Deployment Setup Guide

This guide will walk you through setting up GitHub Actions to deploy Apache Superset to your server (PULPHOST).

## Overview

GitHub Actions needs to:
1. Connect to your server via SSH
2. Transfer files
3. Run Docker commands

To do this securely, we use **GitHub Secrets** (encrypted variables that store sensitive information like passwords and SSH keys).

## Step 1: Prepare Your Deployment Server (PULPHOST)

### 1.1 Install Required Software

SSH into your server and install Docker:

```bash
# Update package list
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Log out and back in for group changes to take effect
# Then verify installation
docker --version
docker compose version
```

### 1.2 Create SSH Key for GitHub Actions

On your **local machine** (not the server), generate a dedicated SSH key pair:

```bash
# Generate SSH key (press Enter for default location, no passphrase)
ssh-keygen -t ed25519 -f ~/.ssh/github-actions-deploy -C "github-actions-deploy"
```

This creates two files:
- `~/.ssh/github-actions-deploy` (private key - keep this secret!)
- `~/.ssh/github-actions-deploy.pub` (public key - safe to share)

### 1.3 Add Public Key to Your Server

Copy the public key to your server:

```bash
# View the public key
cat ~/.ssh/github-actions-deploy.pub

# Copy the output, then SSH to your server
ssh your-username@your-server-address

# Add the public key to authorized_keys
mkdir -p ~/.ssh
echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### 1.4 Test SSH Connection

Test that the key works:

```bash
ssh -i ~/.ssh/github-actions-deploy your-username@your-server-address
```

If this works, you're ready to proceed!

## Step 2: Add Secrets to GitHub

### 2.1 Navigate to Repository Settings

1. Go to your GitHub repository: `https://github.com/at062084/ode-viz`
2. Click on **Settings** (top navigation bar)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 2.2 Add SSH_PRIVATE_KEY

1. Click **New repository secret**
2. Name: `SSH_PRIVATE_KEY`
3. Value: Copy your private key
   ```bash
   cat ~/.ssh/github-actions-deploy
   ```
   Copy the entire output including:
   ```
   -----BEGIN OPENSSH PRIVATE KEY-----
   ... (key content) ...
   -----END OPENSSH PRIVATE KEY-----
   ```
4. Click **Add secret**

### 2.3 Add SSH_USER

1. Click **New repository secret**
2. Name: `SSH_USER`
3. Value: Your username on the server (e.g., `ubuntu`, `root`, `deploy`, etc.)
4. Click **Add secret**

### 2.4 Add PULPHOST

1. Click **New repository secret**
2. Name: `PULPHOST`
3. Value: Your server's hostname or IP address
   - Examples: `123.456.789.012` or `superset.yourdomain.com`
4. Click **Add secret**

### 2.5 Verify Secrets

You should now see three secrets listed:
- `SSH_PRIVATE_KEY`
- `SSH_USER`
- `PULPHOST`

Note: Once added, you can't view secret values again (for security), but you can update them.

## Step 3: Configure Environment Variables on Server

SSH to your server and create the environment file:

```bash
# Create deployment directory
mkdir -p ~/superset-deployment
cd ~/superset-deployment

# Create .env file
nano .env
```

Add this content (update the values as needed):

```env
# PostgreSQL Configuration
POSTGRES_DB=superset
POSTGRES_USER=superset
POSTGRES_PASSWORD=your-secure-password-here

# Superset Configuration - IMPORTANT: Change this!
SUPERSET_SECRET_KEY=your-secure-secret-key-here

# Optional: Mapbox API Key
MAPBOX_API_KEY=
```

**Generate a secure secret key:**
```bash
openssl rand -base64 42
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

## Step 4: Test the Deployment

### 4.1 Manual Trigger

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Build and Deploy Apache Superset** workflow (left sidebar)
4. Click **Run workflow** button (right side)
5. Select your branch (e.g., `claude/github-action-superset-build-011CUruagQwpnbseTBYBssqM`)
6. Click **Run workflow**

### 4.2 Monitor the Workflow

1. Click on the running workflow to see logs
2. Watch each step execute
3. If any step fails, check the error message

### 4.3 Verify Deployment on Server

SSH to your server and check:

```bash
cd ~/superset-deployment
docker compose ps
```

You should see three containers running:
- superset-app
- superset-postgres
- superset-redis

Access Superset at: `http://YOUR_SERVER_IP:8088`

## Troubleshooting

### SSH Connection Fails

**Error:** `Permission denied (publickey)`

**Solution:**
1. Verify the private key is correctly added to GitHub Secrets
2. Verify the public key is in `~/.ssh/authorized_keys` on the server
3. Check SSH user is correct
4. Test manually: `ssh -i ~/.ssh/github-actions-deploy user@host`

### Docker Command Fails

**Error:** `permission denied while trying to connect to the Docker daemon socket`

**Solution:**
```bash
# On the server, add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Port Already in Use

**Error:** `port is already allocated`

**Solution:**
```bash
# On the server, stop conflicting services
docker compose down
# Or change ports in docker-compose.yml
```

### Workflow Can't Find Files

**Error:** `No such file or directory`

**Solution:**
- Ensure you're running the workflow from the correct branch
- Check that all required files are committed to the repository

## Security Best Practices

1. **Never commit secrets** to your repository
   - `.env` is in `.gitignore` - keep it that way!

2. **Use strong passwords**
   - Generate: `openssl rand -base64 32`

3. **Restrict SSH key permissions**
   - Private key: `chmod 600`
   - Use a dedicated key just for deployments

4. **Use firewall on server**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 22    # SSH
   sudo ufw allow 8088  # Superset
   sudo ufw enable
   ```

5. **Regular updates**
   ```bash
   # Keep server updated
   sudo apt-get update && sudo apt-get upgrade
   ```

## What Happens During Deployment

Here's what the GitHub Action does:

1. **Checkout code** - Downloads your repository
2. **Build Docker image** - Creates the Superset container image
3. **Setup SSH** - Configures SSH connection to your server
4. **Create deployment directory** - Makes `~/superset-deployment` on server
5. **Copy files** - Transfers Docker image and configuration files
6. **Load image** - Imports the Docker image on the server
7. **Deploy** - Runs `docker compose up -d` to start services
8. **Verify** - Checks that containers are running

## Next Steps

After successful deployment:

1. **Access Superset**
   - URL: `http://YOUR_SERVER_IP:8088`
   - Username: `admin`
   - Password: `admin`

2. **Change admin password immediately!**

3. **Set up HTTPS** (recommended for production)
   - Use nginx or Caddy as reverse proxy
   - Get SSL certificate from Let's Encrypt

4. **Set up backups**
   - Backup PostgreSQL data regularly
   - Backup Superset configuration

## Need Help?

If you encounter issues:
1. Check the GitHub Actions logs (Actions tab → Click on workflow run)
2. Check server logs: `docker compose logs -f`
3. Check this repository's Issues tab
4. Review the main README.md for additional troubleshooting

## Summary Checklist

- [ ] Docker installed on server
- [ ] SSH key pair generated
- [ ] Public key added to server's `~/.ssh/authorized_keys`
- [ ] SSH connection tested manually
- [ ] Three GitHub Secrets added (SSH_PRIVATE_KEY, SSH_USER, PULPHOST)
- [ ] `.env` file created on server with secure values
- [ ] GitHub Action workflow triggered
- [ ] Deployment successful
- [ ] Superset accessible at server URL
- [ ] Admin password changed
