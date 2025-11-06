# Quick Start: GitHub Actions Deployment

## What You Need

| Item | What It Is | Where to Get It | Where It Goes |
|------|-----------|----------------|---------------|
| **PULPHOST** | Your server's IP or domain | Your hosting provider | GitHub Secret |
| **SSH_USER** | Username on your server | Usually `ubuntu`, `root`, or custom | GitHub Secret |
| **SSH_PRIVATE_KEY** | SSH private key for authentication | Generate with `ssh-keygen` | GitHub Secret |

## 5-Minute Setup

### On Your Local Machine

```bash
# 1. Generate SSH key pair
ssh-keygen -t ed25519 -f ~/.ssh/github-actions-deploy

# 2. Copy the private key (for GitHub)
cat ~/.ssh/github-actions-deploy
# Copy the entire output

# 3. Copy the public key (for your server)
cat ~/.ssh/github-actions-deploy.pub
# Copy this output too
```

### On Your Server (PULPHOST)

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 3. Add the public key you copied earlier
mkdir -p ~/.ssh
echo "PASTE_YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 4. Create environment file
mkdir -p ~/superset-deployment
cd ~/superset-deployment
nano .env
```

Paste this into `.env` (update the values):
```env
POSTGRES_DB=superset
POSTGRES_USER=superset
POSTGRES_PASSWORD=change-this-password
SUPERSET_SECRET_KEY=change-this-secret-key
```

Save (Ctrl+O, Enter, Ctrl+X).

### On GitHub

1. Go to your repo: `https://github.com/at062084/ode-viz`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** three times to add:

   | Name | Value |
   |------|-------|
   | `SSH_PRIVATE_KEY` | Paste the private key from step 2 above |
   | `SSH_USER` | Your server username (e.g., `ubuntu`) |
   | `PULPHOST` | Your server IP (e.g., `123.45.67.89`) |

### Deploy

1. Go to **Actions** tab in GitHub
2. Click **Build and Deploy Apache Superset**
3. Click **Run workflow** → **Run workflow**
4. Wait 3-5 minutes
5. Visit: `http://YOUR_SERVER_IP:8088`

Default login:
- Username: `admin`
- Password: `admin`

**Change the password immediately!**

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 GitHub Actions                   │
│  (Builds Docker image & runs deployment)         │
└──────────────────┬──────────────────────────────┘
                   │ SSH Connection
                   │ (using secrets)
                   ▼
┌─────────────────────────────────────────────────┐
│           Your Server (PULPHOST)                 │
│                                                   │
│  ~/superset-deployment/                          │
│  ├── docker-compose.yml                          │
│  ├── .env                                        │
│  └── Docker containers:                          │
│      ├── Superset (port 8088)                    │
│      ├── PostgreSQL (port 5432)                  │
│      └── Redis (port 6379)                       │
└─────────────────────────────────────────────────┘
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Permission denied (publickey)" | Check that public key is in server's `~/.ssh/authorized_keys` |
| "Docker daemon socket error" | Run `sudo usermod -aG docker $USER` then log out/in |
| "Port already allocated" | Run `docker compose down` on server |
| Can't access Superset | Check firewall: `sudo ufw allow 8088` |
| **SSH blocked by IP firewall** | **See [GITHUB_ACTIONS_FIREWALL.md](GITHUB_ACTIONS_FIREWALL.md)** |

## Need More Details?

See the complete guide: [DEPLOYMENT_SETUP.md](DEPLOYMENT_SETUP.md)

## Example Values

Here's what your GitHub Secrets might look like:

**SSH_PRIVATE_KEY:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
... (many more lines) ...
-----END OPENSSH PRIVATE KEY-----
```

**SSH_USER:**
```
ubuntu
```

**PULPHOST:**
```
123.45.67.89
```
or
```
superset.mycompany.com
```
