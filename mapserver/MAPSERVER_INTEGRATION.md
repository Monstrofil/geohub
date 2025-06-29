# MapServer Integration

This project now includes MapServer integration for GeoTIFF file preview and mapping capabilities.

## Overview

MapServer is a platform for publishing spatial data and interactive mapping applications to the web. In this project, it's used to:

- Serve GeoTIFF files as web maps
- Provide interactive map previews for raster files
- Enable WMS (Web Map Service) functionality

## Architecture

### Services

1. **MapServer Container** (`mapserver` service in docker-compose.yml)
   - Built from custom `mapserver/Dockerfile.mapserver`
   - Runs on port 8082
   - Serves GeoTIFF files via FastCGI
   - Apache web server with MapServer modules
   - Shares configuration files with backend via Docker volume

2. **Backend Integration** (`backend/mapserver_service.py`)
   - MapServerService class for generating map URLs
   - API endpoints for file preview and mapping
   - Automatic GeoTIFF detection
   - Writes MapServer configuration files to shared directory

3. **Frontend Integration** (`frontend/src/components/GeoTiffPreview.vue`)
   - Vue component for displaying map previews
   - Interactive controls (refresh, full map)
   - Error handling and loading states

## File Structure

```
├── mapserver/                    # MapServer configuration and build files
│   ├── Dockerfile.mapserver     # MapServer container build
│   ├── apache.mapserver.conf    # Apache configuration for MapServer
│   ├── mapserver.conf          # MapServer configuration template
│   └── MAPSERVER_INTEGRATION.md # This documentation
├── backend/
│   ├── mapserver_service.py     # MapServer service utilities
│   └── api.py                   # API endpoints for map services
└── frontend/
    ├── components/
    │   └── GeoTiffPreview.vue   # Map preview component
    └── data/
        └── presets/
            └── generic/
                └── geotiff.json # GeoTIFF preset definition
```

## Shared Directory Architecture

The backend and MapServer containers share a volume for configuration files:

- **Backend Container**: Writes MapServer config files to `/opt/shared/mapserver/`
- **MapServer Container**: Reads config files from `/opt/shared/mapserver/`
- **Docker Volume**: `mapserver_configs` volume shared between containers

### Configuration File Naming

MapServer configuration files are generated with unique names:
- Format: `map_{uuid}_{filename}.map`
- Example: `map_a1b2c3d4_satellite_image.map`

## Usage

### Starting the Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Backend API (port 8000)
- Frontend (port 8080)
- MapServer (port 8082)

### GeoTIFF Preview

1. Upload a GeoTIFF file (.tif, .tiff, .geotiff)
2. The file will be automatically detected as a GeoTIFF
3. Backend creates a MapServer configuration file in shared directory
4. In the file editor, a map preview will be displayed
5. Use the controls to refresh or open the full map

### API Endpoints

- `GET /files/{file_id}/preview` - Get preview URL for a file
- `GET /files/{file_id}/map` - Get MapServer URL for a GeoTIFF
- `POST /mapserver/cleanup` - Clean up old configuration files

## Configuration

### MapServer Configuration

The `mapserver/mapserver.conf` file contains the base MapServer configuration:

```mapfile
MAP
  NAME "Tagger MapServer"
  STATUS ON
  SIZE 800 600
  EXTENT -180 -90 180 90
  UNITS DD
  IMAGETYPE PNG
  
  LAYER
    NAME "geotiff_layer"
    TYPE RASTER
    STATUS ON
    CONNECTIONTYPE GDAL
    CONNECTION "/opt/mapserver/{filename}"
    PROCESSING "BANDS=1,2,3"
    PROCESSING "SCALE=AUTO"
  END
END
```

### Apache Configuration

The `mapserver/apache.mapserver.conf` file configures Apache for FastCGI:

- Loads required modules (proxy, fcgid)
- Configures FastCGI wrapper for MapServer
- Sets up performance tuning parameters

### Docker Volumes

```yaml
volumes:
  - ./backend/uploads:/opt/shared/uploads          # Shared uploads directory
  - mapserver_configs:/opt/shared/mapserver        # Shared MapServer configs
```

## Supported File Types

Currently supported for map preview:
- `.tif` - Tagged Image File Format
- `.tiff` - Tagged Image File Format
- `.geotiff` - GeoTIFF format

## Development

### Adding New Raster Formats

1. Update `backend/mapserver_service.py` to include new extensions
2. Add corresponding preset in `frontend/src/data/presets/`
3. Update the `isGeoTiff` computed property in `FileEditor.vue`

### Customizing Map Display

1. Modify `mapserver/mapserver.conf` for different map settings
2. Update the MapServer configuration generation in `backend/mapserver_service.py`
3. Adjust the preview component styling in `frontend/src/components/GeoTiffPreview.vue`

## Maintenance

### Cleaning Up Old Configurations

MapServer configuration files are automatically cleaned up:

```bash
# Clean up configs older than 24 hours (default)
curl -X POST http://localhost:8000/api/v1/mapserver/cleanup

# Clean up configs older than 48 hours
curl -X POST "http://localhost:8000/api/v1/mapserver/cleanup?max_age_hours=48"
```

### Manual Cleanup

You can also manually clean up the shared directory:

```bash
# Access the backend container
docker exec -it tagger_backend_1 sh

# List configuration files
ls -la /opt/shared/mapserver/

# Remove old files
rm /opt/shared/mapserver/map_*.map
```

## Troubleshooting

### MapServer Not Starting

1. Check Docker logs: `docker-compose logs mapserver`
2. Verify Apache configuration syntax in `mapserver/apache.mapserver.conf`
3. Ensure all required packages are installed in `mapserver/Dockerfile.mapserver`
4. Check shared directory permissions: `ls -la /opt/shared/mapserver/`

### GeoTIFF Not Displaying

1. Check if file is properly uploaded to `/opt/shared/uploads/`
2. Verify MapServer config file exists in `/opt/shared/mapserver/`
3. Check MapServer error logs: `/tmp/ms_error.log`
4. Verify file permissions in shared directories

### Configuration File Issues

1. Check if backend can write to shared directory
2. Verify MapServer can read from shared directory
3. Check file permissions: `chmod 755 /opt/shared/mapserver`
4. Ensure unique filenames are generated

### Performance Issues

1. Adjust FastCGI parameters in `mapserver/apache.mapserver.conf`
2. Consider caching strategies
3. Optimize GeoTIFF files (compression, overviews)
4. Clean up old configuration files regularly

## Future Enhancements

- Add support for other raster formats (JPEG2000, ECW)
- Implement map caching with MapCache
- Add vector file support (Shapefile, GeoJSON)
- Include map controls (zoom, pan, layer toggle)
- Add coordinate system transformation
- Implement map export functionality
- Add configuration file caching and reuse 