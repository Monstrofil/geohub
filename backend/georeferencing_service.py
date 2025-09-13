"""
Georeferencing service for handling image warping and control point management
"""
import os
import json
import uuid
import tempfile
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from osgeo import gdal, osr, ogr
from dataclasses import dataclass
import math


@dataclass
class ControlPoint:
    """Control point for georeferencing"""
    image_x: float
    image_y: float
    world_x: float
    world_y: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'image_x': self.image_x,
            'image_y': self.image_y,
            'world_x': self.world_x,
            'world_y': self.world_y
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'ControlPoint':
        return cls(
            image_x=data['image_x'],
            image_y=data['image_y'],
            world_x=data['world_x'],
            world_y=data['world_y']
        )


class GeoreferencingService:
    """Service for handling georeferencing operations"""
    
    def __init__(self, uploads_dir: str = "./uploads", temp_dir: str = "./uploads"):
        self.uploads_dir = Path(uploads_dir)
        self.temp_dir = Path(temp_dir)  # Use uploads dir for temp files to ensure MapServer access
        self.temp_dir.mkdir(exist_ok=True)
        
        # Enable GDAL exceptions
        gdal.UseExceptions()
    
    def is_georeferenced(self, file_path: str) -> bool:
        """
        Check if a raster file is already georeferenced
        
        Args:
            file_path: Path to the raster file
            
        Returns:
            bool: True if file is georeferenced, False otherwise
        """
        try:
            dataset = gdal.Open(file_path)
            if dataset is None:
                return False
            
            # Check if it has a valid geotransform
            geotransform = dataset.GetGeoTransform()
            
            # Default geotransform is (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
            # If it's different, the file is probably georeferenced
            default_gt = (0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
            
            if geotransform == default_gt:
                return False
            
            # Also check if it has a spatial reference system
            projection = dataset.GetProjection()
            
            dataset = None  # Close dataset
            
            return projection is not None and projection != ""
            
        except Exception as e:
            print(f"Error checking georeferencing: {e}")
            return False
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about a raster image
        
        Args:
            file_path: Path to the raster file
            
        Returns:
            dict: Image information including dimensions and data type
        """
        try:
            dataset = gdal.Open(file_path)
            if dataset is None:
                raise ValueError("Cannot open image file")
            
            info = {
                'width': dataset.RasterXSize,
                'height': dataset.RasterYSize,
                'bands': dataset.RasterCount,
                'driver': dataset.GetDriver().ShortName,
                'georeferenced': self.is_georeferenced(file_path)
            }
            
            # Get data type from first band
            if dataset.RasterCount > 0:
                band = dataset.GetRasterBand(1)
                info['data_type'] = gdal.GetDataTypeName(band.DataType)
            
            dataset = None
            return info
            
        except Exception as e:
            raise ValueError(f"Error reading image info: {e}")
    
    def calculate_transform_from_control_points(self, control_points: List[ControlPoint]) -> Optional[List[float]]:
        """
        Calculate geotransform coefficients from control points using polynomial transformation
        
        Args:
            control_points: List of control points
            
        Returns:
            list: Geotransform coefficients or None if calculation fails
        """
        if len(control_points) < 3:
            return None
        
        try:
            # Extract coordinates
            image_coords = np.array([(cp.image_x, cp.image_y) for cp in control_points])
            world_coords = np.array([(cp.world_x, cp.world_y) for cp in control_points])
            
            # For simple affine transformation, we need at least 3 points
            # Use least squares to solve for affine transformation parameters
            # x_world = a*x_img + b*y_img + c
            # y_world = d*x_img + e*y_img + f
            
            n_points = len(control_points)
            
            # Build coefficient matrix for X coordinates
            A = np.ones((n_points, 3))
            A[:, 0] = image_coords[:, 0]  # x_img
            A[:, 1] = image_coords[:, 1]  # y_img
            
            # Solve for x_world = A * [a, b, c]
            x_coeffs = np.linalg.lstsq(A, world_coords[:, 0], rcond=None)[0]
            
            # Solve for y_world = A * [d, e, f]  
            y_coeffs = np.linalg.lstsq(A, world_coords[:, 1], rcond=None)[0]
            
            # Convert to GDAL geotransform format
            # geotransform = [x_min, pixel_width, rotation, y_max, rotation, pixel_height]
            # For affine: x_world = GT[0] + x_pixel*GT[1] + y_pixel*GT[2]
            #            y_world = GT[3] + x_pixel*GT[4] + y_pixel*GT[5]
            
            geotransform = [
                x_coeffs[2],  # x_min (c)
                x_coeffs[0],  # pixel_width (a) 
                x_coeffs[1],  # x_rotation (b)
                y_coeffs[2],  # y_max (f)
                y_coeffs[0],  # y_rotation (d)
                y_coeffs[1]   # pixel_height (e)
            ]
            
            return geotransform
            
        except Exception as e:
            print(f"Error calculating transform: {e}")
            return None
    
    def warp_image_with_control_points(self, 
                                     input_path: str, 
                                     control_points: List[ControlPoint],
                                     control_points_srs: str = "EPSG:4326") -> str:
        """
        Warp an image using control points
        
        Args:
            input_path: Path to input image
            control_points: List of control points
            control_points_srs: Target spatial reference system
            
        Returns:
            str: Path to warped image
        """
        if len(control_points) < 3:
            raise ValueError("At least 3 control points are required")
        
        # Create output path
        input_file = Path(input_path)
        output_path = self.temp_dir / f"warped_{uuid.uuid4().hex[:8]}_{input_file.name}"
        
        # Open input dataset
        src_ds = gdal.Open(input_path)
        if src_ds is None:
            raise ValueError("Cannot open input file")
        
        # Get geotransform and projection from the input file
        input_geotransform = src_ds.GetGeoTransform()
        input_projection = src_ds.GetProjection()
        
        print(f"Input file geotransform: {input_geotransform}")
        print(f"Input file projection: {input_projection}")
        
        # Set up coordinate transformation from whatever user provided to image CRS
        src_srs = osr.SpatialReference()
        src_srs.ImportFromEPSG(int(control_points_srs.split(':')[1]))
        
        dst_srs = osr.SpatialReference()
        if not input_projection:
            raise ValueError("Input file has no projection")

        # Image has a projection, use it
        dst_srs.ImportFromWkt(input_projection)
        print("Using image's native projection for coordinate transformation")

        
        # Create coordinate transformation
        coord_transform = osr.CoordinateTransformation(src_srs, dst_srs)
        
        # Create GCP list using GDAL coordinate transformation
        gcps = []
        for i, cp in enumerate(control_points):
            print(f"Control Point {i}: Original coords lon/lat ({cp.image_x}, {cp.image_y})")
            
            # Transform lat/lon to image CRS
            x_geo, y_geo, _ = coord_transform.TransformPoint(cp.image_y, cp.image_x)
            print(f"Control Point {i}: Transformed to image CRS ({x_geo}, {y_geo})")
            
            # Convert geo coordinates to pixel coordinates using geotransform
            # With corrected geotransform: Geo (x_min, y_max) = Pixel (0,0)
            # Straightforward conversion formulas:
            x_min = input_geotransform[0]
            pixel_size_x = input_geotransform[1]
            y_max = input_geotransform[3]
            pixel_size_y = abs(input_geotransform[5])  # Make positive for calculation
            
            pixel_x = int((x_geo - x_min) / pixel_size_x)
            pixel_y = int((y_max - y_geo) / pixel_size_y)   # no negative division anymore
            
            print(f"Control Point {i}: Geo ({x_geo}, {y_geo}) -> Pixel ({pixel_x}, {pixel_y})")
            print(f"  Conversion: X = ({x_geo} - {x_min}) / {pixel_size_x} = {pixel_x}")
            print(f"  Conversion: Y = ({y_max} - {y_geo}) / {pixel_size_y} = {pixel_y}")
            
            # Create GCP with world coordinates in EPSG:4326
            gcp = gdal.GCP(cp.world_x, cp.world_y, 0, pixel_x, pixel_y, f"gcp_{i}")
            gcps.append(gcp)
        
        # Assign GCPs to a virtual copy (don’t mutate src_ds directly)
        tmp_vrt = gdal.Translate(
            "", src_ds,
            format="VRT",
            GCPs=gcps,
            outputSRS='EPSG:4326'
        )
        
        # Create warping options
        warp_options = gdal.WarpOptions(
            format='GTiff',
            dstSRS='EPSG:3857',
            resampleAlg=gdal.GRA_Bilinear,
            errorThreshold=0.125,
            creationOptions=['COMPRESS=LZW', 'TILED=YES']
        )
        
        # Perform warping
        print(f"Attempting to warp image to: {output_path}")
        print(f"Input file exists: {os.path.exists(input_path)}")
        print(f"Input file path: {input_path}")
        print(f"Temp directory path: {self.temp_dir}")
        print(f"Temp directory exists: {self.temp_dir.exists()}")
        print(f"Temp directory is writable: {os.access(str(self.temp_dir), os.W_OK)}")
        print(f"Current working directory: {os.getcwd()}")
        
        # List files in temp directory before warping
        if self.temp_dir.exists():
            temp_files = list(self.temp_dir.glob('*'))
            print(f"Files in temp directory before warping: {temp_files}")
        
        warped_ds = gdal.Warp(str(output_path), tmp_vrt, options=warp_options)
        if warped_ds is None:
            raise ValueError("Warping failed")
        
        if warped_ds is None:
            print("GDAL Warp returned None - warping failed")
            raise ValueError("Warping failed")
        
        print("GDAL Warp completed successfully")
        
        # Close datasets
        src_ds = None
        warped_ds = None
        
        # List files in temp directory after warping
        if self.temp_dir.exists():
            temp_files = list(self.temp_dir.glob('*'))
            print(f"Files in temp directory after warping: {temp_files}")
        
        # Verify the output file was created
        if not os.path.exists(str(output_path)):
            print(f"ERROR: Warped file was not created at expected location: {output_path}")
            # Try to find the file elsewhere
            potential_locations = [
                f"./warped_{output_path.name}",
                f"/app/warped_{output_path.name}",
                f"/opt/shared/temp/{output_path.name}"
            ]
            for location in potential_locations:
                if os.path.exists(location):
                    print(f"Found warped file at unexpected location: {location}")
            raise ValueError(f"Warped file was not created at: {output_path}")
        
        file_size = os.path.getsize(str(output_path))
        print(f"Warped file created successfully: {output_path} (size: {file_size} bytes)")
        
        return str(output_path)
            
    
    def create_preview_image(self, file_path: str, max_size: Tuple[int, int] = (512, 512)) -> str:
        """
        Create a preview image for display in the web interface
        
        Args:
            file_path: Path to the source image
            max_size: Maximum dimensions for the preview
            
        Returns:
            str: Path to the preview image
        """
        try:
            # Create output path
            input_file = Path(file_path)
            output_path = self.temp_dir / f"preview_{uuid.uuid4().hex[:8]}_{input_file.stem}.png"
            
            # Open input dataset
            src_ds = gdal.Open(file_path)
            if src_ds is None:
                raise ValueError("Cannot open input file")
            
            # Calculate preview dimensions
            src_width = src_ds.RasterXSize
            src_height = src_ds.RasterYSize
            
            # Calculate scale to fit within max_size while maintaining aspect ratio
            scale_x = max_size[0] / src_width
            scale_y = max_size[1] / src_height
            scale = min(scale_x, scale_y)
            
            preview_width = int(src_width * scale)
            preview_height = int(src_height * scale)
            
            # Create preview using GDAL translate
            translate_options = gdal.TranslateOptions(
                format='PNG',
                width=preview_width,
                height=preview_height,
                resampleAlg=gdal.GRA_Bilinear
            )
            
            preview_ds = gdal.Translate(str(output_path), src_ds, options=translate_options)
            
            if preview_ds is None:
                raise ValueError("Preview creation failed")
            
            # Close datasets
            src_ds = None
            preview_ds = None
            
            return str(output_path)
            
        except Exception as e:
            raise ValueError(f"Error creating preview: {e}")
    
    def validate_control_points(self, control_points: List[ControlPoint]) -> Dict[str, Any]:
        """
        Validate control points and calculate transformation accuracy
        
        Args:
            control_points: List of control points
            
        Returns:
            dict: Validation results including errors and warnings
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        if len(control_points) < 3:
            result['valid'] = False
            result['errors'].append("At least 3 control points are required")
            return result
        
        try:
            # Check for duplicate points
            image_coords = [(cp.image_x, cp.image_y) for cp in control_points]
            world_coords = [(cp.world_x, cp.world_y) for cp in control_points]
            
            if len(set(image_coords)) != len(image_coords):
                result['warnings'].append("Duplicate image coordinates detected")
            
            if len(set(world_coords)) != len(world_coords):
                result['warnings'].append("Duplicate world coordinates detected")
            
            # Calculate transformation and residuals
            geotransform = self.calculate_transform_from_control_points(control_points)
            
            if geotransform is None:
                result['valid'] = False
                result['errors'].append("Cannot calculate transformation from control points")
                return result
            
            # Calculate residuals
            residuals = []
            for cp in control_points:
                # Apply transformation to image coordinates
                x_calc = geotransform[0] + cp.image_x * geotransform[1] + cp.image_y * geotransform[2]
                y_calc = geotransform[3] + cp.image_x * geotransform[4] + cp.image_y * geotransform[5]
                
                # Calculate residual
                dx = x_calc - cp.world_x
                dy = y_calc - cp.world_y
                residual = math.sqrt(dx*dx + dy*dy)
                residuals.append(residual)
            
            # Calculate statistics
            result['statistics'] = {
                'mean_residual': np.mean(residuals),
                'max_residual': np.max(residuals),
                'std_residual': np.std(residuals),
                'rmse': math.sqrt(np.mean([r*r for r in residuals]))
            }
            
            # Add warnings based on residuals
            if result['statistics']['rmse'] > 100:  # meters for geographic coordinates
                result['warnings'].append(f"High RMSE: {result['statistics']['rmse']:.2f}")
            
            if result['statistics']['max_residual'] > 500:
                result['warnings'].append(f"High maximum residual: {result['statistics']['max_residual']:.2f}")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {e}")
        
        return result
    
    
    def load_control_points(self, file_path: str) -> List[ControlPoint]:
        """
        Load control points from a JSON file
        
        Args:
            file_path: Path to the control points file
            
        Returns:
            list: List of control points
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return [ControlPoint.from_dict(cp_data) for cp_data in data['control_points']]
            
        except Exception as e:
            raise ValueError(f"Error loading control points: {e}")
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Clean up temporary files older than specified age
        
        Args:
            max_age_hours: Maximum age of files to keep
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for temp_file in self.temp_dir.glob("*"):
            try:
                if temp_file.is_file():
                    file_age = current_time - temp_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        temp_file.unlink()
                        print(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                print(f"Error cleaning up {temp_file}: {e}")
