# Streamlined File Upload & Georeferencing Workflow

## Overview

The file upload and georeferencing process has been completely streamlined into separate, focused steps:

## 1. 📁 **Upload** (Smart Detection)

**Endpoint**: `POST /api/v1/files`

**Behavior**: 
- Automatically detects if uploaded files are already georeferenced
- If georeferenced: creates a `GeoRasterFile` with `is_georeferenced: true`
- If not georeferenced: creates a `RawFile`
- Fast, smart upload with minimal processing

**Example**:
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('tags', JSON.stringify({title: "My Image"}));

const response = await fetch('/api/v1/files', {
    method: 'POST',
    body: formData
});
// Returns TreeItem with:
// - object_type="geo_raster_file" if already georeferenced
// - object_type="raw_file" if not georeferenced
```

## 2. 🔍 **Probe** (Check GDAL Compatibility)

**Endpoint**: `POST /api/v1/files/{file_id}/probe`

**Purpose**: Check if uploaded file can be georeferenced
- Tests GDAL compatibility
- Checks if already georeferenced
- Returns image dimensions and metadata

**Response**:
```json
{
  "can_georeference": true,
  "gdal_compatible": true,
  "is_already_georeferenced": false,
  "image_info": {
    "width": 2048,
    "height": 1536,
    "bands": 3,
    "has_projection": false,
    "has_geotransform": false
  }
}
```

## 3. 🔄 **Convert** (RawFile → GeoRasterFile)

**Endpoint**: `POST /api/v1/files/{file_id}/convert-to-geo-raster`

**Purpose**: Convert RawFile to GeoRasterFile for georeferencing
- Validates GDAL compatibility
- Creates GeoRasterFile with image metadata
- Updates TreeItem to point to new model
- Deletes old RawFile

**Returns**: Updated TreeItem with `object_type="geo_raster_file"`

## 4. 🗺️ **Georeference** (Existing Workflow)

**Endpoints**: 
- `POST /api/v1/files/{file_id}/apply-georeferencing`
- Other existing georeferencing endpoints

**Purpose**: Apply actual georeferencing with control points

## 📋 **UI Workflow**

### Step 1: Upload
```javascript
// 1. Upload file (automatically detects if georeferenced)
const uploadResult = await uploadFile(file, tags);

// Check what type was created
if (uploadResult.object_type === 'geo_raster_file') {
    // File was already georeferenced - ready for mapping!
    showMappingInterface(uploadResult.id);
} else {
    // File was uploaded as RawFile - continue with optional georeferencing workflow
    continueWithProbeAndConvert(uploadResult.id);
}
```

### Step 2: Probe & Ask User (for RawFiles)
```javascript
// 2. Probe to check if it can be georeferenced
const probeResult = await fetch(`/api/v1/files/${fileId}/probe`, {method: 'POST'});

if (probeResult.can_georeference) {
    // Show UI: "This file can be georeferenced. Would you like to prepare it for georeferencing?"
    const userWantsGeoreferencing = await askUser();
    
    if (userWantsGeoreferencing) {
        // 3. Convert to GeoRasterFile
        await fetch(`/api/v1/files/${fileId}/convert-to-geo-raster`, {method: 'POST'});
        
        // 4. Show georeferencing UI
        showGeoreferencingInterface(fileId);
    }
} else {
    // File stays as RawFile - show regular file interface
    showRegularFileInterface(fileId);
}
```

## 🎯 **Benefits**

### 1. **Intelligent Upload**
- Automatically detects already georeferenced files
- No manual conversion needed for georeferenced uploads
- Ready-to-map files are immediately available

### 2. **Better User Experience**
- Fast uploads with smart detection
- Georeferenced files skip manual workflow steps
- Optional georeferencing workflow for non-georeferenced files

### 3. **Cleaner Code**
- Single upload endpoint handles both cases
- Each step has a single responsibility
- Easier to test and maintain

### 4. **Flexible Workflow**
- Users can upload any file type
- Georeferenced files are immediately usable
- Non-georeferenced files can optionally be processed

## 🏗️ **Architecture**

```
Upload File → Smart Detection
     ↓                    ↓
   (not georeferenced)   (already georeferenced)
     ↓                    ↓
  RawFile (TreeItem)    GeoRasterFile (TreeItem)
     ↓ (user choice)      ↓
   Probe → Check GDAL     Ready for Mapping!
     ↓ (if compatible)
  Convert → GeoRasterFile
     ↓ (user applies georeferencing)
Georeference → Spatially referenced file
```

## 📁 **File States**

1. **RawFile**: Just uploaded, no georeferencing detected
2. **GeoRasterFile (not georeferenced)**: Ready for manual georeferencing
3. **GeoRasterFile (georeferenced)**: Spatially referenced and ready for mapping
   - Can be created during upload (if already georeferenced)
   - Can be created via manual georeferencing workflow

This workflow provides clear separation between file storage and geospatial processing, giving users full control over the georeferencing process.
