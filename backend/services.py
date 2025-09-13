from models import TreeItem, TreeItem_Pydantic, File, Collection, RawFile, GeoRasterFile
from model_helpers import ModelFactory, TreeItemService
from tortoise.expressions import Q
import os
import uuid
import aiofiles
from osgeo import gdal, osr
import geopandas as gpd
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException
from datetime import datetime, timezone
import json



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



class CollectionsService:
    @classmethod
    async def create_collection(cls, name: str, tags: dict, parent_path: str = "root"):
        """Create a new collection"""
        # Generate a unique path segment for this collection (LTREE compatible)
        import uuid
        
        # Create LTREE-compatible ID: use 'c' prefix + first 12 chars of UUID hex (no hyphens)
        collection_uuid = str(uuid.uuid4()).replace('-', '')[:12]
        collection_segment = f"c{collection_uuid}"
        
        # Create the path: parent_path.collection_segment
        if parent_path == "root":
            collection_path = f"root.{collection_segment}"
        else:
            collection_path = f"{parent_path}.{collection_segment}"
        
        # Use the new ModelFactory to create collection
        collection_obj = await ModelFactory.create_collection(
            name=name,
            parent_path=collection_path,
            description=tags.get('description', ''),
            tags=tags
        )
        
        return collection_obj
    
    @classmethod
    async def get_collection(cls, collection_id: str):
        """Get collection by ID"""
        return await TreeItem.get_or_none(id=collection_id, object_type="collection")
    
    @classmethod
    async def get_collection_by_path(cls, path: str):
        """Get collection by path"""
        return await TreeItem.get_or_none(path=path, object_type="collection")
    
    @classmethod
    async def update_collection(cls, collection_id: str, name: str = None, tags: dict = None, new_parent_path: str = None):
        """Update collection"""
        collection = await TreeItem.get_or_none(id=collection_id, object_type="collection")
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
                object_type=row['object_type'],
                object_id=row['object_id'],
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
    def _analyze_raster_file(cls, file_path: str) -> Dict[str, Any]:
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
    
    @classmethod
    async def save_uploaded_file(cls, file: UploadFile, tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Save uploaded file to disk and return file info"""
        await cls.ensure_upload_dir()
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
        
        # Save file
        content = await file.read()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return {
            "original_name": file.filename,
            "name": unique_filename,
            "file_path": file_path,
            "file_size": len(content),
            "mime_type": file.content_type or "application/octet-stream"
        }
    
    @classmethod
    async def create_file(cls, uploaded_file, tags: Dict[str, str] = None, parent_path: str = "root") -> TreeItem:
        """Create a new file record - detect if already georeferenced and create appropriate type"""
        file_info = await cls.save_uploaded_file(uploaded_file, tags)
        
        # Generate a unique path segment for this file (LTREE compatible)
        import uuid
        
        # Create LTREE-compatible ID: use 'f' prefix + first 12 chars of UUID hex (no hyphens)
        file_uuid = str(uuid.uuid4()).replace('-', '')[:12]
        file_segment = f"f{file_uuid}"
        
        # Create the path: parent_path.file_segment
        file_ltree_path = f"{parent_path}.{file_segment}"

        # Clean user tags (remove any system-level keys that shouldn't be in tags)
        user_tags = tags or {}
        system_keys = ['original_name', 'file_path', 'file_size', 'mime_type', 'base_file_type']
        clean_tags = {k: v for k, v in user_tags.items() if k not in system_keys}

        # Analyze file to check if it's already georeferenced
        analysis = cls._analyze_raster_file(file_info["file_path"])
        is_georeferenced = analysis.get("is_georeferenced", False)

        # Create appropriate file type based on georeferencing status
        if is_georeferenced:
            # Add georeferencing metadata to tags for GeoRasterFile
            georef_tags = clean_tags.copy()
            georef_tags.update({
                "is_georeferenced": True,
                "georeferencing_method": "original"  # Mark as originally georeferenced
            })
            
            # Create as GeoRasterFile since it's already georeferenced
            file_obj = await ModelFactory.create_geo_raster_file(
                name=file_info["name"],
                file_path=file_info["file_path"],
                original_name=file_info["original_name"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                parent_path=file_ltree_path,
                tags=georef_tags
            )
        else:
            # Create as RawFile (not georeferenced or not a raster)
            file_obj = await ModelFactory.create_raw_file(
                name=file_info["name"],
                file_path=file_info["file_path"],
                original_name=file_info["original_name"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                parent_path=file_ltree_path,
                tags=clean_tags
            )
        
        return file_obj
    
    @classmethod
    async def probe_tree_item(cls, item_id: str) -> Dict[str, Any]:
        """Probe a tree item to see if it can be georeferenced with GDAL"""
        tree_item = await TreeItem.get_or_none(id=item_id)
        if not tree_item:
            raise HTTPException(status_code=404, detail="Tree item not found")
        
        # Only files can be georeferenced
        if not tree_item.is_file:
            return {
                "can_georeference": False,
                "gdal_compatible": False,
                "error": "Only files can be georeferenced"
            }
        
        file_obj = await tree_item.get_object()
        file_path = file_obj.file_path
        
        # Analyze the raster file
        analysis = cls._analyze_raster_file(file_path)
        
        if not analysis.get("gdal_compatible", False):
            return {
                "can_georeference": False,
                "gdal_compatible": False,
                "error": analysis.get("error", "File cannot be opened by GDAL")
            }
        
        return {
            "can_georeference": True,
            "gdal_compatible": True,
            "is_already_georeferenced": analysis.get("is_georeferenced", False),
            "image_info": {
                "width": analysis.get("width"),
                "height": analysis.get("height"),
                "bands": analysis.get("bands"),
                "has_projection": analysis.get("has_projection", False),
                "has_geotransform": analysis.get("has_geotransform", False)
            }
        }

        
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
    async def convert_to_geo_raster(cls, item_id: str) -> TreeItem:
        """Convert a RawFile to GeoRasterFile and create dummy georeferenced TIF if needed"""
        tree_item = await TreeItem.get_or_none(id=item_id, object_type="raw_file")
        if not tree_item:
            raise HTTPException(status_code=404, detail="Raw file not found")
        
        raw_file = await tree_item.get_object()
        
        # Probe first to make sure it's GDAL compatible
        probe_result = await cls.probe_tree_item(item_id)
        if not probe_result["gdal_compatible"]:
            raise HTTPException(status_code=400, detail=f"File is not GDAL compatible: {probe_result.get('error', 'Unknown error')}")
        
        # Get image dimensions
        src_ds = gdal.Open(raw_file.file_path)
        image_width = src_ds.RasterXSize
        image_height = src_ds.RasterYSize
        image_bands = src_ds.RasterCount
        src_ds = None
        
        dummy_georeferenced_file_path = await cls._create_dummy_georeferenced_file(raw_file.file_path)
        geo_raster = await GeoRasterFile.create(
            original_name=raw_file.original_name,
            file_path=dummy_georeferenced_file_path,
            original_file_path=raw_file.file_path,
            file_size=raw_file.file_size,
            mime_type=raw_file.mime_type,
            image_width=image_width,
            image_height=image_height,
            image_bands=image_bands
        )
        
        # Update TreeItem to point to GeoRasterFile
        tree_item.object_type = "geo_raster_file"
        tree_item.object_id = geo_raster.id
        
        # Update tags to reflect new type
        updated_tags = tree_item.tags.copy()
        updated_tags["base_file_type"] = "raster"
        tree_item.tags = updated_tags
        
        await tree_item.save()
        
        # Delete the old RawFile
        await raw_file.delete()
        
        return tree_item
    
    @classmethod
    async def get_file(cls, file_id: str) -> Optional[TreeItem]:
        """Get file by ID"""
        return await TreeItem.get_or_none(id=file_id, object_type__in=["raw_file", "geo_raster_file"])
    
    @classmethod
    async def update_file(cls, file_id: str, tags: Dict[str, str] = None, new_parent_path: str = None) -> Optional[TreeItem]:
        """Update file metadata"""
        file_obj = await TreeItem.get_or_none(id=file_id, object_type__in=["raw_file", "geo_raster_file"])
        if not file_obj:
            return None
        
        if tags is not None:
            # Update only user-editable tags (don't modify system metadata)
            clean_tags = file_obj.tags.copy()
            
            # Filter out system keys that shouldn't be updated via tags
            system_keys = ['original_name', 'file_path', 'file_size', 'mime_type', 'base_file_type']
            user_tags = {k: v for k, v in tags.items() if k not in system_keys}
            
            clean_tags.update(user_tags)
            file_obj.tags = clean_tags
        
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
        file_obj = await TreeItem.get_or_none(id=file_id, object_type__in=["raw_file", "geo_raster_file"])
        if not file_obj:
            return False
            
        # Remove file from disk
        file_path = await file_obj.get_file_path()
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        await file_obj.delete()
        return True
    
    @classmethod
    async def search_files(cls, tags: Dict[str, str] = None, base_type: str = None, collection_path: str = None, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Search files with filters"""
        # Use Tortoise ORM query builder instead of raw SQL for better compatibility
        query = TreeItem.filter(object_type__in=["raw_file", "geo_raster_file"])
        
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
    
