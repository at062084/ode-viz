# Quick Start - Running on WSL

## Prerequisites Check

```bash
# Check Docker is running
docker ps

# Check Docker Compose
docker compose version

# Check you're in the repo
pwd
# Should show: /home/user/ode-viz (or your path)
```

## 🚀 Get It Running (3 Commands)

```bash
# 1. Make sure .env exists
cp .env.example .env

# 2. Build and start everything
docker compose up -d --build

# 3. Check status
docker compose ps
```

That's it!

## ✅ Verify It's Working

```bash
# Check all containers are running
docker compose ps

# Should show:
# - superset-app (healthy)
# - superset-postgres (healthy)
# - superset-redis (healthy)

# Watch logs
docker compose logs -f superset
```

## 🌐 Access Superset

Open in browser: **http://localhost:8088**

**Login:**
- Username: `admin`
- Password: `admin`

**⚠️ Change password immediately after first login!**

## 🔧 Troubleshooting

### Port conflicts?

```bash
# Check what's using ports
netstat -ano | grep -E "8088|6543|6379"

# Or on WSL
ss -tlnp | grep -E "8088|6543|6379"
```

### Container won't start?

```bash
# View logs
docker compose logs superset
docker compose logs postgres
docker compose logs redis

# Rebuild from scratch
docker compose down -v
docker compose up -d --build
```

### Permission issues on WSL?

```bash
# Fix ownership if needed
sudo chown -R $USER:$USER .
```

## 🛑 Stop Everything

```bash
docker compose down

# Or to remove volumes too (fresh start)
docker compose down -v
```

## 📊 Quick Health Check

```bash
# One-liner to check everything
echo "Services:" && docker compose ps && \
echo -e "\nSuperset health:" && curl -s http://localhost:8088/health && \
echo -e "\nPostgreSQL:" && docker compose exec postgres pg_isready -U superset && \
echo -e "\nRedis:" && docker compose exec redis redis-cli ping
```

## WSL-Specific Notes

✅ **Works on WSL2** - Docker Desktop integrates perfectly
✅ **No special configuration needed** - Standard Docker commands work
✅ **File permissions** - Usually fine, but fix with `chown` if needed
✅ **Port access** - Access from Windows browser at `http://localhost:8088`

## Next Steps

After it's running:
1. Change admin password
2. Add your data sources
3. Create dashboards

Need help? Check the main [README.md](README.md)
