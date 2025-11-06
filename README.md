# Apache Superset Docker Setup

A Docker-based deployment of Apache Superset with PostgreSQL and Redis.

## Features

- Apache Superset latest version
- PostgreSQL 14 as metadata database
- Redis for caching and Celery message broker
- Health checks for all services
- Persistent volumes for data
- Configurable via environment variables

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

## Quick Start

1. Clone this repository and navigate to the directory:
```bash
cd ode-viz
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit `.env` and update the configuration (especially `SUPERSET_SECRET_KEY` for production):
```bash
nano .env
```

4. Build and start the services:
```bash
docker-compose up -d
```

5. Wait for services to be healthy (check with `docker-compose ps`)

6. Access Superset at `http://localhost:8088`

Default credentials:
- Username: `admin`
- Password: `admin`

**Important:** Change the default admin password immediately after first login!

## Configuration

### Environment Variables

Edit the `.env` file to customize:

- `POSTGRES_DB`: PostgreSQL database name (default: superset)
- `POSTGRES_USER`: PostgreSQL username (default: superset)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: superset)
- `SUPERSET_SECRET_KEY`: Secret key for Superset (change for production!)
- `MAPBOX_API_KEY`: Optional Mapbox API key for map visualizations

### Advanced Configuration

For advanced Superset configuration, edit `superset_config.py`:

- Database connections
- Cache settings
- Feature flags
- Security settings
- And more

## Services

The stack includes three services:

1. **superset** - Apache Superset application (port 8088)
2. **postgres** - PostgreSQL database (port 5432)
3. **redis** - Redis cache (port 6379)

## Common Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f superset
```

### Restart Superset
```bash
docker-compose restart superset
```

### Access Superset shell
```bash
docker-compose exec superset superset shell
```

### Create additional admin user
```bash
docker-compose exec superset superset fab create-admin \
  --username <username> \
  --firstname <First> \
  --lastname <Last> \
  --email <email@example.com> \
  --password <password>
```

### Database migrations
```bash
docker-compose exec superset superset db upgrade
```

### Initialize Superset (roles and permissions)
```bash
docker-compose exec superset superset init
```

## Data Persistence

Data is persisted in Docker volumes:

- `postgres-data`: PostgreSQL database files
- `redis-data`: Redis data files
- `superset-data`: Superset application data

To remove all data and start fresh:
```bash
docker-compose down -v
```

## Production Deployment

For production use:

1. **Change default credentials**: Update admin password and database credentials
2. **Set strong secret key**: Generate a strong `SUPERSET_SECRET_KEY`
3. **Use HTTPS**: Set up a reverse proxy (nginx/traefik) with SSL
4. **Configure backup**: Set up regular backups of PostgreSQL data
5. **Resource limits**: Add resource limits in docker-compose.yml
6. **Security**: Review and harden `superset_config.py` settings
7. **Monitoring**: Add monitoring and alerting

### Generate Secret Key

```bash
openssl rand -base64 42
```

## Troubleshooting

### Service won't start
Check logs:
```bash
docker-compose logs superset
```

### Database connection issues
Ensure PostgreSQL is healthy:
```bash
docker-compose ps postgres
```

### Clear cache
```bash
docker-compose exec redis redis-cli FLUSHALL
```

### Reset everything
```bash
docker-compose down -v
docker-compose up -d
```

## Architecture

```
┌─────────────────┐
│   Superset UI   │ :8088
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Redis │  │Postgres│
│:6379 │  │ :5432  │
└──────┘  └────────┘
```

## Ports

- 8088: Superset web interface
- 5432: PostgreSQL (accessible from host)
- 6379: Redis (accessible from host)

## Support

For issues and questions:
- Apache Superset Documentation: https://superset.apache.org/docs/intro
- GitHub Issues: https://github.com/apache/superset/issues

## License

This Docker setup is provided as-is. Apache Superset is licensed under the Apache License 2.0.
