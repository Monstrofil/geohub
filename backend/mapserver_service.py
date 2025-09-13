import os
from pathlib import Path
import uuid
from osgeo import gdal, osr

class MapServerService:
    def __init__(self, uploads_dir="./uploads", mapserver_url="http://localhost:8082", shared_mapserver_dir="/opt/shared/mapserver"):
        self.uploads_dir = Path(uploads_dir)
        self.mapserver_url = mapserver_url
        self.shared_mapserver_dir = Path(shared_mapserver_dir)
        
        # Ensure shared directory exists
        self.shared_mapserver_dir.mkdir(parents=True, exist_ok=True)
        
    def get_map_url(self, filename):
        """
        Generate a MapServer URL for a GeoTIFF file
        """
        if not filename:
            return None
            
        # Check in uploads directory first, then temp directory
        file_path = self.uploads_dir / filename
        
        if not file_path.exists():
            # Try temp directory (for georeferencing temp files)
            temp_dir = Path("./temp")
            file_path = temp_dir / filename
            
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return None
            
        # Check if it's a GeoTIFF file or raster file
        if not self._is_geotiff(filename) and not filename.endswith(('.tif', '.tiff', '.pdf')):
            print(f"File is not a raster: {filename}")
            return None
            
        # Create a MapServer configuration for this specific file
        map_config_path = self._create_map_config(filename)
        
        # Return the MapServer URL
        return f"{self.mapserver_url}/mapserver?map={map_config_path}"
    
    def _is_geotiff(self, filename):
        """
        Check if a file is a GeoTIFF or supported raster based on extension
        """
        geotiff_extensions = {'.tif', '.tiff', '.geotiff', '.pdf'}
        return Path(filename).suffix.lower() in geotiff_extensions
    
    def _get_file_data_path(self, filename):
        """
        Get the correct data path for a file - all files are now in the main directory
        """
        # All files (including warped files) are now in the uploads directory
        return filename
    
    def _validate_gdal(self):
        """
        Validate that GDAL is working properly
        """
        try:
            gdal_version = gdal.VersionInfo()
            print(f"GDAL version: {gdal_version}")
            return True
        except Exception as e:
            print(f"GDAL validation failed: {e}")
            return False
    
    def _get_gdal_info(self, filename):
        """
        Extract extent and projection information from a georeferenced file using GDAL
        """
        # Validate GDAL first
        if not self._validate_gdal():
            print("GDAL validation failed, cannot extract geospatial information")
            return None, None
            
        # All files are in the uploads directory
        file_path = self.uploads_dir / filename
        
        try:
            print(f"File path: {file_path}")
            # Open the dataset
            dataset = gdal.Open(str(file_path))
            if dataset is None:
                print(f"Could not open file with GDAL: {file_path}")
                return None, None
            
            # Get the extent from the dataset
            geotransform = dataset.GetGeoTransform()

            print(f"Geotransform: {geotransform}")
            
            # Use GDAL's built-in extent calculation
            ulx = geotransform[0]
            uly = geotransform[3]
            lrx = geotransform[0] + geotransform[1] * dataset.RasterXSize
            lry = geotransform[3] + geotransform[5] * dataset.RasterYSize
            
            extent = (ulx, lry, lrx, uly)  # (min_x, min_y, max_x, max_y)
            print(f"Raw extent from geotransform: {extent}")
            
            # Get the projection
            projection = dataset.GetProjection()
            print(f"Raw projection from file: '{projection}' '{str(file_path)}'")
            print(f"Projection length: {len(projection) if projection else 0}")
            
            if projection and len(projection.strip()) > 0:
                # Convert to WKT format for MapServer
                spatial_ref = osr.SpatialReference()
                try:
                    spatial_ref.ImportFromWkt(projection)
                    print("Successfully imported projection from WKT")
                except Exception as e:
                    print(f"Failed to import projection from WKT: {e}")
                
                # Get EPSG code if available
                epsg_code = None
                try:
                    epsg_code = spatial_ref.GetAuthorityCode(None)
                    print(f"Extracted EPSG code: {epsg_code}")
                except Exception as e:
                    print(f"Failed to get EPSG code: {e}")
                
                if epsg_code:
                    projection_str = f'"init=epsg:{epsg_code}"'
                    print(f"Using EPSG code: {epsg_code}")
                else:
                    # Use WKT format if no EPSG code
                    projection_str = f'"{projection}"'
                    print("Using WKT projection format")
            else:
                # Default to WGS84 if no projection found
                projection_str = '"init=epsg:4326"'
                print("No projection found, using default WGS84")
            
            dataset = None  # Close the dataset
            
            return extent, projection_str
            
        except Exception as e:
            print(f"Error extracting GDAL info from {file_path}: {e}")
            return None, None
    
    def _create_map_config(self, filename):
        """
        Create a MapServer configuration file for a specific GeoTIFF in the shared directory
        """
        # Generate a unique config filename
        config_filename = f"map_{uuid.uuid4().hex[:8]}_{Path(filename).stem}.map"
        config_path = self.shared_mapserver_dir / config_filename
        
        # Get extent and projection from the file using GDAL
        extent, projection = self._get_gdal_info(filename)
        
        # Use extracted values or fallback to defaults
        if extent:
            extent_str = f"{extent[0]} {extent[1]} {extent[2]} {extent[3]}"
            print(f"Using extracted extent: {extent_str}")
        else:
            # Fallback to default extent (world)
            extent_str = "-180 -90 180 90"
            print(f"Using default extent: {extent_str}")
        
        if projection:
            projection_str = projection
            print(f"Using extracted projection: {projection_str}")
        else:
            # Fallback to WGS84
            projection_str = '"init=epsg:4326"'
            print(f"Using default projection: {projection_str}")
        
        # Determine the correct data path for the file
        data_path = self._get_file_data_path(filename)
        
        config_content = f"""
MAP
  NAME "Tagger MapServer - {filename}"
  STATUS ON
  SIZE 800 600
  EXTENT {extent_str}
  UNITS DD
  IMAGETYPE PNG
  CONFIG "MS_ERRORFILE" "/tmp/ms_error.log"
  DEBUG 5
  
  WEB
      IMAGEPATH "/tmp/ms_tmp/"
      IMAGEURL "/ms_tmp/"
      METADATA 
          WMS_ENABLE_REQUEST "*" 
      END
  END

    PROJECTION
        {projection_str}
    END

  LAYER
    NAME "geotiff_layer"
    TYPE RASTER
    STATUS ON
    DATA "/opt/mapserver/{data_path}"

    PROJECTION
        {projection_str}
    END
  END
END"""
        
        # Write the config file to the shared directory
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        print(f"Created MapServer config: {config_path}")
        return str(config_path)
    
    def get_preview_url(self, filename):
        """
        Get a simple preview URL for a GeoTIFF file
        """
        # Support both regular files and temp files
        if not self._is_geotiff(filename) and not filename.endswith(('.tif', '.tiff', '.pdf')):
            return None
            
        # Create a MapServer configuration for this specific file
        map_config_path = self._create_map_config(filename)
        
        return f"{self.mapserver_url}/mapserver?map={map_config_path}&layer=geotiff_layer&mode=map"
    
    def get_file_extent(self, filename):
        """
        Get the extent (bounding box) of a GeoTIFF file in WGS84 coordinates
        """
        if not self._is_geotiff(filename):
            return None
            
        # Get extent and projection from GDAL
        extent, projection_str = self._get_gdal_info(filename)
        
        if extent:
            print(f"Original extent: {extent}")
            print(f"Projection string: {projection_str}")
            
            # Convert extent to WGS84 if needed
            wgs84_extent = self._transform_extent_to_wgs84(extent, projection_str)
            
            print(f"Transformed extent: {wgs84_extent}")
            
            if wgs84_extent:
                # Return extent as a comma-separated string in WGS84
                result = f"{wgs84_extent[0]},{wgs84_extent[1]},{wgs84_extent[2]},{wgs84_extent[3]}"
                print(f"Returning extent: {result}")
                return result
        
        return None
    
    def _transform_extent_to_wgs84(self, extent, projection_str):
        """
        Transform extent coordinates to WGS84 (EPSG:4326)
        """
        try:
            # Create source spatial reference
            source_srs = osr.SpatialReference()
            
            # Parse projection string to get EPSG code
            if 'epsg:' in projection_str.lower():
                # Extract EPSG code from string like '"init=epsg:3857"'
                epsg_code = projection_str.split('epsg:')[1].split('"')[0]
                source_srs.ImportFromEPSG(int(epsg_code))
            else:
                # Try to import from WKT
                source_srs.ImportFromWkt(projection_str.strip('"'))
            
            # Create target spatial reference (WGS84)
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)
            
            # Create coordinate transformation
            transform = osr.CoordinateTransformation(source_srs, target_srs)
            
            # Transform the four corners of the extent
            # extent format: (x_min, y_min, x_max, y_max)
            x_min, y_min, x_max, y_max = extent
            
            # Transform all four corners to ensure we get the correct bounding box
            corners = [
                (x_min, y_min),  # bottom-left
                (x_max, y_min),  # bottom-right
                (x_min, y_max),  # top-left
                (x_max, y_max)   # top-right
            ]
            
            transformed_corners = []
            for x, y in corners:
                lng, lat, _ = transform.TransformPoint(x, y)
                transformed_corners.append((lng, lat))
            
            # Find the bounding box of all transformed corners
            lats = [corner[0] for corner in transformed_corners]
            lngs = [corner[1] for corner in transformed_corners]
            
            min_lng = min(lngs)
            max_lng = max(lngs)
            min_lat = min(lats)
            max_lat = max(lats)
            
            print(f"Original extent: {extent}")
            print(f"Transformed corners: {transformed_corners}")
            print(f"WGS84 extent: [{min_lng}, {min_lat}, {max_lng}, {max_lat}]")
            
            return (min_lng, min_lat, max_lng, max_lat)
            
        except Exception as e:
            print(f"Error transforming extent to WGS84: {e}")
            # Return original extent if transformation fails
            return extent
    
    def cleanup_old_configs(self, max_age_hours=24):
        """
        Clean up old MapServer configuration files
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for config_file in self.shared_mapserver_dir.glob("map_*.map"):
            try:
                file_age = current_time - config_file.stat().st_mtime
                if file_age > max_age_seconds:
                    config_file.unlink()
                    print(f"Cleaned up old config: {config_file}")
            except Exception as e:
                print(f"Error cleaning up {config_file}: {e}") 