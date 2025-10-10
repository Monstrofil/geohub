# Background Tasks with Celery

This document describes the implementation of background task processing using Celery for the tagger application.

## Overview

The `convert-to-geo-raster` operation has been converted from a synchronous API call to an asynchronous background task to improve user experience and system performance.

## Architecture

### Components

1. **Redis**: Message broker and result backend
2. **Celery Worker**: Processes background tasks
3. **FastAPI Backend**: Initiates tasks and provides status endpoints
4. **Task Queue**: Dedicated queue for geo-processing tasks

### Task Flow

```
User Request → FastAPI → Celery Task → Redis → Celery Worker → Database Update
     ↓              ↓           ↓
Status Check ← Task Status ← Progress Updates
```

## API Changes

### Convert to Geo-Raster (Updated)

**Endpoint**: `POST /api/v1/tree-items/{item_id}/convert-to-geo-raster`

**Response**: Returns task ID instead of immediate result
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "STARTED",
  "message": "Geo-raster conversion started in background"
}
```

### New Task Management Endpoints

#### Get Task Status
**Endpoint**: `GET /api/v1/tasks/{task_id}/status`

**Response**:
```json
{
  "task_id": "abc123-def456-ghi789",
  "state": "PROGRESS",
  "status": "Creating georeferenced file",
  "progress": 40,
  "result": null,
  "error": null
}
```

#### Cancel Task
**Endpoint**: `POST /api/v1/tasks/{task_id}/cancel`

**Response**:
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "CANCELLED",
  "message": "Task cancellation requested"
}
```

#### Get Conversion Status
**Endpoint**: `GET /api/v1/tree-items/{item_id}/conversion-status`

**Response**:
```json
{
  "item_id": "file-uuid-here",
  "status": "COMPLETED",
  "object_type": "geo_raster_file",
  "message": "File is already converted to geo raster"
}
```

## Task States

- **PENDING**: Task is waiting to be processed
- **PROGRESS**: Task is currently running
- **SUCCESS**: Task completed successfully
- **FAILURE**: Task failed with an error
- **CANCELLED**: Task was cancelled

## Progress Tracking

The conversion task provides progress updates at key stages:

1. **0%**: Starting conversion
2. **10%**: Loading file
3. **20%**: Analyzing file
4. **40%**: Creating georeferenced file
5. **80%**: Updating database
6. **100%**: Conversion complete

## Development Setup

### Prerequisites

1. Redis server running
2. Python dependencies installed (`celery[redis]`, `redis`)

### Starting Services

#### Using Docker Compose (Recommended)
```bash
# Start all services including Redis and Celery worker
docker-compose up

# Or start specific services
docker-compose up redis celery-worker backend
```

#### Manual Development Setup

1. **Start Redis**:
   ```bash
   redis-server
   ```

2. **Start Celery Worker**:
   ```bash
   cd backend
   python start_celery.py
   ```

3. **Start FastAPI Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

4. **Monitor Tasks** (Optional):
   ```bash
   # Flower web interface available at http://localhost:5555
   # Or start with docker-compose (included automatically)
   ```

### Environment Variables

Add to your `.env` file:
```env
REDIS_URL=redis://localhost:6379/0
# Optional: For production Flower basic auth (generate with: echo -n "admin:password" | base64)
FLOWER_BASIC_AUTH=admin:$$2y$$10$$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi
```

**Note**: The Celery worker does NOT need `JWT_SECRET_KEY` or other authentication-related environment variables since background tasks don't perform user authentication - that's handled by the FastAPI backend before tasks are created.

## Production Deployment

### Docker Compose Production

The production setup includes:
- Redis with persistent volume
- Celery worker with restart policy
- Proper health checks and dependencies

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Scaling

To scale Celery workers:
```bash
# Scale to 3 workers
docker-compose up --scale celery-worker=3
```

### Monitoring

#### Flower Web Interface
Flower provides a comprehensive web-based monitoring interface:

- **Development**: http://localhost:5555
- **Production**: https://yourdomain.com/flower (with basic auth)

Features:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task retry and cancellation
- Performance metrics
- Queue management

#### Command Line Monitoring
```bash
# Monitor active tasks
docker exec -it tagger_celery_worker celery -A celery_app inspect active

# Monitor task statistics
docker exec -it tagger_celery_worker celery -A celery_app inspect stats
```

#### Redis Monitoring
```bash
# Connect to Redis CLI
docker exec -it tagger_redis redis-cli

# Monitor Redis commands
docker exec -it tagger_redis redis-cli monitor
```

## Error Handling

### Task Retries

Tasks are configured with:
- Maximum 3 retries
- Exponential backoff with jitter
- Late acknowledgment for reliability

### Error Recovery

1. **Database Connection Issues**: Tasks will retry automatically
2. **File Processing Errors**: Tasks fail gracefully with error details
3. **Worker Crashes**: Tasks are reassigned to other workers

### Monitoring Failed Tasks

```bash
# List failed tasks
docker exec -it tagger_celery_worker celery -A celery_app inspect failed

# Retry failed tasks
docker exec -it tagger_celery_worker celery -A celery_app control retry <task_id>
```

## Performance Considerations

### Queue Configuration

- **geo_processing**: Dedicated queue for heavy geo-processing tasks
- **default**: General purpose queue for lighter tasks

### Worker Configuration

- **Concurrency**: 2 workers per container (configurable)
- **Memory Management**: Workers restart after 1000 tasks
- **Resource Limits**: Configure based on available CPU/memory

### Redis Configuration

- **Persistence**: Enabled for task results
- **Memory**: Monitor usage for large file processing
- **Connection Pooling**: Configured for optimal performance

## Troubleshooting

### Common Issues

1. **Tasks Stuck in PENDING**:
   - Check if Celery worker is running
   - Verify Redis connection
   - Check worker logs for errors

2. **Tasks Failing**:
   - Check database connectivity
   - Verify file permissions
   - Review task logs for specific errors

3. **High Memory Usage**:
   - Monitor Redis memory usage
   - Adjust worker concurrency
   - Consider task result expiration

### Debugging Commands

```bash
# Check worker status
docker exec -it tagger_celery_worker celery -A celery_app status

# View worker logs
docker logs tagger_celery_worker

# Check Redis status
docker exec -it tagger_redis redis-cli ping

# View task details
docker exec -it tagger_celery_worker celery -A celery_app result <task_id>

# Test Celery setup
docker exec -it tagger_celery_worker python test_celery.py
```

### Common Issues and Solutions

#### 1. ModuleNotFoundError: No module named 'database'
**Problem**: Celery worker can't find the database module.

**Solution**: The task now imports modules after database initialization. If you still see this error:
```bash
# Check if the worker has the correct working directory
docker exec -it tagger_celery_worker pwd
# Should be /app

# Check if database.py exists
docker exec -it tagger_celery_worker ls -la database.py
```

#### 2. ValueError: Exception information must include the exception type
**Problem**: Celery can't properly serialize exceptions.

**Solution**: This has been fixed with proper exception handling. If you still see this:
```bash
# Restart the Celery worker
docker-compose restart celery-worker

# Check Redis for corrupted task data
docker exec -it tagger_redis redis-cli FLUSHDB
```

#### 3. Database Connection Issues
**Problem**: Tasks fail with database connection errors.

**Solution**: 
```bash
# Check database connectivity
docker exec -it tagger_celery_worker python -c "
import asyncio
from database import TORTOISE_ORM
from tortoise import Tortoise

async def test():
    await Tortoise.init(config=TORTOISE_ORM)
    print('Database connection OK')
    await Tortoise.close_connections()

asyncio.run(test())
"
```

#### 4. Task Stuck in PENDING State
**Problem**: Tasks are created but never processed.

**Solution**:
```bash
# Check if worker is running
docker exec -it tagger_celery_worker celery -A celery_app inspect active

# Check worker logs for errors
docker logs tagger_celery_worker --tail 50

# Restart worker if needed
docker-compose restart celery-worker
```

## Flower Configuration

### Development
Flower is automatically available at http://localhost:5555 when using docker-compose.

### Production
In production, Flower is secured with basic authentication and accessible via Traefik at `/flower`.

#### Generate Basic Auth Credentials
```bash
# Generate password hash for admin:password
echo -n "admin:password" | base64
# Or use htpasswd
htpasswd -nb admin password
```

#### Environment Variable
```env
FLOWER_BASIC_AUTH=admin:$$2y$$10$$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi
```

### Flower Features
- **Dashboard**: Overview of workers, tasks, and queues
- **Tasks**: Detailed view of individual tasks with logs
- **Workers**: Worker status, active tasks, and statistics
- **Broker**: Redis connection and queue information
- **Monitor**: Real-time task execution monitoring
- **API**: RESTful API for programmatic access

## Future Enhancements

1. **Task Prioritization**: Implement priority queues for urgent tasks
2. **Progress Webhooks**: Real-time progress updates via WebSockets
3. **Task Scheduling**: Delayed task execution for batch processing
4. **Advanced Monitoring**: Integration with monitoring tools (Prometheus, Grafana)
5. **Task Dependencies**: Chain related tasks together
