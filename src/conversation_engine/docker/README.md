# Conversation Engine Docker Deployment

This directory contains Docker deployment configuration for the Riker Conversation Engine.

## Architecture

The deployment consists of three main services:

- **Redis**: Message bus and memory storage
- **Backend**: FastAPI application with WebSocket support
- **Frontend**: React application served by Nginx

## Prerequisites

1. **Docker**: Version 20.10 or later
2. **Docker Compose**: Version 2.0 or later
3. **Anthropic API Key**: Required for LLM functionality

```bash
# Check Docker installation
docker --version
docker-compose --version

# Set API key
export ANTHROPIC_API_KEY=your_api_key_here
```

## Quick Start

### 1. Deploy Everything

```bash
cd src/conversation_engine/docker
./deploy.sh
```

This will:
- Build all Docker images
- Start all services
- Run health checks
- Validate the deployment

### 2. Access Services

Once deployed, services are available at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Manual Deployment

### 1. Build and Start Services

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Validate Deployment

```bash
# Quick validation
python3 validate_deployment.py --quick

# Full validation (includes conversation flow tests)
python3 validate_deployment.py
```

## Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis
```

### Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down --volumes
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

## Troubleshooting

### Common Issues

#### 1. Port Conflicts

If ports 3000, 8000, or 6379 are already in use:

```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8000
lsof -i :6379

# Stop conflicting services or modify docker-compose.yml
```

#### 2. Build Failures

```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 3. Health Check Failures

```bash
# Check service logs
docker-compose logs backend

# Verify Redis connectivity
docker-compose exec redis redis-cli ping

# Test backend directly
curl http://localhost:8000/health
```

#### 4. Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Verify Nginx configuration
docker-compose exec frontend nginx -t

# Test frontend directly
curl http://localhost:3000
```

### Debug Mode

Enable debug logging for the backend:

```bash
# Edit docker-compose.yml
environment:
  - CONVERSATION_ENGINE_DEBUG=true
  - CONVERSATION_ENGINE_LOG_LEVEL=DEBUG

# Restart services
docker-compose restart backend
```

## Configuration

### Environment Variables

The deployment supports these environment variables:

#### Backend Configuration

- `ANTHROPIC_API_KEY`: Required for LLM functionality
- `REDIS_URL`: Redis connection URL (default: redis://redis:6379)
- `CONVERSATION_ENGINE_DEBUG`: Enable debug mode (default: false)
- `CONVERSATION_ENGINE_LOG_LEVEL`: Log level (default: INFO)

#### Frontend Configuration

- `REACT_APP_BACKEND_URL`: Backend URL for API calls (default: http://localhost:8000)

### Volume Mounts

- `redis_data`: Persistent Redis data
- `../src/plugins`: Plugin directory (development mode)

## Production Deployment

For production deployment, consider these modifications:

### 1. Security

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - CONVERSATION_ENGINE_DEBUG=false
      - CONVERSATION_ENGINE_LOG_LEVEL=WARNING
    # Remove plugin volume mount
    # volumes: []
```

### 2. Load Balancing

Use a reverse proxy like Nginx or Traefik:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### 3. Monitoring

Add monitoring services:

```yaml
services:
  prometheus:
    image: prom/prometheus
    # ... configuration
  
  grafana:
    image: grafana/grafana
    # ... configuration
```

## Development Mode

For development with hot reloading:

```yaml
# docker-compose.dev.yml
services:
  backend:
    volumes:
      - ../backend:/app
    environment:
      - CONVERSATION_ENGINE_DEBUG=true
  
  frontend:
    command: npm start
    volumes:
      - ../frontend:/app
    ports:
      - "3000:3000"
```

```bash
# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Testing

### Automated Testing

```bash
# Run deployment validation
./deploy.sh validate

# Run backend tests
docker-compose exec backend python -m pytest

# Run frontend tests
docker-compose exec frontend npm test
```

### Manual Testing

1. **WebSocket Connection**: Use browser dev tools to test WebSocket at `ws://localhost:8000/ws`
2. **API Endpoints**: Use curl or Postman to test REST endpoints
3. **Frontend Functionality**: Test UI components and dashboard features

## Monitoring and Logs

### Health Monitoring

All services include health checks:

```bash
# Check health status
docker-compose ps

# Manual health checks
curl http://localhost:8000/health
curl http://localhost:3000/health
```

### Log Aggregation

For centralized logging:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Backup and Recovery

### Redis Data Backup

```bash
# Create backup
docker-compose exec redis redis-cli BGSAVE

# Copy backup file
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/

# Restore from backup
docker cp ./backup/dump.rdb $(docker-compose ps -q redis):/data/
docker-compose restart redis
```

### Configuration Backup

```bash
# Backup all configuration
tar -czf conversation-engine-backup.tar.gz \
  docker-compose.yml \
  Dockerfile.* \
  nginx.conf \
  ../backend/requirements.txt
```

## Support

For issues with deployment:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs`
3. Run validation: `python3 validate_deployment.py`
4. Check the main project documentation

## Scripts Reference

- `deploy.sh`: Main deployment orchestration script
- `validate_deployment.py`: Comprehensive deployment validation
- `docker-compose.yml`: Main service configuration
- `Dockerfile.backend`: Backend container configuration
- `Dockerfile.frontend`: Frontend container configuration
- `nginx.conf`: Nginx configuration for frontend