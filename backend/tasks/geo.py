"""
Geo-related background tasks
"""
import asyncio
from typing import Dict, Any

from tortoise import Tortoise

from celery_app import celery_app
from .common import init_database, close_database


from mapserver_service import MapServerService

mapserver = MapServerService()


@celery_app.task(bind=True, name="tasks.convert_to_geo_raster_task")
def convert_to_geo_raster_task(self, tree_item_id: str, upload_dir: str = "uploads") -> Dict[str, Any]:
    """
    Background task to convert a RawFile to GeoRasterFile
    
    Args:
        tree_item_id: UUID string of the TreeItem to convert
        upload_dir: Directory for uploads
        
    Returns:
        Dict with task result information
    """
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting conversion", "progress": 0}
        )
        
        # Run the async conversion in an event loop
        result = asyncio.run(_convert_to_geo_raster_async(tree_item_id, upload_dir, self))
        
        return {
            "status": "SUCCESS",
            "tree_item_id": tree_item_id,
            "result": result
        }
        
    except Exception as exc:
        # Log the error for debugging
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Task failed with error: {str(exc)}")
        print(f"Traceback: {error_traceback}")
        
        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={
                "status": "FAILED",
                "error": str(exc),
                "tree_item_id": tree_item_id,
                "traceback": error_traceback
            }
        )
        raise


async def _convert_to_geo_raster_async(tree_item_id: str, upload_dir: str, task_instance) -> Dict[str, Any]:
    """
    Async implementation of the geo-raster conversion
    
    Args:
        tree_item_id: UUID string of the TreeItem to convert
        upload_dir: Directory for uploads
        task_instance: Celery task instance for progress updates
        
    Returns:
        Dict with conversion result
    """
    await init_database()
    
    try:
        # Import required modules after database initialization
        from models import TreeItem, RawFile, GeoRasterFile
        from models_factory import convert_to_geo_raster
        from services.geo import analyze_raster_file
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Loading file", "progress": 10}
        )
        
        # Get the tree item and raw file
        tree_item = await TreeItem.get_or_none(id=tree_item_id)
        if not tree_item:
            raise ValueError(f"TreeItem with id {tree_item_id} not found")
        
        raw_file = await tree_item.get_object()
        if not raw_file or not isinstance(raw_file, RawFile):
            raise ValueError(f"RawFile not found for TreeItem {tree_item_id}")
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Analyzing file", "progress": 20}
        )
        
        # Analyze the raster file to make sure it's GDAL compatible
        analysis = analyze_raster_file(raw_file.file_path)
        if not analysis["gdal_compatible"]:
            raise ValueError(f"File is not GDAL compatible: {analysis.get('error', 'Unknown error')}")
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Creating georeferenced file", "progress": 40}
        )
        
        # Create progress callback that updates Celery task progress
        def progress_callback(progress, message):
            # Map overall progress (0.0-1.0) to task progress (40-80)
            task_progress = 40 + int(progress * 40)
            task_instance.update_state(
                state="PROGRESS",
                meta={"status": message, "progress": task_progress}
            )
        
        # Perform the conversion
        geo_raster_file_obj = await convert_to_geo_raster(
            raw_file, upload_dir, progress_callback=progress_callback)
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Updating database", "progress": 80}
        )
        
        # Ensure the new geo raster file is marked as not georeferenced initially
        geo_raster_file_obj.is_georeferenced = False
        await geo_raster_file_obj.save()
        
        # Update TreeItem to point to GeoRasterFile
        tree_item.object_type = "geo_raster_file"
        tree_item.object_id = geo_raster_file_obj.id
        await tree_item.save()
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Conversion complete", "progress": 100}
        )
        
        return {
            "tree_item_id": tree_item_id,
            "geo_raster_file_id": str(geo_raster_file_obj.id),
            "object_type": "geo_raster_file",
            "is_georeferenced": False
        }
        
    finally:
        await close_database()


@celery_app.task(bind=True, name="tasks.apply_georeferencing_task")
def apply_georeferencing_task(self, tree_item_id: str, control_points_data: list, control_points_srs: str = "EPSG:4326") -> Dict[str, Any]:
    """
    Background task to apply georeferencing to a GeoRasterFile
    
    Args:
        tree_item_id: UUID string of the TreeItem to georeference
        control_points_data: List of control point dictionaries
        control_points_srs: Spatial reference system for control points
        
    Returns:
        Dict with task result information
    """
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"status": "Starting georeferencing", "progress": 0}
        )
        
        # Run the async georeferencing in an event loop
        result = asyncio.run(_apply_georeferencing_async(tree_item_id, control_points_data, control_points_srs, self))
        
        return {
            "status": "SUCCESS",
            "tree_item_id": tree_item_id,
            "result": result
        }
        
    except Exception as exc:
        # Log the error for debugging
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Georeferencing task failed with error: {str(exc)}")
        print(f"Traceback: {error_traceback}")
        
        # Update task state with error
        self.update_state(
            state="FAILURE",
            meta={
                "status": "FAILED",
                "error": str(exc),
                "tree_item_id": tree_item_id,
                "traceback": error_traceback
            }
        )
        raise


async def _apply_georeferencing_async(tree_item_id: str, control_points_data: list, control_points_srs: str, task_instance) -> Dict[str, Any]:
    """
    Async implementation of the georeferencing application
    
    Args:
        tree_item_id: UUID string of the TreeItem to georeference
        control_points_data: List of control point dictionaries
        control_points_srs: Spatial reference system for control points
        task_instance: Celery task instance for progress updates
        
    Returns:
        Dict with georeferencing result
    """
    await init_database()
    
    try:
        # Import required modules after database initialization
        from models import TreeItem, GeoRasterFile
        from services import georeference
        import os
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Loading file", "progress": 10}
        )
        
        # Get the tree item and geo raster file
        tree_obj = await TreeItem.get_or_none(id=tree_item_id, object_type="geo_raster_file")
        if not tree_obj:
            raise ValueError(f"TreeItem with id {tree_item_id} not found")
        
        geo_raster_file = await tree_obj.get_object()
        if not geo_raster_file or not isinstance(geo_raster_file, GeoRasterFile):
            raise ValueError(f"GeoRasterFile not found for TreeItem {tree_item_id}")
        
        file_path = geo_raster_file.file_path
        if not os.path.exists(file_path):
            raise ValueError(f"File not found on disk: {file_path}")
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Validating control points", "progress": 20}
        )
        
        # Convert control points data to ControlPoint objects
        control_points = [
            georeference.ControlPoint(cp["image_x"], cp["image_y"], cp["world_x"], cp["world_y"])
            for cp in control_points_data
        ]
        
        # Validate control points
        validation_results = georeference.validate_control_points(control_points)
        
        if not validation_results['valid']:
            raise ValueError(f"Invalid control points: {validation_results['errors']}")
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Creating georeferenced file", "progress": 40}
        )
        
        # Create the final georeferenced file
        georeferenced_path = georeference.warp_image_with_control_points(
            file_path,
            control_points,
            control_points_srs
        )
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Updating map configuration", "progress": 70}
        )
        
        # Save old file path for cleanup
        old_file_path = file_path
        
        # Regenerate map config to clear cache on mapserver
        map_config_path = mapserver._create_map_config(georeferenced_path)
        geo_raster_file.map_config_path = map_config_path
        geo_raster_file.file_path = georeferenced_path
        geo_raster_file.is_georeferenced = True
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Saving changes", "progress": 90}
        )
        
        await geo_raster_file.save()
        
        # Clean up old file if it's different from the original
        if os.path.exists(old_file_path) and old_file_path != geo_raster_file.original_file_path:
            os.remove(old_file_path)
        
        # Update progress
        task_instance.update_state(
            state="PROGRESS",
            meta={"status": "Georeferencing complete", "progress": 100}
        )
        
        return {
            "tree_item_id": tree_item_id,
            "geo_raster_file_id": str(geo_raster_file.id),
            "is_georeferenced": True,
            "validation_results": validation_results
        }
        
    finally:
        await close_database()
