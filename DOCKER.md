# Docker Deployment Guide

This guide explains how to run Aztec List using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

## Quick Start

### 1. Configure Environment Variables

Create a `.env.docker` file from the example:

```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and set the required values:

- **`JWT__SECRET_KEY`** - Generate with: `uv run python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Update other values as needed for your environment

### 2. Build and Run

```bash
# Build and start all services
docker-compose --env-file .env.docker up --build

# Or run in detached mode (background)
docker-compose --env-file .env.docker up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Services

### Backend (FastAPI)

- **Container**: `aztec-list-backend`
- **Port**: 8000
- **Technology**: Python 3.13, FastAPI, SQLAlchemy
- **Volumes**:
  - `./backend/aztec_list.db` - SQLite database
  - `./backend/uploads` - User uploaded images

### Frontend (Next.js)

- **Container**: `aztec-list-frontend`
- **Port**: 3000
- **Technology**: Node.js 20, Next.js 16, React 19
- **Depends on**: Backend service

## Common Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Stop Services

```bash
# Stop services (keep containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers, and remove volumes
docker-compose down -v
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart backend only
docker-compose restart backend
```

### Execute Commands in Container

```bash
# Backend shell
docker-compose exec backend /bin/bash

# Run database migrations
docker-compose exec backend uv run alembic upgrade head

# Frontend shell
docker-compose exec frontend /bin/sh
```

## Database Management

### Run Migrations

```bash
# Apply all pending migrations
docker-compose exec backend uv run alembic upgrade head

# Create a new migration
docker-compose exec backend uv run alembic revision --autogenerate -m "description"
```

### Backup Database

```bash
# For SQLite (copy the database file)
docker cp aztec-list-backend:/app/aztec_list.db ./backup_$(date +%Y%m%d).db
```

## Production Deployment

### Environment Variables

For production, update these settings in your `.env.docker`:

1. **Generate a secure JWT secret key**:

   ```bash
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update CORS origins** to your production domain:

   ```
   CORS__ALLOWED_ORIGINS='["https://yourdomain.com"]'
   ```

3. **Consider using PostgreSQL** instead of SQLite:

   ```
   DB__DATABASE_URL="postgresql://user:password@postgres:5432/aztec_list"
   ```

4. **Set frontend API URL** to your backend domain:

   ```
   NEXT_PUBLIC_API_URL="https://api.yourdomain.com"
   ```

5. **Configure email service** (optional):
   ```
   EMAIL__RESEND_API_KEY="your-resend-api-key"
   EMAIL__FROM_EMAIL="noreply@yourdomain.com"
   ```

### Using PostgreSQL

To use PostgreSQL instead of SQLite, add this to your `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: aztec-list-postgres
    environment:
      - POSTGRES_USER=azteclist
      - POSTGRES_PASSWORD=changeme
      - POSTGRES_DB=aztec_list
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - aztec-list-network
    restart: unless-stopped

  backend:
    # ... existing backend config ...
    environment:
      - DB__DATABASE_URL=postgresql://azteclist:changeme@postgres:5432/aztec_list
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### HTTPS / Reverse Proxy

For production, use a reverse proxy like nginx or Traefik to handle HTTPS:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - aztec-list-network
```

## Troubleshooting

### Port Already in Use

If ports 3000 or 8000 are already in use, change them in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000" # Change host port (left side)
  frontend:
    ports:
      - "3001:3000" # Change host port (left side)
```

### Build Errors

Clear Docker cache and rebuild:

```bash
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up
```

### Container Won't Start

Check logs for errors:

```bash
docker-compose logs backend
docker-compose logs frontend
```

### Database Connection Issues

1. Ensure the database file has correct permissions
2. Check the `DB__DATABASE_URL` environment variable
3. Verify the volume mount in `docker-compose.yml`

### Frontend Can't Connect to Backend

1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Check CORS settings in backend `.env`
3. Ensure backend container is running: `docker-compose ps`

## Development vs Production

### Development Setup

- Use SQLite database
- Enable hot reload (mount source code as volumes)
- Use localhost URLs
- Enable debug logging

### Production Setup

- Use PostgreSQL database
- Don't mount source code (baked into image)
- Use production domain URLs
- Use INFO or WARNING log level
- Enable HTTPS with reverse proxy
- Use secure secret keys
- Set up backups

## Health Checks

Add health checks to `docker-compose.yml`:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Next.js Docker Deployment](https://nextjs.org/docs/deployment#docker-image)
