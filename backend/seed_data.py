import asyncio
import os
from models import File
from database import init_db, close_db


async def seed_sample_data():
    """Seed the database with sample files"""
    await init_db()
    
    # Sample files with tags
    sample_files = [
        {
            "name": "sample_photo.jpg",
            "original_name": "photo.jpg",
            "file_path": "/tmp/sample_photo.jpg",
            "file_size": 1024000,
            "mime_type": "image/jpeg",
            "tags": {"type": "raster", "name": "photo.jpg"}
        },
        {
            "name": "sample_map.svg",
            "original_name": "map.svg",
            "file_path": "/tmp/sample_map.svg",
            "file_size": 512000,
            "mime_type": "image/svg+xml",
            "tags": {"type": "vector", "name": "map.svg"}
        },
        {
            "name": "sample_checkpoint.jpg",
            "original_name": "checkpoint.jpg",
            "file_path": "/tmp/sample_checkpoint.jpg",
            "file_size": 2048000,
            "mime_type": "image/jpeg",
            "tags": {"military": "checkpoint", "name": "checkpoint.jpg"}
        },
        {
            "name": "sample_trench.jpg",
            "original_name": "trench.jpg",
            "file_path": "/tmp/sample_trench.jpg",
            "file_size": 1536000,
            "mime_type": "image/jpeg",
            "tags": {"military": "trench", "name": "trench.jpg"}
        },
        {
            "name": "sample_highway.jpg",
            "original_name": "highway.jpg",
            "file_path": "/tmp/sample_highway.jpg",
            "file_size": 3072000,
            "mime_type": "image/jpeg",
            "tags": {
                "highway": "motorway",
                "name": "highway.jpg",
                "ref_road_number": "M1",
                "maxspeed": "120"
            }
        }
    ]
    
    # Create sample files
    for file_data in sample_files:
        await File.create(**file_data)
        print(f"Created sample file: {file_data['original_name']}")
    
    await close_db()
    print("Sample data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_sample_data()) 