# MapServer Configuration

This folder contains all MapServer-related configuration and build files for the Tagger application.

## Files

- `Dockerfile.mapserver` - Docker build file for the MapServer container
- `apache.mapserver.conf` - Apache configuration for FastCGI and MapServer
- `mapserver.conf` - MapServer configuration template for serving GeoTIFF files
- `MAPSERVER_INTEGRATION.md` - Complete documentation for MapServer integration

## Usage

The MapServer service is configured in the main `docker-compose.yml` file and will automatically build from this folder when you run:

```bash
docker-compose up -d
```

For detailed information about the MapServer integration, see `MAPSERVER_INTEGRATION.md`. 