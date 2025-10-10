"""
Background tasks package for the tagger application
"""

# Import all tasks to make them available when importing the package
from .geo import convert_to_geo_raster_task, apply_georeferencing_task
from .common import cancel_task

__all__ = [
    'convert_to_geo_raster_task',
    'apply_georeferencing_task',
    'cancel_task'
]
