# Docker Quick Reference - Aztec List

## Start Services

```bash
# First time setup
cp .env.docker.example .env.docker
# Edit .env.docker and set JWT__SECRET_KEY

# Build and start
docker-compose --env-file .env.docker up --build -d

# Check status
docker-compose ps
```

## Access URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Run migrations
docker-compose exec backend uv run alembic upgrade head

# Backend shell
docker-compose exec backend /bin/bash

# Rebuild after code changes
docker-compose up --build
```

## Troubleshooting

```bash
# Check if containers are running
docker-compose ps

# View backend logs
docker-compose logs backend

# View frontend logs
docker-compose logs frontend

# Clean rebuild
docker-compose down
docker system prune -a
docker-compose up --build
```

See [DOCKER.md](./DOCKER.md) for detailed documentation.
