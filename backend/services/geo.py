from osgeo import gdal, osr
from typing import Dict, Any
import os
import uuid


def analyze_raster_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a raster file with GDAL to get georeferencing info and image metadata
    
    Returns:
        Dict with keys: gdal_compatible, is_georeferenced, width, height, bands, 
        has_projection, has_geotransform, error (if any)
    """
    try:
        src_ds = gdal.Open(file_path)
        if src_ds is None:
            return {
                "gdal_compatible": False,
                "is_georeferenced": False,
                "error": "File cannot be opened by GDAL"
            }

        if len(src_ds.GetSubDatasets()) > 1:
            return {
                "gdal_compatible": False,
                "is_georeferenced": False,
                "error": "File is a subdataset, not a single page"
            }
        
        # Get basic info
        width = src_ds.RasterXSize
        height = src_ds.RasterYSize
        bands = src_ds.RasterCount
        projection = src_ds.GetProjection()
        geotransform = src_ds.GetGeoTransform()
        
        # Check if already georeferenced
        has_projection = bool(projection and projection.strip())
        has_geotransform = bool(geotransform and geotransform != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
        is_georeferenced = has_projection and has_geotransform
        
        src_ds = None  # Close dataset
        
        return {
            "gdal_compatible": True,
            "is_georeferenced": is_georeferenced,
            "width": width,
            "height": height,
            "bands": bands,
            "has_projection": has_projection,
            "has_geotransform": has_geotransform
        }
        
    except Exception as e:
        return {
            "gdal_compatible": False,
            "is_georeferenced": False,
            "error": f"Error analyzing file: {str(e)}"
        }


def create_dummy_georeferenced_file(original_file_path: str, upload_dir: str, dpi: int = 300) -> str:
    """Create a dummy georeferenced GeoTIFF for MapServer compatibility
    
    Args:
        original_file_path: Path to the original file
        upload_dir: Upload directory (kept for compatibility)
        dpi: DPI setting for PDF conversion (default: 300)
    """
    
    # Set GDAL PDF DPI configuration option
    # TODO: not very thread safe
    gdal.SetConfigOption('GDAL_PDF_DPI', str(dpi))
    
    # Generate unique filename for georeferenced version
    file_extension = os.path.splitext(original_file_path)[1]
    base_name = os.path.splitext(os.path.basename(original_file_path))[0]
    georef_filename = f"{base_name}_georef_{uuid.uuid4().hex[:8]}.tif"
    
    # Place the georeferenced file in the same directory as the original file
    original_dir = os.path.dirname(original_file_path)
    georef_path = os.path.join(original_dir, georef_filename)
    

    # Open the original file
    src_ds = gdal.Open(original_file_path)
    if src_ds is None:
        raise ValueError("Cannot open source file with GDAL")
    
    # Get image dimensions
    width = src_ds.RasterXSize
    height = src_ds.RasterYSize
    
    # Create dummy georeference in EPSG:3857 (Web Mercator)
    # This is more compatible with MapLibre GL JS tiling system
    
    # Use (0,0) as top-left corner and (max_x, max_y) as bottom-right corner
    # Scale the image to fit within a reasonable area for meaningful coordinates
    max_dimension = max(width, height)
    
    # Use a 1000km area in Web Mercator coordinates (meters)
    scale_factor = 1000000.0 / max_dimension  # 1000km = 1,000,000 meters
    
    # Calculate geographic dimensions
    geo_width_meters = width * scale_factor
    geo_height_meters = height * scale_factor
    
    # Set up coordinate system with y_max as top-left Y (GDAL convention)
    x_min = 0.0
    x_max = geo_width_meters
    y_min = 0.0
    y_max = geo_height_meters
    
    # Calculate pixel size in meters
    pixel_size_x = (x_max - x_min) / width
    pixel_size_y = (y_max - y_min) / height
    
    # Create geotransform with correct Y-axis orientation:
    # Geo (x_min, y_max) = Pixel (0,0)
    # Geo (x_max, y_min) = Pixel (width, height)
    geotransform = (
        x_min,              # top-left X
        pixel_size_x,       # pixel width
        0,                  # rotation
        y_max,              # top-left Y (note: MAX because Y decreases downwards)
        0,                  # rotation
        -pixel_size_y       # pixel height (negative so Y increases downward in pixel space)
    )
    
    # Create output GeoTIFF from scratch to ensure projection is set properly
    driver = gdal.GetDriverByName('GTiff')
    
    # Get source dataset dimensions and data type
    width = src_ds.RasterXSize
    height = src_ds.RasterYSize
    bands = src_ds.RasterCount
    data_type = src_ds.GetRasterBand(1).DataType
    
    try:
        # Create new dataset with optimized creation options
        creation_options = [
            'COMPRESS=LZW', 
            'TILED=YES',
            'INTERLEAVE=PIXEL',
            'TILED=TRUE',
            'BLOCKXSIZE=256',
            'BLOCKYSIZE=256',
            'ZLEVEL=1',
            'BIGTIFF=IF_SAFER'
        ]
        dst_ds = driver.Create(georef_path, width, height, bands, data_type, options=creation_options)
        
        # Copy all raster data using GDAL's internal methods (avoid ReadAsArray)
        for band_idx in range(1, bands + 1):
            src_band = src_ds.GetRasterBand(band_idx)
            dst_band = dst_ds.GetRasterBand(band_idx)
            
            # Use GDAL's RasterIO to copy data without needing numpy
            # Read the entire band as binary data and write directly
            band_data = src_band.ReadRaster(0, 0, width, height)
            dst_band.WriteRaster(0, 0, width, height, band_data)
            
            # Copy band metadata
            no_data_value = src_band.GetNoDataValue()
            if no_data_value is not None:
                dst_band.SetNoDataValue(no_data_value)
        
        # Apply geotransform
        dst_ds.SetGeoTransform(geotransform)
        
        # Set EPSG:3857 projection (Web Mercator)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)
        wkt = srs.ExportToWkt()
        dst_ds.SetProjection(wkt)
        
        print(f"Set projection on dummy georeferenced file: {wkt[:100]}...")
        
        # Flush and close datasets to ensure changes are written
        dst_ds.FlushCache()
        src_ds = None
        dst_ds = None
        
        return georef_path
        
    except Exception as e:
        # If georeferencing fails, clean up and return original path
        print(f"Failed to create dummy georeferenced file: {e}")
        if os.path.exists(georef_path):
            try:
                os.remove(georef_path)
            except Exception as cleanup_error:
                print(f"Failed to cleanup georeferenced file: {cleanup_error}")
        
        # Return original file path as fallback instead of raising
        print(f"Falling back to original file path: {original_file_path}")
        return original_file_path
    finally:
        gdal.SetConfigOption('GDAL_PDF_DPI', None)
