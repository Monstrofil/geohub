import os
import tempfile
from pathlib import Path

class MapServerService:
    def __init__(self, uploads_dir="./uploads", mapserver_url="http://localhost:8081"):
        self.uploads_dir = Path(uploads_dir)
        self.mapserver_url = mapserver_url
        
    def get_map_url(self, filename):
        """
        Generate a MapServer URL for a GeoTIFF file
        """
        if not filename:
            return None
            
        file_path = self.uploads_dir / filename
        
        if not file_path.exists():
            return None
            
        # Check if it's a GeoTIFF file
        if not self._is_geotiff(filename):
            return None
            
        # Create a temporary MapServer configuration for this specific file
        map_config = self._create_map_config(filename)
        
        # Return the MapServer URL
        return f"{self.mapserver_url}/mapserver?map={map_config}&layer=geotiff_layer&mode=map"
    
    def _is_geotiff(self, filename):
        """
        Check if a file is a GeoTIFF based on extension
        """
        geotiff_extensions = {'.tif', '.tiff', '.geotiff'}
        return Path(filename).suffix.lower() in geotiff_extensions
    
    def _create_map_config(self, filename):
        """
        Create a temporary MapServer configuration file for a specific GeoTIFF
        """
        config_content = f"""MAP
  NAME "Tagger MapServer - {filename}"
  STATUS ON
  SIZE 800 600
  EXTENT -180 -90 180 90
  UNITS DD
  IMAGETYPE PNG
  CONFIG "MS_ERRORFILE" "/tmp/ms_error.log"
  DEBUG 5
  
  WEB
    METADATA
      "wms_title"           "Tagger MapServer"
      "wms_onlineresource"  "{self.mapserver_url}/mapserver?"
      "wms_srs"             "EPSG:4326 EPSG:3857"
      "wms_enable_request"  "*"
    END
  END

  LAYER
    NAME "geotiff_layer"
    TYPE RASTER
    STATUS ON
    CONNECTIONTYPE GDAL
    CONNECTION "/opt/mapserver/{filename}"
    PROCESSING "BANDS=1,2,3"
    PROCESSING "SCALE=AUTO"
    METADATA
      "wms_title" "GeoTIFF Layer"
    END
  END
END"""
        
        # Create temporary config file
        temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.map', delete=False)
        temp_config.write(config_content)
        temp_config.close()
        
        return temp_config.name
    
    def get_preview_url(self, filename):
        """
        Get a simple preview URL for a GeoTIFF file
        """
        if not self._is_geotiff(filename):
            return None
            
        return f"{self.mapserver_url}/mapserver?map=/usr/local/etc/mapserver.conf&layer=geotiff_layer&mode=map&map_geotiff_layer_filename={filename}" 