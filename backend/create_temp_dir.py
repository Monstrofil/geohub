#!/usr/bin/env python3
"""
Simple script to create the temp directory for georeferencing operations
"""
import os
import pathlib

def main():
    # Create temp directory
    temp_dir = pathlib.Path("./temp")
    temp_dir.mkdir(exist_ok=True)
    print(f"Created temp directory: {temp_dir.absolute()}")
    
    # Create uploads directory if it doesn't exist
    uploads_dir = pathlib.Path("./uploads")
    uploads_dir.mkdir(exist_ok=True)
    print(f"Created uploads directory: {uploads_dir.absolute()}")

if __name__ == "__main__":
    main()
