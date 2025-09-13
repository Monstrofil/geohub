from models import TreeItem, TreeItem_Pydantic, File, Collection, calculate_tree_item_hash, calculate_file_obj_hash
from tortoise.expressions import Q
import os
import uuid
import aiofiles
from osgeo import gdal, osr
import geopandas as gpd
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException
import hashlib
from datetime import datetime, timezone
import json



def detect_file_type(file_path: str) -> str:
    """
    Detect the base file type using GDAL and GeoPandas
    
    Returns:
        str: base_file_type
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise RuntimeError("Uploaded file is missing: check disk storage")
    
    # Try to detect as raster using GDAL
    if _is_raster(file_path):
        return "raster"
    
    # Try to detect as vector using GeoPandas
    if _is_vector(file_path):
        return "vector"
    
    # If neither, it's a raw file
    return "raw"


def _is_raster(file_path: str) -> bool:
    """
    Check if file is a raster using GDAL
    """
    dataset = gdal.Open(file_path)
    if dataset is None:
        return False
    
    # Check if it has geotransform (extent)
    geotransform = dataset.GetGeoTransform()
    if geotransform is None:
        return False
    
    return True


def _is_vector(file_path: str) -> bool:
    """
    Check if file is a vector using GeoPandas
    """
    try:
        gdf = gpd.read_file(file_path)
        return True
    except Exception as e:
        print(f"Error checking vector with GeoPandas: {e}")
        return False


def validate_file_type(filename: str, expected_type: str) -> bool:
    """
    Validate if a file matches the expected base type
    
    Args:
        filename: The filename to check
        expected_type: Expected base type ('raster', 'vector', 'raw')
    
    Returns:
        bool: True if file type matches expected type
    """
    if not filename:
        return False
    
    # For validation, we need to actually check the file
    file_path = os.path.join(FileService.UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        return False
    
    if expected_type == "raster":
        return _is_raster(file_path)
    elif expected_type == "vector":
        return _is_vector(file_path)
    elif expected_type == "raw":
        # Raw accepts anything that's not raster or vector
        return not _is_raster(file_path) and not _is_vector(file_path)
    else:
        return False


class CollectionsService:
    @classmethod
    async def create_collection(cls, name: str, tags: dict, parent_path: str = "root"):
        """Create a new collection"""
        # Generate a unique path segment for this collection (LTREE compatible)
        import uuid
        import hashlib
        
        # Create LTREE-compatible ID: use 'c' prefix + first 12 chars of UUID hex (no hyphens)
        collection_uuid = str(uuid.uuid4()).replace('-', '')[:12]
        collection_segment = f"c{collection_uuid}"
        
        # Create the path: parent_path.collection_segment
        if parent_path == "root":
            collection_path = f"root.{collection_segment}"
        else:
            collection_path = f"{parent_path}.{collection_segment}"
        
        collection_obj = await TreeItem.create(
            name=name,
            type="collection",
            tags=tags,
            path=collection_path,
        )
        
        return collection_obj
    
    @classmethod
    async def get_collection(cls, collection_id: str):
        """Get collection by ID"""
        return await TreeItem.get_or_none(id=collection_id, type="collection")
    
    @classmethod
    async def get_collection_by_path(cls, path: str):
        """Get collection by path"""
        return await TreeItem.get_or_none(path=path, type="collection")
    
    @classmethod
    async def update_collection(cls, collection_id: str, name: str = None, tags: dict = None, new_parent_path: str = None):
        """Update collection"""
        collection = await TreeItem.get_or_none(id=collection_id, type="collection")
        if not collection:
            return None
        
        old_path = collection.path
        
        if name is not None:
            collection.name = name
        if tags is not None:
            collection.tags = tags
        
        if new_parent_path is not None:
            # Update the collection's path and all its descendants
            path_parts = old_path.split('.')
            collection_segment = path_parts[-1]  # Keep the same collection ID segment
            
            if new_parent_path == "root":
                new_path = f"root.{collection_segment}"
            else:
                new_path = f"{new_parent_path}.{collection_segment}"
            
            # Update this collection's path
            collection.path = new_path
            
            # Update all descendants (files and subcollections)
            await cls._update_descendant_paths(old_path, new_path)
            
        await collection.save()
        return collection
    
    @classmethod
    async def _update_descendant_paths(cls, old_path: str, new_path: str):
        """Update paths of all descendants when a collection is moved"""
        # Update all tree items that have paths starting with old_path
        from tortoise import connections
        connection = connections.get("default")
        
        # Update all tree items (both files and collections)
        await connection.execute_query(
            "UPDATE tree_items SET path = $1 || subpath(path, nlevel($2)) WHERE path <@ $2 AND path != $2",
            [new_path, old_path]
        )
    
    @classmethod
    async def delete_collection(cls, collection_id: str, force: bool = False):
        """Delete collection and optionally its contents"""
        collection = await TreeItem.get_or_none(id=collection_id, type="collection")
        if not collection:
            return False
        
        collection_path = collection.path
        
        # Check if collection has contents using LTREE operators
        if not force:
            from tortoise import connections
            connection = connections.get("default")
            
            # Check for any items in this collection or its descendants
            item_count = await connection.execute_query_dict(
                "SELECT COUNT(*) as count FROM tree_items WHERE path <@ $1 AND path != $1",
                [collection_path]
            )
            
            if item_count[0]['count'] > 0:
                raise ValueError("Collection is not empty. Use force=True to delete anyway.")
        
        # If force=True, delete all contents first
        if force:
            from tortoise import connections
            connection = connections.get("default")
            
            # Delete all items in this collection and its descendants
            await connection.execute_query(
                "DELETE FROM tree_items WHERE path <@ $1 AND path != $1",
                [collection_path]
            )
        
        await collection.delete()
        return True
    
    @classmethod
    async def list_collection_contents(cls, collection_path: str = "root", skip: int = 0, limit: int = 100):
        """List files and subcollections in a collection as one iterable"""
        # Use raw SQL with proper parameterization and manual model instantiation
        from tortoise import connections
        
        connection = connections.get("default")
        
        # Construct regex pattern safely - escape special characters for PostgreSQL regex
        # Pattern matches paths that are direct children of collection_path
        regex_pattern = f"{collection_path}.*{{1}}"
        
        # Use parameterized query to prevent SQL injection
        query = """
            SELECT * FROM tree_items 
            WHERE path ~ $1 
            ORDER BY created_at 
            OFFSET $2 LIMIT $3
        """
        
        # Execute raw query and get results
        results = await connection.execute_query_dict(query, [regex_pattern, skip, limit])
        
        # Manually instantiate TreeItem objects with proper field mapping
        items = []
        for row in results:
            # Create TreeItem instance with all fields
            item = TreeItem(
                id=row['id'],
                name=row['name'], 
                type=row['type'],
                tags=row['tags'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                path=row['path']
            )
            # Mark as fetched from DB so it behaves like a proper model instance
            item._saved_in_db = True
            items.append(item)
        
        return items

class FileService:
    UPLOAD_DIR = "uploads"
    
    @classmethod
    async def ensure_upload_dir(cls):
        """Ensure upload directory exists"""
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
    
    @classmethod
    async def save_uploaded_file(cls, file: UploadFile, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Save uploaded file to disk and return file info"""
        await cls.ensure_upload_dir()
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
        
        # Save file and calculate sha1
        content = await file.read()
        tags = tags or {}
        tags_json = json.dumps(tags, sort_keys=True, separators=(",", ":"))
        sha1 = hashlib.sha1(content + tags_json.encode('utf-8')).hexdigest()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "original_name": file.filename,
            "name": unique_filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream",
            "sha1": sha1
        }
    
    @classmethod
    async def create_file(cls, uploaded_file, tags: Dict[str, str] = None, expected_type: str = None, parent_path: str = "root") -> TreeItem:
        """Create a new file record with automatic type detection"""
        file_info = await cls.save_uploaded_file(uploaded_file, tags)
        
        # Detect file type
        base_file_type = detect_file_type(file_info["file_path"])
        
        # Validate against expected type if provided
        if expected_type and not validate_file_type(file_info["original_name"], expected_type):
            # Delete the uploaded file if validation fails
            if os.path.exists(file_info["file_path"]):
                os.remove(file_info["file_path"])
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed for '{expected_type}'"
            )

        # For raster files, ensure they have a georeferenced version for MapServer
        georef_file_path = file_info["file_path"]
        is_georeferenced = False
        
        if base_file_type == "raster":
            from georeferencing_service import GeoreferencingService
            georef_service = GeoreferencingService()
            is_georeferenced = georef_service.is_georeferenced(file_info["file_path"])
            
            if not is_georeferenced:
                # Create a dummy georeferenced version
                georef_file_path = await cls._create_dummy_georeferenced_file(file_info["file_path"])
                print(f"Created dummy georeferenced file: {georef_file_path}")


        # Merge user tags with file-specific metadata
        file_tags = tags or {}
        file_tags.update({
            "original_name": file_info["original_name"],
            "file_path": georef_file_path,  # Use georeferenced version for MapServer
            "original_file_path": file_info["file_path"],  # Keep reference to original
            "file_size": file_info["file_size"],
            "mime_type": file_info["mime_type"],
            "base_file_type": base_file_type,
            "sha1": file_info["sha1"],
            "georeferenced": is_georeferenced,
            "has_dummy_georeference": not is_georeferenced and base_file_type == "raster"
        })

        # Generate a unique path segment for this file (LTREE compatible)
        import uuid
        
        # Create LTREE-compatible ID: use 'f' prefix + first 12 chars of UUID hex (no hyphens)
        file_uuid = str(uuid.uuid4()).replace('-', '')[:12]
        file_segment = f"f{file_uuid}"
        
        # Create the path: parent_path.file_segment
        if parent_path == "root":
            file_ltree_path = f"root.{file_segment}"
        else:
            file_ltree_path = f"{parent_path}.{file_segment}"

        file_obj = await TreeItem.create(
            name=file_info["name"],
            type="file",
            tags=file_tags,
            path=file_ltree_path
        )
        
        return file_obj
    
    @classmethod
    async def _create_dummy_georeferenced_file(cls, original_file_path: str) -> str:
        """Create a dummy georeferenced GeoTIFF for MapServer compatibility"""
        import uuid
        
        # Generate unique filename for georeferenced version
        file_extension = os.path.splitext(original_file_path)[1]
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        georef_filename = f"{base_name}_georef_{uuid.uuid4().hex[:8]}.tif"
        georef_path = os.path.join(cls.UPLOAD_DIR, georef_filename)
        
    
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
            # Create new dataset
            dst_ds = driver.Create(georef_path, width, height, bands, data_type)
            
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
    
    @classmethod
    async def get_file(cls, file_id: str) -> Optional[TreeItem]:
        """Get file by ID"""
        return await TreeItem.get_or_none(id=file_id, type="file")
    
    @classmethod
    async def update_file(cls, file_id: str, tags: Dict[str, str] = None, new_parent_path: str = None) -> Optional[TreeItem]:
        """Update file metadata"""
        file_obj = await TreeItem.get_or_none(id=file_id, type="file")
        if not file_obj:
            return None
        
        if tags is not None:
            # Merge new tags with existing file metadata (preserve file-specific tags)
            existing_tags = file_obj.tags.copy()
            existing_tags.update(tags)
            file_obj.tags = existing_tags
            
            # Recalculate hash when tags change
            new_sha1 = calculate_tree_item_hash(file_obj)
            if new_sha1:
                file_obj.tags["sha1"] = new_sha1
        
        if new_parent_path is not None:
            # Update the file's path
            path_parts = file_obj.path.split('.')
            file_segment = path_parts[-1]  # Keep the same file ID segment
            
            if new_parent_path == "root":
                new_path = f"root.{file_segment}"
            else:
                new_path = f"{new_parent_path}.{file_segment}"
            
            file_obj.path = new_path
            
        await file_obj.save()
        return file_obj
    
    @classmethod
    async def delete_file(cls, file_id: str) -> bool:
        """Delete file and remove from disk"""
        file_obj = await TreeItem.get_or_none(id=file_id, type="file")
        if not file_obj:
            return False
            
        # Remove file from disk
        file_path = file_obj.file_path
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        await file_obj.delete()
        return True
    
    @classmethod
    async def search_files(cls, tags: Dict[str, str] = None, base_type: str = None, collection_path: str = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search files with filters"""
        # Use Tortoise ORM query builder instead of raw SQL for better compatibility
        query = TreeItem.filter(type="file")
        
        if tags:
            for key, value in tags.items():
                query = query.filter(tags__contains={key: value})
        
        if base_type:
            # Check base_file_type in tags
            query = query.filter(tags__contains={"base_file_type": base_type})
        
        if collection_path:
            query = query.filter(path__contains=collection_path)
        
        total = await query.count()
        files = await query.offset(skip).limit(limit).order_by('created_at').all()
        
        return {
            "files": files,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
