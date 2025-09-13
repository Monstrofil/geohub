# Georeferencing Workflow Implementation

This document describes the new comprehensive georeferencing workflow implemented for the raster file sharing system.

## Overview

The system now provides a streamlined 4-step process for uploading and georeferencing raster files:

1. **Upload** - Simple drag-and-drop file upload
2. **Georeference Check** - Automatic detection of georeferencing status
3. **Manual Georeferencing** - Interactive control point mapping (if needed)
4. **Metadata** - Comprehensive metadata collection

## Features Implemented

### Backend Services

#### 1. Georeferencing Service (`backend/georeferencing_service.py`)
- **Georeferencing Detection**: Automatically detects if raster files are already georeferenced
- **Dummy Georeferencing**: Applies temporary georeferencing for display purposes
- **Control Point Management**: Handles control point validation and transformation calculations
- **Image Warping**: Performs GDAL-based image warping using control points
- **Preview Generation**: Creates preview images for the interface
- **Validation**: Calculates transformation accuracy and residuals

#### 2. Enhanced API Endpoints (`backend/api.py`)
- `GET /files/{file_id}/georeferencing-status` - Check georeferencing status
- `POST /files/{file_id}/create-preview` - Generate preview images
- `POST /files/{file_id}/validate-control-points` - Validate control points
- `POST /files/{file_id}/apply-georeferencing` - Apply final georeferencing
- `POST /georeferencing/cleanup` - Clean up temporary files

#### 3. Enhanced MapServer Integration
- Support for temporary files from georeferencing operations
- Automatic configuration generation for warped images
- Preview URL generation for validation

### Frontend Components

#### 1. Upload Wizard (`frontend/src/components/UploadWizard.vue`)
A comprehensive multi-step upload interface:
- **Step 1**: File selection with drag-and-drop support
- **Step 2**: Georeferencing status check and options
- **Step 3**: Metadata collection with tags and descriptions

#### 2. Georeferencing Modal (`frontend/src/components/GeoreferencingModal.vue`)
Interactive split-screen georeferencing interface:
- **Left Panel**: Original image with zoom/pan controls
- **Right Panel**: Interactive map (OpenStreetMap, Satellite, Terrain)
- **Control Points**: Click-to-add control points with validation
- **Live Validation**: Real-time accuracy statistics (RMSE)
- **Preview**: Preview warped results before applying

#### 3. Enhanced File List (`frontend/src/components/FileList.vue`)
- Upload choice modal (Raster Wizard vs Regular Upload)
- Integration with both upload workflows

#### 4. Enhanced API Service (`frontend/src/services/api.js`)
- Complete georeferencing API coverage
- Progress tracking for uploads
- Blob handling for preview images

## Workflow Details

### 1. Upload Process

When a user uploads a raster file:

1. File is uploaded to the server
2. System automatically detects file type using GDAL
3. For raster files, georeferencing status is checked
4. File metadata is updated with georeferencing information

### 2. Georeferencing Detection

The system uses GDAL to check:
- Presence of valid geotransform
- Spatial reference system information
- Image dimensions and data type

### 3. Manual Georeferencing

If georeferencing is needed:

1. **Control Point Collection**: User clicks on image, then corresponding map location
2. **Validation**: System calculates transformation accuracy in real-time
3. **Preview**: User can preview the warped result
4. **Application**: Final georeferencing is applied to the original file

### 4. Control Point Algorithm

The system uses least-squares affine transformation:
- Minimum 3 control points required
- Calculates 6-parameter affine transformation
- Provides accuracy statistics (RMSE, residuals)
- Validates geometric consistency

## Technical Implementation

### Dependencies Added

**Backend:**
- GDAL 3.6.2 (already present)
- NumPy (via GeoPandas)
- Enhanced GDAL operations

**Frontend:**
- Leaflet 1.9.4 for interactive mapping
- Enhanced Vue.js components

### File Structure

```
backend/
├── georeferencing_service.py    # Core georeferencing logic
├── api.py                       # Enhanced with georeferencing endpoints
├── mapserver_service.py         # Enhanced for temp file support
├── temp/                        # Temporary files directory
└── create_temp_dir.py          # Setup script

frontend/src/components/
├── UploadWizard.vue            # New upload workflow
├── GeoreferencingModal.vue     # Split-screen georeferencing
├── FileList.vue                # Enhanced with upload choices
└── ...

frontend/src/services/
└── api.js                      # Enhanced with georeferencing methods
```

### Docker Configuration

Updated `docker-compose.yml` to mount temp directories:
- Backend temp directory mounted for processing
- MapServer temp directory mounted for serving warped files

## Usage Instructions

### 1. For Regular Users

1. **Upload a Raster File**:
   - Click "Upload" button
   - Choose "Raster Image" option
   - Drag and drop or select your raster file

2. **Georeferencing** (if needed):
   - System will detect if georeferencing is required
   - Click "Manual Georeferencing" 
   - Add control points by clicking image then map
   - Preview the result
   - Apply georeferencing

3. **Add Metadata**:
   - Fill in title (required)
   - Add description, year, source
   - Add tags for better organization

### 2. For Developers

#### Setting Up Development Environment

1. **Backend Setup**:
   ```bash
   cd backend
   python create_temp_dir.py  # Create required directories
   ```

2. **Install Frontend Dependencies**:
   ```bash
   cd frontend
   npm install  # This will install Leaflet
   ```

3. **Run with Docker**:
   ```bash
   docker-compose up --build
   ```

#### API Testing

Test georeferencing endpoints:

```bash
# Check georeferencing status
curl http://localhost:8000/api/v1/files/{file_id}/georeferencing-status

# Create preview
curl -X POST http://localhost:8000/api/v1/files/{file_id}/create-preview
```

## Performance Considerations

### Backend
- GDAL operations are CPU intensive
- Large files may require significant processing time
- Temporary files are automatically cleaned up after 24 hours

### Frontend
- Leaflet maps provide smooth interaction
- Image preview is scaled for performance
- Large control point sets may impact performance

## Error Handling

### Common Issues

1. **GDAL Errors**: Usually indicate corrupted or unsupported file formats
2. **Insufficient Control Points**: Minimum 3 points required for transformation
3. **High RMSE**: Indicates poor control point placement
4. **Memory Issues**: Large files may require server resources

### Troubleshooting

1. **Check GDAL Installation**: Ensure GDAL is properly installed with all drivers
2. **Verify File Formats**: Test with known good GeoTIFF files
3. **Control Point Quality**: Ensure points are well-distributed across the image
4. **Server Resources**: Monitor CPU and memory usage during processing

## Future Enhancements

Potential improvements for the georeferencing workflow:

1. **Automatic Control Point Detection**: Use image matching algorithms
2. **Batch Georeferencing**: Process multiple files simultaneously
3. **Advanced Transformations**: Support polynomial and spline transformations
4. **Quality Assessment**: More sophisticated accuracy metrics
5. **Undo/Redo**: Allow users to modify control points
6. **Templates**: Save control point patterns for similar images

## Security Considerations

1. **File Validation**: All uploaded files are validated for type and size
2. **Temporary File Cleanup**: Automatic cleanup prevents disk space issues
3. **Input Sanitization**: All user inputs are validated
4. **Resource Limits**: Processing is limited to prevent DoS attacks

## Integration with Existing System

The georeferencing workflow integrates seamlessly with the existing file management system:

- **File Types**: Extends existing raster/vector/raw categorization
- **Tags System**: Adds georeferencing metadata to existing tag structure
- **MapServer**: Enhances existing MapServer integration
- **API**: Extends existing REST API with new endpoints
- **UI**: Adds new components while maintaining existing design language

This implementation provides a complete, professional-grade georeferencing solution that makes raster file sharing significantly more convenient and user-friendly.
