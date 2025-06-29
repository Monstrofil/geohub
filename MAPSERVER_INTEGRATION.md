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
   - Built from custom Dockerfile.mapserver
   - Runs on port 8082
   - Serves GeoTIFF files via FastCGI
   - Apache web server with MapServer modules

2. **Backend Integration** (`mapserver_service.py`)
   - MapServerService class for generating map URLs
   - API endpoints for file preview and mapping
   - Automatic GeoTIFF detection

3. **Frontend Integration** (`GeoTiffPreview.vue`)
   - Vue component for displaying map previews
   - Interactive controls (refresh, full map)
   - Error handling and loading states

## File Structure

```
├── Dockerfile.mapserver          # MapServer container build
├── apache.mapserver.conf         # Apache configuration for MapServer
├── mapserver.conf               # MapServer configuration template
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
3. In the file editor, a map preview will be displayed
4. Use the controls to refresh or open the full map

### API Endpoints

- `GET /files/{file_id}/preview` - Get preview URL for a file
- `GET /files/{file_id}/map` - Get MapServer URL for a GeoTIFF

## Configuration

### MapServer Configuration

The `mapserver.conf` file contains the base MapServer configuration:

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

The `apache.mapserver.conf` file configures Apache for FastCGI:

- Loads required modules (proxy, fcgid)
- Configures FastCGI wrapper for MapServer
- Sets up performance tuning parameters

## Supported File Types

Currently supported for map preview:
- `.tif` - Tagged Image File Format
- `.tiff` - Tagged Image File Format
- `.geotiff` - GeoTIFF format

## Development

### Adding New Raster Formats

1. Update `mapserver_service.py` to include new extensions
2. Add corresponding preset in `frontend/src/data/presets/`
3. Update the `isGeoTiff` computed property in `FileEditor.vue`

### Customizing Map Display

1. Modify `mapserver.conf` for different map settings
2. Update the MapServer configuration generation in `mapserver_service.py`
3. Adjust the preview component styling in `GeoTiffPreview.vue`

## Troubleshooting

### MapServer Not Starting

1. Check Docker logs: `docker-compose logs mapserver`
2. Verify Apache configuration syntax
3. Ensure all required packages are installed in Dockerfile

### GeoTIFF Not Displaying

1. Check if file is properly uploaded to `/opt/mapserver/`
2. Verify file permissions
3. Check MapServer error logs: `/tmp/ms_error.log`

### Performance Issues

1. Adjust FastCGI parameters in `apache.mapserver.conf`
2. Consider caching strategies
3. Optimize GeoTIFF files (compression, overviews)

## Future Enhancements

- Add support for other raster formats (JPEG2000, ECW)
- Implement map caching with MapCache
- Add vector file support (Shapefile, GeoJSON)
- Include map controls (zoom, pan, layer toggle)
- Add coordinate system transformation
- Implement map export functionality 