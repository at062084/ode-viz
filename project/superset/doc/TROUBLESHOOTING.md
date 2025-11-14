# Troubleshooting Superset Connection

Run these commands in your WSL terminal to diagnose the issue:

## 1. Check Container Status

```bash
docker compose ps
```

Look for the `superset-app` container. What does the STATUS column say?
- `healthy` = Good!
- `starting` = Still initializing, wait a bit
- `unhealthy` = There's a problem

## 2. Check Superset Logs

```bash
docker compose logs superset
```

Look for:
- ✅ `"Running on http://0.0.0.0:8088"` = Superset is ready
- ❌ Errors or stack traces = There's a problem

## 3. Check if Port is Listening

```bash
# Check if something is listening on port 8088
netstat -tlnp | grep 8088

# Or use ss
ss -tlnp | grep 8088
```

Should show something listening on `0.0.0.0:8088` or `:::8088`

## 4. Test Connection from Inside WSL

```bash
# Try curl from WSL
curl http://localhost:8088/health

# Should return: {"health": "ok"} or similar
```

## 5. Check Port Mapping

```bash
docker compose ps superset
```

Look at the PORTS column. Should show: `0.0.0.0:8088->8088/tcp`

## Common Issues & Solutions

### Issue 1: Superset is Still Starting

**Symptom:** Container status is `starting` or logs show initialization

**Solution:** Wait 1-2 minutes. Superset takes time to:
- Upgrade database schema
- Create admin user
- Initialize roles and permissions

Watch logs:
```bash
docker compose logs -f superset
```

When you see `"Running on http://0.0.0.0:8088"`, it's ready!

### Issue 2: Database Connection Failed

**Symptom:** Logs show PostgreSQL connection errors

**Solution:**
```bash
# Check if PostgreSQL is healthy
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Restart everything
docker compose down
docker compose up -d
```

### Issue 3: Port Conflict

**Symptom:** Error about port already in use

**Solution:**
```bash
# Check what's using port 8088
sudo netstat -tlnp | grep 8088

# Or change the port in docker-compose.yml
# Change: "8088:8088" to "8089:8088"
# Then access at http://localhost:8089
```

### Issue 4: Container Keeps Restarting

**Symptom:** `docker compose ps` shows container restarting

**Solution:**
```bash
# Check logs for errors
docker compose logs superset --tail 100

# Common fix: Remove volumes and start fresh
docker compose down -v
docker compose up -d
```

### Issue 5: WSL Networking Issue

**Symptom:** Curl works in WSL, but browser can't connect

**Solution:**

Try accessing from Windows browser using WSL IP:
```bash
# In WSL, get your IP
ip addr show eth0 | grep inet

# Access from Windows browser:
# http://<WSL_IP>:8088
```

Or use Windows localhost (should work with WSL2):
- http://localhost:8088

### Issue 6: Firewall Blocking

**Symptom:** Everything looks good but can't connect

**Solution:**
```bash
# Allow port 8088 (if firewall is enabled)
sudo ufw allow 8088

# Or disable firewall temporarily to test
sudo ufw disable
```

## Quick Health Check Script

Run this all at once:

```bash
echo "=== Container Status ==="
docker compose ps

echo -e "\n=== Port Listening ==="
ss -tlnp | grep 8088

echo -e "\n=== Superset Health ==="
curl -s http://localhost:8088/health || echo "Not responding"

echo -e "\n=== Recent Logs ==="
docker compose logs --tail 20 superset
```

## Expected Startup Sequence

When starting, Superset goes through these steps:

1. **Container starts** (STATUS: starting)
2. **Database upgrade** (logs show migrations)
3. **Create admin user** (logs show admin creation)
4. **Initialize Superset** (logs show init)
5. **Start web server** (logs show "Running on http://0.0.0.0:8088")
6. **Health check passes** (STATUS: healthy)

This can take **1-3 minutes** on first startup.

## Still Not Working?

Share the output of:
```bash
docker compose ps
docker compose logs superset --tail 50
```

And I'll help diagnose!
