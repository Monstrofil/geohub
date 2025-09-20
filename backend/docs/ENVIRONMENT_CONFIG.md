# Environment Configuration

This document describes how to configure the Tagger application for different environments using environment variables.

## Environment Variables

### Database Configuration

- **DATABASE_URL**: PostgreSQL connection string
  - Format: `postgres://username:password@host:port/database`
  - Default: `postgres://tagger_user:tagger_password@postgres:5432/tagger_db`

- **POSTGRES_DB**: PostgreSQL database name
  - Default: `tagger_db`

- **POSTGRES_USER**: PostgreSQL username
  - Default: `tagger_user`

- **POSTGRES_PASSWORD**: PostgreSQL password
  - Default: `tagger_password`
  - **IMPORTANT**: Change this in production!

### Backend Configuration


- **DEBUG**: Enable debug mode
  - Default: `false`
  - Values: `true`, `false`

- **LOG_LEVEL**: Logging level
  - Default: `info`
  - Values: `debug`, `info`, `warning`, `error`, `critical`

### Authentication & Security

- **JWT_SECRET_KEY**: Secret key for JWT token signing
  - Default: `your-secret-key-change-this-in-production`
  - **CRITICAL**: Must be changed in production to a strong, random key

- **JWT_EXPIRE_MINUTES**: JWT access token expiration time in minutes
  - Default: `30`

- **JWT_REFRESH_EXPIRE_DAYS**: JWT refresh token expiration time in days
  - Default: `7`

- **CORS_ORIGINS**: Comma-separated list of allowed CORS origins
  - Default: `http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173`
  - Production example: `https://yourdomain.com,https://www.yourdomain.com`

### Frontend Configuration

- **VITE_API_BASE_URL**: Base URL for API calls from frontend
  - Default: `http://localhost:8000/api/v1`
  - Production example: `https://api.yourdomain.com/api/v1`

### MapServer Configuration

- **MAPSERVER_URL**: The URL where the MapServer service is accessible
  - Default: `http://mapserver`
  - Local development: `http://localhost:8082`
  - Production example: `https://mapserver.yourdomain.com`

- **MAPSERVER_SHARED_DIR**: Directory path for MapServer configuration files
  - Default: `/opt/shared/mapserver`
  - This should be a path accessible to both the backend and MapServer services

## Configuration Methods

### 1. Docker Compose (Recommended for Development)

The `docker-compose.yml` file automatically configures the environment variables with sensible defaults for containerized deployment:

```yaml
environment:
  MAPSERVER_URL: ${MAPSERVER_URL:-http://mapserver}
  MAPSERVER_SHARED_DIR: ${MAPSERVER_SHARED_DIR:-/opt/shared/mapserver}
```

### 2. .env File

Create a `.env` file in the project root to override default values:

```bash
# Copy the example file and modify as needed
cp .env.example .env
```

Example `.env` file:
```
MAPSERVER_URL=http://mapserver
MAPSERVER_SHARED_DIR=/opt/shared/mapserver
```

### 3. System Environment Variables

Set environment variables directly in your system or deployment environment:

```bash
export MAPSERVER_URL=https://your-production-mapserver.com
export MAPSERVER_SHARED_DIR=/opt/shared/mapserver
```

## Deployment Scenarios

### Local Development

```
MAPSERVER_URL=http://localhost:8082
MAPSERVER_SHARED_DIR=/opt/shared/mapserver
```

### Docker Compose

```
MAPSERVER_URL=http://mapserver
MAPSERVER_SHARED_DIR=/opt/shared/mapserver
```

### Production

```
# Database
DATABASE_URL=postgres://tagger_prod:strong_password@production-db:5432/tagger_prod_db
POSTGRES_DB=tagger_prod_db
POSTGRES_USER=tagger_prod
POSTGRES_PASSWORD=strong_password_here

# Backend
DEBUG=false
LOG_LEVEL=warning

# Security
JWT_SECRET_KEY=your-very-strong-secret-key-for-production
JWT_EXPIRE_MINUTES=60
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1

# MapServer
MAPSERVER_URL=https://mapserver.yourdomain.com
MAPSERVER_SHARED_DIR=/opt/shared/mapserver
```

## Testing Configuration

To verify that your configuration is working correctly:

1. Check the application logs on startup
2. Verify that MapServer URLs are generated correctly
3. Test file preview functionality

The MapServerService will automatically use the configured URL when generating preview URLs and MapServer configuration files.

## Production Deployment Checklist

### Security Requirements

- [ ] **Change JWT_SECRET_KEY**: Generate a strong, random secret key (minimum 32 characters)
- [ ] **Change Database Password**: Use a strong password for POSTGRES_PASSWORD
- [ ] **Configure CORS**: Set CORS_ORIGINS to only include your production domains
- [ ] **Enable HTTPS**: Use HTTPS URLs for all production services
- [ ] **Disable Debug**: Set DEBUG=false in production
- [ ] **Set Log Level**: Use LOG_LEVEL=warning or LOG_LEVEL=error in production

### Performance Optimization

- [ ] **Worker Processes**: Set UVICORN_WORKERS to match your server's CPU cores
- [ ] **Database Connection**: Use a dedicated database server for production
- [ ] **Port Configuration**: Configure appropriate ports for your infrastructure

### Environment File Management

1. **Create Production .env**:
   ```bash
   cp .env.example .env.production
   # Edit .env.production with your production values
   ```

2. **Secure Environment Files**:
   ```bash
   chmod 600 .env.production
   chown root:root .env.production
   ```

3. **Use in Docker Compose**:
   ```bash
   docker-compose --env-file .env.production up -d
   ```

### Example Production Commands

```bash
# Generate a strong JWT secret
openssl rand -hex 32

# Start production deployment
docker-compose --env-file .env.production up -d

# Check service health
curl https://api.yourdomain.com/health
```

## Environment File Priority

1. Command line environment variables (highest priority)
2. `.env` file in project root
3. Default values in docker-compose.yml
4. Application defaults (lowest priority)
