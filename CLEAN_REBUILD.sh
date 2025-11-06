# Clean Rebuild Script

Run these commands to force a complete rebuild without cache:

```bash
# Stop and remove everything
docker compose down -v

# Remove the old image
docker rmi superset-app:latest 2>/dev/null || true
docker rmi ode-viz-superset 2>/dev/null || true

# Clean build cache
docker builder prune -f

# Rebuild from scratch (no cache)
docker compose build --no-cache

# Start
docker compose up -d

# Watch logs
docker compose logs -f superset
```

This ensures Docker doesn't use any cached layers from previous builds.
