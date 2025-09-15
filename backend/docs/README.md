# File Tagger Backend API

A FastAPI-based backend for uploading, managing, and tagging files with PostgreSQL and Tortoise ORM.

## Features

- File upload with automatic storage management
- File metadata storage (name, size, MIME type, etc.)
- Flexible tag system for categorizing files
- File search by tags
- File download functionality
- RESTful API with automatic documentation

## Database Schema

### Files Table
- `id`: Primary key
- `name`: Unique filename (UUID-based)
- `original_name`: Original filename
- `file_path`: Path to stored file
- `file_size`: File size in bytes
- `mime_type`: MIME type
- `tags`: JSON field containing file tags
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## API Endpoints

### Files

- `POST /api/v1/files/upload` - Upload a new file with optional tags
- `GET /api/v1/files` - List all files with pagination
- `GET /api/v1/files/{file_id}` - Get specific file details
- `GET /api/v1/files/{file_id}/download` - Download a file
- `DELETE /api/v1/files/{file_id}` - Delete a file
- `POST /api/v1/files/search` - Search files by tags

### Tags

- `GET /api/v1/files/{file_id}/tags` - Get all tags for a file
- `PUT /api/v1/files/{file_id}/tags` - Update all tags for a file
- `POST /api/v1/files/{file_id}/tags/{key}` - Add a single tag
- `DELETE /api/v1/files/{file_id}/tags/{key}` - Remove a tag

## Setup

1. **Environment Variables**
   ```bash
   DATABASE_URL=postgres://tagger_user:tagger_password@postgres:5432/tagger_db
   DB_HOST=postgres
   DB_PORT=5432
   DB_USER=tagger_user
   DB_PASSWORD=tagger_password
   DB_NAME=tagger_db
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up backend
   ```

4. **Seed Sample Data (Optional)**
   ```bash
   python seed_data.py
   ```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage

### Upload a file with tags
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@photo.jpg" \
  -F "tags={\"type\": \"raster\", \"name\": \"photo.jpg\"}"
```

### List all files
```bash
curl -X GET "http://localhost:8000/api/v1/files"
```

### Update file tags
```bash
curl -X PUT "http://localhost:8000/api/v1/files/1/tags" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"tags": {"type": "vector", "name": "map.svg"}}'
```

### Search files by tags
```bash
curl -X POST "http://localhost:8000/api/v1/files/search" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"tags": {"type": "raster"}}'
```

## File Storage

Files are stored in the `uploads/` directory with UUID-based filenames to prevent conflicts. The original filename is preserved in the database for display purposes.

## Error Handling

The API returns appropriate HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found (file doesn't exist)
- `500` - Internal Server Error

All errors include a JSON response with an error message. 