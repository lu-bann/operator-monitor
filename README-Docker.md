# Docker Deployment Guide

This guide covers deploying the Ethereum Operator Monitor stack using Docker and Docker Compose.

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose v2
- At least 2GB RAM and 10GB disk space
- Access to Ethereum RPC endpoint

### 1. Clone and Configure
```bash
git clone <repository-url>
cd luban/monitor

# Copy environment template
cp .env.example .env

# Edit configuration (required)
nano .env
```

### 2. Start Services
```bash
# Start all services in background
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Verify Deployment
```bash
# Check API health
curl http://localhost:8000/health

# View interactive documentation
open http://localhost:8000/docs
```

## 📊 Service Architecture

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| **operator-status-api** | 8000 | REST API Server | Redis, PostgreSQL |
| **operator-monitor** | - | Blockchain Monitor | Redis |
| **redis** | 6379 | Caching & Storage | - |
| **postgres** | 5432 | Validator Data | - |

## ⚙️ Configuration

### Environment Variables

#### Required (for operator monitoring)
```bash
NETWORK=holesky
RPC_URL=https://ethereum-holesky.publicnode.com
REGISTRY_CONTRACT_ADDRESS=0x...
```

#### Optional Contract Addresses
```bash
TAIYI_COORDINATOR_CONTRACT_ADDRESS=0x...
TAIYI_ESCROW_CONTRACT_ADDRESS=0x...
EIGENLAYER_MIDDLEWARE_CONTRACT_ADDRESS=0x...
```

#### Database Configuration (pre-configured)
```bash
REDIS_URL=redis://redis:6379
POSTGRES_HOST=postgres
POSTGRES_DB=helix_mev_relayer
```

### Volume Mounts
- `redis_data`: Redis persistence
- `postgres_data`: PostgreSQL data
- `./logs`: Application logs

## 🔧 Operations

### Service Management
```bash
# View logs
docker-compose logs -f operator-status-api
docker-compose logs -f operator-monitor

# Restart specific service
docker-compose restart operator-status-api

# Scale services (API only)
docker-compose up -d --scale operator-status-api=3

# Stop all services
docker-compose down

# Stop and remove data (⚠️ destroys data)
docker-compose down -v
```

### Health Monitoring
```bash
# Check all service health
docker-compose ps

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/validator-delegation/0x8a1d...

# Monitor resource usage
docker stats
```

### Data Management
```bash
# Backup PostgreSQL
docker exec operator-monitor-postgres pg_dump -U postgres helix_mev_relayer > backup.sql

# Backup Redis
docker exec operator-monitor-redis redis-cli BGSAVE
docker cp operator-monitor-redis:/data/dump.rdb ./redis-backup.rdb

# Restore PostgreSQL
cat backup.sql | docker exec -i operator-monitor-postgres psql -U postgres -d helix_mev_relayer
```

## 🧪 Development

### Local Development with Docker
```bash
# Build development image
docker build -t operator-monitor:dev .

# Run with hot reload (mount source code)
docker run -p 8000:8000 -v $(pwd):/app operator-monitor:dev \
  python operator_status/start_server.py start --reload

# Run tests in container
docker run --rm operator-monitor:dev pytest
```

### Custom Builds
```bash
# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.11 -t operator-monitor:py311 .

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 -t operator-monitor:latest .
```

## 🔍 Troubleshooting

### Common Issues

#### Services won't start
```bash
# Check Docker daemon
docker version

# Check available resources
docker system df
docker system prune  # Clean up if needed

# View detailed service logs
docker-compose logs operator-status-api
```

#### Redis connection errors
```bash
# Check Redis connectivity
docker exec operator-monitor-redis redis-cli ping

# Verify network connectivity
docker network ls
docker network inspect operator-monitor-network
```

#### PostgreSQL connection errors
```bash
# Check database status
docker exec operator-monitor-postgres pg_isready -U postgres

# Connect to database
docker exec -it operator-monitor-postgres psql -U postgres -d helix_mev_relayer

# Check table structure
\dt
SELECT * FROM validators LIMIT 5;
```

#### API not responding
```bash
# Check if container is running
docker ps | grep operator-status-api

# Check application logs
docker logs operator-status-api

# Test internal connectivity
docker exec operator-status-api curl localhost:8000/health
```

### Performance Tuning

#### Redis Optimization
```yaml
# In docker-compose.yml, add Redis configuration
redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

#### PostgreSQL Optimization
```yaml
# Add PostgreSQL performance settings
postgres:
  environment:
    POSTGRES_SHARED_PRELOAD_LIBRARIES: pg_stat_statements
  command: postgres -c shared_preload_libraries=pg_stat_statements -c max_connections=200
```

#### Application Scaling
```bash
# Run multiple API instances behind load balancer
docker-compose up -d --scale operator-status-api=3

# Use nginx for load balancing
# (requires additional nginx configuration)
```

## 🔒 Security

### Production Deployment
```bash
# Use environment-specific configuration
cp .env.example .env.production

# Set secure passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Run with read-only filesystem
docker run --read-only --tmpfs /tmp operator-monitor
```

### Network Security
```yaml
# Restrict external access in docker-compose.yml
postgres:
  ports: []  # Remove external port exposure
redis:
  ports: []  # Remove external port exposure
```

## 📈 Monitoring

### Metrics Collection
```bash
# Enable Docker metrics
echo '{"metrics-addr": "127.0.0.1:9323", "experimental": true}' > /etc/docker/daemon.json

# Monitor container metrics
curl http://localhost:9323/metrics
```

### Log Aggregation
```yaml
# Add logging configuration to docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "100m"
    max-file: "5"
```

## 📚 API Usage Examples

### Validator Delegation Status
```bash
# Check single validator
curl http://localhost:8000/validator-delegation/0x8a1d7b8dd64e0aafe7ea7b6c95065c9364cf99d38470db679bdf5c9bed34755c947c6c3cdb2f4a66dd4d31aae7e23d7a

# Batch check validators
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"validator_keys": ["0x8a1d...", "0x9b2e..."]}'
```

### Operator Validator Mappings
```bash
# Get validators for operator
curl http://localhost:8000/operator/0x1234567890abcdef1234567890abcdef12345678

# List all validators with delegations
curl http://localhost:8000/list-validators
```

### Health and Status
```bash
# System health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/  # API info
open http://localhost:8000/docs  # Swagger UI
```

For more detailed API documentation, visit http://localhost:8000/docs when the service is running.