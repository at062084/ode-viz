# PULPHOST GitHub Actions Runner Diagnostics

The Docker build fails with `mkdir /home/docker: permission denied` BEFORE any Dockerfile commands execute. This indicates a Docker daemon or runner configuration issue on PULPHOST.

## Run These Commands on PULPHOST

SSH into PULPHOST and run these diagnostic commands:

### 1. Check GitHub Actions Runner User

```bash
# Who is running the GitHub Actions runner?
ps aux | grep actions-runner

# Check the docker user's home directory
getent passwd docker
# Expected output: docker:x:1000:1000::/home/docker:/bin/bash
#                                      ^^^^^^^^^^^^^ home directory

# Does /home/docker exist?
ls -ld /home/docker
# If it doesn't exist, this is the problem!

# Who owns /home directory?
ls -ld /home
```

### 2. Check Docker Daemon Configuration

```bash
# Check Docker daemon config
cat /etc/docker/daemon.json
# Look for: userns-remap, user-namespace-remap, storage-driver

# Check Docker info
docker info | grep -i "user\|namespace\|storage"

# What user does Docker run as?
ps aux | grep dockerd
```

### 3. Check Runner Working Directory Permissions

```bash
# Find the runner directory
find /opt -name "_work" 2>/dev/null
# OR
find /home -name "_work" 2>/dev/null

# Check permissions
ls -la /path/to/runner/_work/*/ode-viz/

# Check if docker user can write there
sudo -u docker touch /path/to/runner/_work/test.txt
```

### 4. Test Docker Build as Different User

```bash
# Try building as the runner user
cd /path/to/runner/_work/*/ode-viz/
docker build -t test:latest .

# Try building as root
sudo docker build -t test:latest .
```

### 5. Check BuildKit Configuration

```bash
# Is BuildKit enabled?
echo $DOCKER_BUILDKIT
docker buildx version

# Try disabling BuildKit temporarily
DOCKER_BUILDKIT=0 docker build -t test:latest .
```

---

## Likely Root Causes

### Issue 1: /home/docker Doesn't Exist

**Symptom:** User `docker` exists but `/home/docker` directory was never created.

**Fix:**
```bash
# Create home directory
sudo mkdir -p /home/docker
sudo chown docker:docker /home/docker

# Or fix the user's home directory setting
sudo usermod -d /home/docker docker
```

### Issue 2: Docker User Namespace Remapping

**Symptom:** Docker daemon configured with `userns-remap` causing permission conflicts.

**Check:**
```bash
cat /etc/docker/daemon.json | grep userns
```

**Fix:**
Either:
1. Disable user namespace remapping (less secure)
2. Configure proper subordinate UIDs/GIDs

### Issue 3: BuildKit Cache Directory Issue

**Symptom:** BuildKit trying to use `/home/docker/.docker/buildx` but can't create it.

**Fix:**
```bash
# Create BuildKit cache directory
sudo mkdir -p /home/docker/.docker
sudo chown -R docker:docker /home/docker/.docker

# OR disable BuildKit in GitHub Actions workflow
```

### Issue 4: Runner Working Directory Permissions

**Symptom:** Runner's `_work` directory has restrictive permissions.

**Fix:**
```bash
# Find runner work directory
RUNNER_WORK=$(find /opt /home -name "_work" 2>/dev/null | head -1)

# Fix permissions
sudo chown -R docker:docker $RUNNER_WORK
```

---

## Quick Fixes to Try

### Fix 1: Create Home Directory (Most Likely Solution)

```bash
# SSH to PULPHOST
ssh pulphost

# Create home directory for docker user
sudo mkdir -p /home/docker
sudo chown docker:docker /home/docker
sudo chmod 755 /home/docker

# Verify
ls -ld /home/docker
# Should show: drwxr-xr-x 2 docker docker ...
```

### Fix 2: Disable BuildKit in GitHub Actions

Add to `.github/workflows/deploy-superset.yml`:

```yaml
- name: Build Docker image
  env:
    DOCKER_BUILDKIT: 0  # Disable BuildKit
  run: |
    echo "🔨 Building Docker image..."
    docker build -t ${{ env.IMAGE_NAME }}:latest .
    echo "✅ Docker image built successfully"
```

### Fix 3: Run Docker Commands with sudo

Modify workflow to use sudo (if runner has sudo access):

```yaml
- name: Build Docker image
  run: |
    echo "🔨 Building Docker image..."
    sudo docker build -t ${{ env.IMAGE_NAME }}:latest .
    echo "✅ Docker image built successfully"
```

---

## What to Report Back

Please run the diagnostic commands above and share:

1. **Output of `getent passwd docker`** - Does docker user have /home/docker?
2. **Output of `ls -ld /home/docker`** - Does the directory exist?
3. **Output of `docker info | grep -i storage`** - What storage driver?
4. **Output of `cat /etc/docker/daemon.json`** - Any special config?
5. **Does `DOCKER_BUILDKIT=0 docker build` work?** - Is it a BuildKit issue?

---

## Most Likely Scenario

Based on the error, **I suspect:**

1. GitHub Actions runner installed as user `docker`
2. User `docker` was created without a home directory (`useradd --no-create-home docker`)
3. Docker build tries to access `$HOME` (which is `/home/docker`)
4. `/home/docker` doesn't exist
5. Docker tries to create it, but user `docker` doesn't have permission to create directories in `/home`

**Solution:** Create `/home/docker` directory with proper ownership.

---

## After Fixing

Once the issue is resolved on PULPHOST, the GitHub Actions workflow should work without any code changes!
