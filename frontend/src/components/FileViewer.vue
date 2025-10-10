<template>
  <div class="file-viewer">
    <!-- Header with back button -->
    <div class="viewer-header">
      <button class="back-btn" @click="goBack">
        <svg width="16" height="16" viewBox="0 0 16 16">
          <path d="M10 2L4 8L10 14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Назад до списку
      </button>
      <div class="header-actions">
        <router-link v-if="isAuthenticated" :to="{name: 'FileEditor', query: { id: props.treeItemId }}" class="edit-btn">
          <svg width="16" height="16" viewBox="0 0 16 16">
            <path d="M11 1L15 5L5 15H1V11L11 1Z" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M8 4L12 8" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Редагувати
        </router-link>
        <router-link v-else :to="loginUrl" class="login-btn">
          <svg width="16" height="16" viewBox="0 0 16 16">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="16,17 21,12 16,7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Увійти щоб редагувати
        </router-link>
      </div>
    </div>

    <!-- File info section moved below header -->
    <div class="file-info-header" v-if="file">
      <div class="file-info">
        <div class="file-icon" v-html="fileIcon"></div>
        <div class="file-details">
          <h1 class="file-name">{{ getDisplayName() }}</h1>
          <div class="file-meta">
            <span class="file-type">{{ fileTypeLabel }}</span>
            <span class="file-size" v-if="getFileSize(file)">{{ formatFileSize(getFileSize(file)) }}</span>
            <span class="file-date" v-if="file?.created_at">{{ formatDate(file.created_at) }}</span>
            <span class="file-id" v-if="file?.id">ID: {{ file.id }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="viewer-content">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading file...</p>
      </div>
      
      <div v-else-if="error" class="error">
        <i class="fas fa-exclamation-triangle"></i>
        <h3>Error Loading File</h3>
        <p>{{ error }}</p>
        <button @click="loadFile" class="retry-btn">Try Again</button>
      </div>
      
      <div v-else-if="!file" class="not-found">
        <i class="fas fa-file-excel"></i>
        <h3>File Not Found</h3>
        <p>The requested file could not be found.</p>
        <button @click="goBack" class="back-btn">Go Back</button>
      </div>
      
      <div v-else-if="hasActiveTasks" class="task-content">
        <TaskStatusDisplay 
          :file-id="file.id"
          :tasks="fileTasks"
          @task-completed="handleTaskCompleted"
          @refresh-requested="handleRefreshRequested"
        />
      </div>
      
      <div v-else class="file-content">
        <div class="content-layout">
          <!-- Left panel: Main content -->
          <div class="content-main">
            <!-- Collection viewer -->
            <div v-if="file.object_type === 'tree'" class="collection-viewer">
              <div class="collection-info">
                <h3>Collection: {{ file.name || 'Untitled Collection' }}</h3>
                <p class="collection-description">
                  This is a collection containing {{ file.entries?.length || 0 }} items.
                </p>
                <div class="collection-stats">
                  <div class="stat-item">
                    <span class="stat-label">Items:</span>
                    <span class="stat-value">{{ file.entries?.length || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Created:</span>
                    <span class="stat-value">{{ formatDate(file.created_at) }}</span>
                  </div>
                </div>
              </div>
              
              <div class="collection-content">
                <p>This is a collection of files. You can view the contents below.</p>
                
                <!-- Collection files list -->
                <CollectionFilesList 
                  :collection-id="props.treeItemId"
                  @files-updated="handleCollectionFilesUpdated"
                  ref="collectionFilesList"
                />
              </div>
            </div>
            
            <!-- File viewer -->
            <div v-else class="file-viewer">
            <!-- Layer controls filter block - for georeferenced files -->
            <div v-if="file && isFileGeoreferenced" class="layer-filter-block">
                <div class="filter-header" @click="toggleLayerPanel">
                  <div class="filter-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" class="filter-icon">
                      <path d="M12 16l-6-6h12l-6 6z" fill="currentColor"/>
                      <path d="M12 10l-6-6h12l-6 6z" fill="currentColor" opacity="0.6"/>
                      <path d="M12 4l-6-6h12l-6 6z" fill="currentColor" opacity="0.3"/>
                    </svg>
                    <span>Map Layers</span>
                  </div>
                  <button class="filter-toggle" :class="{ 'expanded': layerPanelOpen }">
                    <svg width="16" height="16" viewBox="0 0 24 24">
                      <path d="M6 9l6 6 6-6" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
                
                <div v-show="layerPanelOpen" class="filter-content">
                  <div class="layer-controls-grid">
                    <!-- Base Map Layer -->
                    <div class="layer-filter-item">
                      <label class="layer-filter-label">
                        <input 
                          type="checkbox" 
                          v-model="layers.baseMap.visible"
                          @change="toggleLayer('osm-tiles', layers.baseMap.visible)"
                          class="layer-filter-checkbox"
                        />
                        <span class="layer-filter-name">Base Map</span>
                      </label>
                      <div class="layer-description">OpenStreetMap background tiles</div>
                      
                      <!-- Opacity slider for Base Map layer -->
                      <div class="layer-opacity-section">
                        <label class="opacity-section-label">Opacity: {{ Math.round(layers.baseMap.opacity * 100) }}%</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1"
                          v-model="layers.baseMap.opacity"
                          @input="updateLayerOpacity('osm-tiles', layers.baseMap.opacity)"
                          class="layer-filter-opacity-slider"
                          :disabled="!layers.baseMap.visible"
                        />
                      </div>
                    </div>
                    
                    <!-- GeoTIFF Layer -->
                    <div class="layer-filter-item">
                      <label class="layer-filter-label">
                        <input 
                          type="checkbox" 
                          v-model="layers.geotiff.visible"
                          @change="toggleLayer('geotiff-layer', layers.geotiff.visible)"
                          class="layer-filter-checkbox"
                        />
                        <span class="layer-filter-name">{{ file.name || 'Georeferenced File' }}</span>
                      </label>
                      <div class="layer-description">Uploaded georeferenced overlay</div>
                      
                      <!-- Opacity slider for GeoTIFF layer -->
                      <div class="layer-opacity-section">
                        <label class="opacity-section-label">Opacity: {{ Math.round(layers.geotiff.opacity * 100) }}%</label>
                        <input 
                          type="range" 
                          min="0" 
                          max="1" 
                          step="0.1"
                          v-model="layers.geotiff.opacity"
                          @input="updateLayerOpacity('geotiff-layer', layers.geotiff.opacity)"
                          class="layer-filter-opacity-slider"
                          :disabled="!layers.geotiff.visible"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
            <!-- Interactive Map for georeferenced files -->
            <InteractiveMap 
              v-if="file && isFileGeoreferenced"
              :fileId="file.id"
              :filename="file.name"
              class="interactive-map-container"
              ref="interactiveMapRef"
            />
            
            <!-- WMS/TMS Links section for georeferenced files -->
            <div v-if="file && isFileGeoreferenced" class="map-links-section">
              <div class="links-header">
                <h3>Map Service Links</h3>
                <p>Copy these URLs to use this layer in GIS applications like QGIS, ArcGIS, or other mapping software:</p>
              </div>
              
              <div class="links-grid">
                <!-- WMS Link -->
                <div class="link-item">
                  <div class="link-header">
                    <div class="link-main-content">
                      <div class="link-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24">
                          <path d="M12 2L2 7v10c0 5.55 3.84 10 9 11 1.06.21 2.17.21 3.23 0 5.16-1 9-5.45 9-11V7l-10-5zM10 17l-5-5 1.41-1.41L10 14.17l7.59-7.58L19 8l-9 9z" fill="currentColor"/>
                        </svg>
                      </div>
                      <div class="link-info">
                        <h4>WMS (Web Map Service) <span class="type">wms</span></h4>
                        <p>Use this URL to add the layer to QGIS, ArcGIS, or other GIS applications</p>
                      </div>
                    </div>
                    <div class="remote-control-links">
                      <span class="remote-control">
                        <a :href="josmWmsUrl" title="Add WMS to JOSM" target="_blank" class="remote-control-btn">JOSM</a>
                      </span>
                      <span class="remote-control">
                        <a :href="idWmsUrl" title="Add WMS to iD" target="_blank" class="remote-control-btn">iD</a>
                      </span>
                    </div>
                  </div>
                  <div class="link-url-container">
                    <input 
                      type="text" 
                      :value="wmsUrl" 
                      readonly 
                      class="link-url"
                      ref="wmsUrlInput"
                    />
                    <button @click="copyToClipboard(wmsUrl, 'WMS URL')" class="copy-btn" title="Copy WMS URL">
                      <svg width="16" height="16" viewBox="0 0 24 24">
                        <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z" fill="currentColor"/>
                      </svg>
                    </button>
                  </div>
                  <div class="link-details">
                    <div><strong>Layer Name:</strong> geotiff_layer</div>
                    <div><strong>Best for:</strong> Adding to desktop GIS applications</div>
                  </div>
                </div>
                
                <!-- TMS Link -->
                <div class="link-item">
                  <div class="link-header">
                    <div class="link-main-content">
                      <div class="link-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24">
                          <path d="M3 3v18h18V3H3zm16 16H5V5h14v14zm-8-2h2v-2h-2v2zm0-4h2V9h-2v2zm0-4h2V5h-2v2z" fill="currentColor"/>
                        </svg>
                      </div>
                      <div class="link-info">
                        <h4>TMS (Tile Map Service) <span class="type">tms</span></h4>
                        <p>Tiled map service for web mapping applications (Google Maps style)</p>
                      </div>
                    </div>
                    <div class="remote-control-links">
                      <span class="remote-control">
                        <a :href="josmTmsUrl" title="Add TMS to JOSM" target="_blank" class="remote-control-btn">JOSM</a>
                      </span>
                      <span class="remote-control">
                        <a :href="idTmsUrl" title="Add TMS to iD" target="_blank" class="remote-control-btn">iD</a>
                      </span>
                    </div>
                  </div>
                  <div class="link-url-container">
                    <input 
                      type="text" 
                      :value="tmsUrl" 
                      readonly 
                      class="link-url"
                      ref="tmsUrlInput"
                    />
                    <button @click="copyToClipboard(tmsUrl, 'TMS URL')" class="copy-btn" title="Copy TMS URL">
                      <svg width="16" height="16" viewBox="0 0 24 24">
                        <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z" fill="currentColor"/>
                      </svg>
                    </button>
                  </div>
                  <div class="link-details">
                    <div><strong>Format:</strong> Google Maps tile scheme (TMS)</div>
                  </div>
                </div>
              </div>
              
              <!-- Copy status notification -->
              <div v-if="copyStatus" class="copy-status" :class="{ 'success': copyStatus.success, 'error': !copyStatus.success }">
                {{ copyStatus.message }}
              </div>
              
            </div>
              
              <!-- File Preview Section - displays regardless of georeferencing ability -->
              <div v-if="previewComponent" class="file-preview-section">
                <div class="file-preview-container">
                  <div class="preview-header">
                    <h3>File Preview</h3>
                  </div>
                  <component 
                    :is="previewComponent.component" 
                    :file-id="file.id"
                    :file="file"
                    @error="handlePreviewError"
                    @loaded="handlePreviewLoaded"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Right panel: Object Information -->
          <div class="content-sidebar">
            <!-- Unified Object Type and Properties section -->
            <div v-if="selectedType || (file.tags && Object.keys(file.tags).length > 0)" class="unified-properties-section">
              <h3>Object Information</h3>
              
              <!-- Object type display -->
              <div v-if="selectedType" class="object-type-display">
                <div class="preset-icon-container">
                  <span v-html="selectedType.icon" class="preset-icon"></span>
                </div>
                <div class="object-type-info">
                  <div class="object-type-name">{{ selectedType.name }}</div>
                  <div class="object-type-description">
                    {{ selectedType.description || 'Description not set' }}
                  </div>
                </div>
              </div>

              <!-- Object properties using field definitions -->
              <div v-if="file.tags && Object.keys(file.tags).length > 0" class="properties-section">
                <h4>Properties</h4>
                <div v-if="selectedFields.length > 0" class="properties-grid">
                  <div v-for="field in selectedFields" :key="field.key" class="property-item">
                    <span class="property-label">{{ field.label || field.key }}:</span>
                    <span class="property-value">{{ file.tags[field.key] || 'Not set' }}</span>
                  </div>
                </div>
                <div v-else class="tags-grid">
                  <div v-for="(value, key) in file.tags" :key="key" class="tag-item">
                    <span class="tag-key">{{ key }}:</span>
                    <span class="tag-value">{{ value }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Information section -->
            <div class="file-info-section">
              <h3>File Information</h3>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Name:</span>
                  <span class="info-value">{{ getOriginalName(file) }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Type:</span>
                  <span class="info-value">{{ fileTypeLabel }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">MIME Type:</span>
                  <span class="info-value">{{ getMimeType(file) || 'Unknown' }}</span>
                </div>
                <div class="info-item" v-if="getFileSize(file)">
                  <span class="info-label">Size:</span>
                  <span class="info-value">{{ formatSize(getFileSize(file)) }}</span>
                </div>
                <div class="info-item" v-if="file.created_at">
                  <span class="info-label">Created:</span>
                  <span class="info-value">{{ formatDate(file.created_at) }}</span>
                </div>
                <div class="info-item" v-if="file.updated_at">
                  <span class="info-label">Modified:</span>
                  <span class="info-value">{{ formatDate(file.updated_at) }}</span>
                </div>
              </div>
            </div>

            <!-- Georeferencing needed for raster files -->
            <div v-if="file && !isFileGeoreferenced" class="georeferencing-needed">
              
              <!-- Probing status -->
              <div v-if="probeLoading" class="probe-status">
                <div class="spinner"></div>
                <h3>Checking file compatibility...</h3>
                <p>Analyzing if this file can be georeferenced...</p>
              </div>

              <!-- Probe error -->
              <div v-else-if="probeError" class="probe-error">
                <div class="georef-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="30" fill="#dc3545"/>
                    <path d="M20 20l24 24M44 20l-24 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                  </svg>
                </div>
                <h3>File Analysis Failed</h3>
                <p>{{ probeError }}</p>
              </div>

              <!-- File cannot be georeferenced -->
              <div v-else-if="probeResult && !probeResult.can_georeference" class="cannot-georeference">
                <div class="no-preview-message">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#6c757d"/>
                      <path d="M20 20l24 24M44 20l-24 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <h3>Cannot Be Georeferenced</h3>
                  <p>{{ probeResult.error || 'This file is not compatible with georeferencing tools.' }}</p>
                  <p v-if="!previewComponent" class="no-preview-note">No preview is available for this file type.</p>
                </div>
              </div>

              <!-- Regular file that can be converted and georeferenced -->
              <div v-else-if="file.object_type === 'raw_file' && probeResult && probeResult.can_georeference && !isFileGeoreferenced" class="can-georeference">
                <div class="georef-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="30" fill="#28a745"/>
                    <path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h3>Ready for Georeferencing</h3>
                <p>This file can be prepared for georeferencing. We'll convert it to a geo-raster format and then open the georeferencing interface where you can add control points.</p>
                
                <div class="georef-actions">
                  <button class="btn btn-success convert-btn" @click="startConversion">
                    <svg width="24" height="24" viewBox="0 0 24 24">
                      <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    Convert & Start Georeferencing
                  </button>
                </div>
                
                <div class="file-info">
                  <p><strong>File details:</strong> {{ probeResult.image_info?.width }}×{{ probeResult.image_info?.height }} pixels, {{ probeResult.image_info?.bands }} bands</p>
                </div>
              </div>

              <!-- Geo-raster file that needs georeferencing (no conversion needed) -->
              <div v-else-if="file.object_type === 'geo_raster_file' && probeResult && probeResult.can_georeference && !isFileGeoreferenced" class="needs-georeferencing">
                <div class="georef-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="30" fill="#ffc107"/>
                    <path d="M32 16v16M32 40h0" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                    <circle cx="32" cy="32" r="2" fill="white"/>
                  </svg>
                </div>
                <h3>Georeferencing Required</h3>
                <p>This geo-raster file is ready for georeferencing. Add control points to georeference it to a map coordinate system.</p>
                
                <div class="georef-actions">
                  <button class="btn btn-primary georef-btn" @click="startGeoreferencing">
                    <svg width="24" height="24" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="12" r="2" fill="currentColor"/>
                      <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    Start Georeferencing
                  </button>
                </div>
                
                <div class="file-info">
                  <p><strong>File details:</strong> {{ probeResult.image_info?.width }}×{{ probeResult.image_info?.height }} pixels, {{ probeResult.image_info?.bands }} bands</p>
                </div>
              </div>

              <!-- File is already georeferenced (fallback case) -->
              <div v-else-if="isFileGeoreferenced" class="already-georeferenced">
                <div class="georef-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="30" fill="#17a2b8"/>
                    <path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h3>Already Georeferenced</h3>
                <p>This file already has georeferencing information. It should be displayed on the map.</p>
              </div>

              <!-- Default georeferencing option (no probe result yet) -->
              <div v-else class="default-georeferencing">
                <div class="georef-header">
                  <div class="georef-icon">
                    <svg width="64" height="64" viewBox="0 0 64 64">
                      <circle cx="32" cy="32" r="30" fill="#ffc107"/>
                      <path d="M32 16v16M32 40h0" stroke="white" stroke-width="4" fill="none" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <h3>Georeferencing Required</h3>
                  <p>This raster file needs georeferencing to be displayed on a map. Add control points to georeference it.</p>
                </div>
                
                <div class="georef-actions">
                  <button class="btn btn-primary georef-btn" @click="startGeoreferencing">
                    <svg width="24" height="24" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
                      <circle cx="12" cy="12" r="2" fill="currentColor"/>
                      <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    Start Georeferencing
                  </button>
                </div>
              </div>
              
              <div v-if="georeferencingStatus" class="georef-status">
                <div v-if="georeferencingStatus.loading" class="status-loading">
                  <div class="spinner"></div>
                  <span>Loading georeferencing interface...</span>
                </div>
                <div v-else-if="georeferencingStatus.error" class="status-error">
                  <span>Error: {{ georeferencingStatus.error }}</span>
                </div>
              </div>
            </div>

            <!-- Georeferencing Actions section for already georeferenced files -->
            <div v-if="file && isFileGeoreferenced" class="georef-actions-section">
              <h3>Georeferencing Actions</h3>
              <p>This file is already georeferenced and displayed on the map.</p>
              <div class="georef-actions">
                <button class="btn btn-warning regeoref-btn" @click="confirmResetGeoreferencing">
                  <svg width="24" height="24" viewBox="0 0 24 24">
                    <path d="M1 4v6h6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  Re-georeference
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Georeferencing Modal -->
    <GeoreferencingModal 
      v-if="showGeoreferencingModal && file"
      :file-id="file.id"
      :file-info="file.tags"
      @close="closeGeoreferencing"
      @completed="onGeoreferencingCompleted" 
    />

    <!-- Task Progress Modal -->
    <TaskProgressModal
      v-if="showTaskProgress && currentTaskId"
      :is-visible="showTaskProgress"
      title="Converting to Geo-Raster"
      :task-id="currentTaskId"
      @close="handleTaskProgressClose"
      @complete="handleTaskComplete"
      @error="handleTaskError"
    />
    
    <!-- Reset Georeferencing Confirmation Modal -->
    <div v-if="showResetConfirmation" class="modal-overlay" @click="showResetConfirmation = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Reset Georeferencing</h3>
          <button class="modal-close" @click="showResetConfirmation = false">
            <svg width="24" height="24" viewBox="0 0 24 24">
              <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="warning-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M12 9v4M12 17h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h4>Are you ready to start from scratch?</h4>
          <p>This will reset the georeferencing for this file, removing all current control points and returning it to its original state. You will need to re-add control points to georeference it again.</p>
          <p><strong>This action cannot be undone.</strong></p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showResetConfirmation = false">
            Cancel
          </button>
          <button class="btn btn-danger" @click="resetGeoreferencing" :disabled="loading">
            <div v-if="loading" class="spinner"></div>
            Reset & Start Over
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InteractiveMap from './InteractiveMap.vue'
import CollectionFilesList from './CollectionFilesList.vue'
import GeoreferencingModal from './GeoreferencingModal.vue'
import TaskProgressModal from './TaskProgressModal.vue'
import TaskStatusDisplay from './TaskStatusDisplay.vue'
import { isAuthenticated } from '../stores/auth.js'
import { matchTagsToPreset, getAllPresets } from '../utils/tagMatcher.js'
import { loadFieldDefinitions, resolveFields } from '../utils/fieldResolver.js'
import apiService from '../services/api.js'
import { getFileSize, getBaseFileType, getMimeType, getOriginalName, getDisplayName as getFileDisplayName, formatFileSize as formatSize } from '../utils/fileHelpers.js'
import { findPreviewComponent, previewComponents } from './previews/index.js'

const route = useRoute()
const router = useRouter()

// Create login URL with current path as redirect
const loginUrl = computed(() => {
  const redirectParam = encodeURIComponent(route.fullPath)
  return `/login?redirect=${redirectParam}`
})

// State
const file = ref(null)
const loading = ref(false)
const error = ref(null)

// Georeferencing state
const showGeoreferencingModal = ref(false)
const georeferencingStatus = ref(null)
const showResetConfirmation = ref(false)

// Probe state for checking if file can be georeferenced
const probeResult = ref(null)
const probeLoading = ref(false)
const probeError = ref(null)

// Task checking state
const fileTasks = ref([])
const hasActiveTasks = ref(false)
const checkingTasks = ref(false)

// Task progress modal state
const showTaskProgress = ref(false)
const currentTaskId = ref(null)

// Preview component state
const previewComponent = ref(null)
const previewComponentLoading = ref(false)

// Layer controls state
const layerPanelOpen = ref(true)
const layers = ref({
  baseMap: {
    visible: true,
    opacity: 1.0
  },
  geotiff: {
    visible: true,
    opacity: 0.8
  }
})
const interactiveMapRef = ref(null)

// Map service URLs state
const mapUrl = ref(null)
const copyStatus = ref(null)

// Field definitions and presets (reused from FileEditor)
const allPresets = ref([])
const allFieldDefinitions = ref({})
const selectedType = ref(null)

const props = defineProps({
  treeItemId: {
    type: String,
    required: true // Tree item ID for direct API access
  }
})


// Computed
const fileIcon = computed(() => {
  switch (fileType.value) {
    case 'raster':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="2" y="6" width="36" height="28" rx="4" fill="#e0e7ef" stroke="#7faaff" stroke-width="2"/>
        <circle cx="14" cy="24" r="4" fill="#7faaff"/>
        <rect x="20" y="16" width="12" height="8" fill="#b3d1ff"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#7faaff" stroke-width="1" fill="none"/>
      </svg>`
    case 'vector':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="2" y="6" width="36" height="28" rx="4" fill="#e0f7e7" stroke="#2ecc71" stroke-width="2"/>
        <circle cx="12" cy="28" r="3" fill="#2ecc71"/>
        <circle cx="28" cy="14" r="3" fill="#2ecc71"/>
        <line x1="12" y1="28" x2="28" y2="14" stroke="#27ae60" stroke-width="2"/>
        <path d="M6 6l4 4M10 6l4 4M14 6l4 4" stroke="#2ecc71" stroke-width="1" fill="none"/>
      </svg>`
    case 'raw':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="4" y="6" width="32" height="28" rx="4" fill="#f7f7e7" stroke="#6c757d" stroke-width="2"/>
        <rect x="12" y="16" width="16" height="2" fill="#6c757d"/>
        <rect x="12" y="22" width="10" height="2" fill="#6c757d"/>
        <rect x="12" y="28" width="14" height="2" fill="#6c757d"/>
      </svg>`
    case 'collection':
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="3" y="8" width="34" height="24" rx="4" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
        <path d="M3 8l4-6h12l4 6" fill="#ffe082" stroke="#ffb300" stroke-width="2"/>
        <rect x="8" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="14" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="20" y="14" width="4" height="2" fill="#ffb300"/>
        <rect x="8" y="18" width="4" height="2" fill="#ffb300"/>
        <rect x="14" y="18" width="4" height="2" fill="#ffb300"/>
        <rect x="20" y="18" width="4" height="2" fill="#ffb300"/>
      </svg>`
    default:
      return `<svg width="40" height="40" viewBox="0 0 40 40">
        <rect x="6" y="6" width="28" height="28" rx="6" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
        <path d="M12 12h16M12 16h12M12 20h8" stroke="#6c757d" stroke-width="2" fill="none"/>
      </svg>`
  }
})

// Methods

async function loadFile() {
  if (!props.treeItemId) {
    error.value = 'No tree item ID provided'
    return
  }

  loading.value = true
  error.value = null
  
  try {
    // Use direct API call with tree item ID
    const response = await apiService.getTreeItem(props.treeItemId)
    
    file.value = response
    // Store the object type for UI rendering
    file.value.object_type = response.object_type || response.type

    // Set initial type based on file tags
    if (file.value && file.value.tags) {
      const matchedPreset = matchTagsToPreset(file.value.tags, allPresets.value, file.value.object_type)
      selectedType.value = matchedPreset
    }

    // Probe file if it's not already confirmed as georeferenced
    // This includes both regular files and geo-raster files that might need georeferencing
    if (file.value && file.value.type === 'file' && !isFileGeoreferenced.value) {
      // Clear previous probe results
      probeResult.value = null
      probeError.value = null
      // Check for preview components
      checkPreviewComponent()
      // Probe the file in the background
      probeFile()
    }
    
    // Load map URL for georeferenced files
    if (file.value && file.value.object_type === 'geo_raster_file') {
      await loadMapUrl()
    }
  } catch (err) {
    console.error('Failed to load file:', err)
    error.value = err.message || 'Failed to load file'
    file.value = null
  } finally {
    loading.value = false
  }
}

function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString()
}

function goBack() {
  router.back()
}

function getDisplayName() {
  if (!file.value) return 'Untitled'
  
  if (file.value.object_type === 'tree') {
    return file.value.tags?.name || file.value.name || 'Untitled Collection'
  } else {
    return file.value.tags?.name || file.value.original_name || file.value.name || 'Untitled File'
  }
}



// File type detection and labels (reused from FileEditor)
const fileType = computed(() => {
  // Check if this is a collection first
  if (file.value?.object_type === 'tree') {
    return 'collection'
  }
  return getBaseFileType(file.value)
})

const fileTypeLabel = computed(() => {
  const labels = {
    'raster': 'Georeferenced Raster Image',
    'vector': 'Georeferenced Vector File', 
    'raw': 'Regular File',
    'collection': 'File Collection',
  }
  return labels[fileType.value] || 'Unknown Type'
})

// Check if file is georeferenced
const isFileGeoreferenced = computed(() => {
  // For geo_raster_file objects, check the is_georeferenced field from the database
  if (file.value && file.value.object_type === 'geo_raster_file' && file.value.object_details) {
    return file.value.object_details.is_georeferenced === true
  }
  
  // For other files, fall back to probe result
  if (probeResult.value && probeResult.value.can_georeference) {
    return probeResult.value.is_already_georeferenced
  }
  
  // Default to false if no conclusive information
  return false
})

// Handle collection files updates
function handleCollectionFilesUpdated(files) {
  // Update the collection entries count if needed
  if (file.value && file.value.object_type === 'tree') {
    file.value.entries = files
  }
}

// Resolve field keys to full field definitions (reused from FileEditor)
const selectedFields = computed(() => {
  if (!selectedType.value || !selectedType.value.fields) {
    return []
  }
  return resolveFields(selectedType.value.fields, allFieldDefinitions.value)
})

// WMS URL computed property (GetCapabilities)
const wmsUrl = computed(() => {
  if (!mapUrl.value) return ''
  
  // Extract base URL and MAP parameter from the mapserver URL
  const baseUrl = mapUrl.value.split('?')[0] + '?'
  const mapParam = mapUrl.value.includes('map=') ? mapUrl.value.split('map=')[1].split('&')[0] : ''
  
  if (!mapParam) return ''
  
  // Generate WMS GetCapabilities URL
  return `${baseUrl}SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&MAP=${mapParam}`
})

// TMS URL computed property  
const tmsUrl = computed(() => {
  if (!mapUrl.value) return ''
  
  // Extract base URL and MAP parameter from the mapserver URL
  const baseUrl = mapUrl.value.split('?')[0] + '?'
  const mapParam = mapUrl.value.includes('map=') ? mapUrl.value.split('map=')[1].split('&')[0] : ''
  
  if (!mapParam) return ''
  
  // Generate TMS URL with tile placeholders
  return `${baseUrl}MAP=${mapParam}&MODE=tile&TILEMODE=gmap&TILE={x}+{y}+{z}&LAYERS=geotiff_layer`
})

// JOSM Remote Control URLs
const josmWmsUrl = computed(() => {
  if (!wmsUrl.value || !file.value) return '#'
  
  const title = encodeURIComponent(file.value.name || 'GeoTIFF Layer')
  const wmsBaseUrl = wmsUrl.value.split('?')[0]
  const mapParam = wmsUrl.value.includes('MAP=') ? wmsUrl.value.split('MAP=')[1].split('&')[0] : ''
  
  if (!mapParam) return '#'
  
  const wmsGetMapUrl = encodeURIComponent(`${wmsBaseUrl}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&LAYERS=geotiff_layer&MAP=${mapParam}&SRS=EPSG:3857&FORMAT=image/png&TRANSPARENT=TRUE&BBOX={bbox}&WIDTH={width}&HEIGHT={height}`)
  
  return `http://127.0.0.1:8111/imagery?title=${title}&type=wms&url=${wmsGetMapUrl}`
})

const josmTmsUrl = computed(() => {
  if (!tmsUrl.value || !file.value) return '#'
  
  const title = encodeURIComponent(file.value.name || 'GeoTIFF Layer')
  const tmsFormatted = tmsUrl.value.replace('{x}', '{x}').replace('{y}', '{y}').replace('{z}', '{zoom}')
  const encodedUrl = encodeURIComponent(tmsFormatted)
  
  return `http://127.0.0.1:8111/imagery?title=${title}&type=tms&min_zoom=1&max_zoom=18&url=${encodedUrl}`
})

// iD Editor Remote Control URLs  
const idWmsUrl = computed(() => {
  if (!wmsUrl.value || !file.value) return '#'
  
  const wmsBaseUrl = wmsUrl.value.split('?')[0]
  const mapParam = wmsUrl.value.includes('MAP=') ? wmsUrl.value.split('MAP=')[1].split('&')[0] : ''
  
  if (!mapParam) return '#'
  
  const wmsGetMapUrl = encodeURIComponent(`${wmsBaseUrl}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=geotiff_layer&MAP=${mapParam}&SRS=EPSG:3857&FORMAT=image/png&TRANSPARENT=TRUE&BBOX={bbox}&WIDTH={width}&HEIGHT={height}`)
  
  return `https://www.openstreetmap.org/edit?editor=id&background=custom:${wmsGetMapUrl}`
})

const idTmsUrl = computed(() => {
  if (!tmsUrl.value || !file.value) return '#'
  
  const tmsFormatted = tmsUrl.value.replace('{x}', '{x}').replace('{y}', '{y}').replace('{z}', '{zoom}')
  const encodedUrl = encodeURIComponent(tmsFormatted)
  
  return `https://www.openstreetmap.org/edit?editor=id&background=custom:${encodedUrl}`
})

// Georeferencing functions
function startGeoreferencing() {
  georeferencingStatus.value = { loading: true }
  showGeoreferencingModal.value = true
}

function closeGeoreferencing() {
  showGeoreferencingModal.value = false
  georeferencingStatus.value = null
}

function onGeoreferencingCompleted(result) {
  showGeoreferencingModal.value = false
  georeferencingStatus.value = null
  
  // Update file tags to reflect georeferencing status
  if (file.value && result.fileInfo) {
    file.value.tags = { ...file.value.tags, ...result.fileInfo }
  }
  
  // Update the is_georeferenced field in the file object
  if (file.value && file.value.object_details) {
    file.value.object_details.is_georeferenced = true
  }
  
  // Force re-render to show the map
  loadFile()
}

// Reset georeferencing functions
function confirmResetGeoreferencing() {
  showResetConfirmation.value = true
}

async function resetGeoreferencing() {
  if (!file.value?.id) return
  
  loading.value = true
  
  try {
    // Call the reset-georeferencing API
    await apiService.resetGeoreferencing(file.value.id)
    
    // Close the confirmation modal
    showResetConfirmation.value = false
    
    // Update the is_georeferenced field in the file object
    if (file.value && file.value.object_details) {
      file.value.object_details.is_georeferenced = false
    }
    
    // Reload the file to reflect the changes
    await loadFile()
    
    // Now start the georeferencing process
    startGeoreferencing()
  } catch (err) {
    console.error('Failed to reset georeferencing:', err)
    alert(`Failed to reset georeferencing: ${err.message}`)
  } finally {
    loading.value = false
  }
}

// Preview component functions
function checkPreviewComponent() {
  console.log('🔍 [FileViewer] Checking preview component for file:', file.value)
  
  if (!file.value) {
    console.log('⚠️ [FileViewer] No file available for preview check')
    return
  }
  
  // Check file size - only show preview for files that aren't too large
  const fileSize = file.value.object_details?.file_size
  const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB maximum size for preview
  const isSizeAppropriate = fileSize && fileSize <= MAX_FILE_SIZE
  
  console.log('📏 [FileViewer] File size check:', {
    fileSize: fileSize,
    maxSize: MAX_FILE_SIZE,
    isSizeAppropriate: isSizeAppropriate,
    fileSizeFormatted: fileSize ? `${(fileSize / 1024 / 1024).toFixed(2)} MB` : 'unknown'
  })
  
  if (!isSizeAppropriate) {
    previewComponent.value = null
    console.log('❌ [FileViewer] File too large for preview:', fileSize, 'bytes (max:', MAX_FILE_SIZE, 'bytes)')
    return
  }
  
  const preview = findPreviewComponent(file.value)
  console.log('🔍 [FileViewer] Preview component search result:', preview)
  
  if (preview) {
    previewComponent.value = preview
    console.log('✅ [FileViewer] Found preview component:', preview.name)
  } else {
    previewComponent.value = null
    console.log('❌ [FileViewer] No preview component found for file type:', file.value.object_details?.mime_type)
    console.log('❌ [FileViewer] File details:', {
      id: file.value.id,
      name: file.value.name,
      object_type: file.value.object_type,
      mime_type: file.value.mime_type,
      'object_details.mime_type': file.value.object_details?.mime_type,
      'object_details.file_size': file.value.object_details?.file_size,
      type: file.value.type
    })
  }
}

function handlePreviewError(error) {
  console.error('❌ [FileViewer] Preview component error:', error)
  // Could show a toast notification or handle the error as needed
}

function handlePreviewLoaded() {
  console.log('✅ [FileViewer] Preview component loaded successfully')
}

// Probe functions
async function probeFile() {
  if (!file.value?.id) return

  probeLoading.value = true
  probeError.value = null
  
  try {
    const result = await apiService.probeTreeItem(file.value.id)
    probeResult.value = result
  } catch (err) {
    console.error('Failed to probe file:', err)
    probeError.value = err.message || 'Failed to probe file'
  } finally {
    probeLoading.value = false
  }
}

async function startConversion() {
  if (!file.value?.id) return

  try {
    // Start the background conversion task
    const taskResponse = await apiService.convertToGeoRaster(file.value.id)
    currentTaskId.value = taskResponse.task_id
    showTaskProgress.value = true
  } catch (err) {
    console.error('Failed to start conversion:', err)
    alert(`Failed to start conversion: ${err.message}`)
  }
}

async function handleTaskComplete(state) {
  console.log('Task completed successfully:', state)
  
  // Wait a moment to show completion
  setTimeout(async () => {
    showTaskProgress.value = false
    currentTaskId.value = null
    
    // Reload the file to get the latest state
    await loadFile()
    
    // After conversion, automatically start the georeferencing process
    startGeoreferencing()
  }, 1500)
}

function handleTaskError(state) {
  console.error('Task failed:', state)
  // Modal will show the error, user can close it manually
}

function handleTaskProgressClose() {
  showTaskProgress.value = false
  currentTaskId.value = null
}

// Layer control functions
function toggleLayerPanel() {
  layerPanelOpen.value = !layerPanelOpen.value
}

function toggleLayer(layerId, visible) {
  if (interactiveMapRef.value && interactiveMapRef.value.map) {
    const map = interactiveMapRef.value.map
    if (visible) {
      map.setLayoutProperty(layerId, 'visibility', 'visible')
    } else {
      map.setLayoutProperty(layerId, 'visibility', 'none')
    }
  }
}

function updateLayerOpacity(layerId, opacity) {
  if (interactiveMapRef.value && interactiveMapRef.value.map) {
    const map = interactiveMapRef.value.map
    if (layerId === 'geotiff-layer') {
      map.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
    } else if (layerId === 'osm-tiles') {
      map.setPaintProperty(layerId, 'raster-opacity', parseFloat(opacity))
    }
  }
}

// Map service URL functions
async function loadMapUrl() {
  if (!file.value?.id || file.value.object_type !== 'geo_raster_file') {
    mapUrl.value = null
    return
  }
  
  try {
    const response = await apiService.request(`/files/${file.value.id}/map`)
    mapUrl.value = response.map_url
  } catch (err) {
    console.error('Failed to load map URL:', err)
    mapUrl.value = null
  }
}

async function copyToClipboard(text, label) {
  if (!text) {
    copyStatus.value = { success: false, message: `${label} is not available` }
    setTimeout(() => { copyStatus.value = null }, 3000)
    return
  }
  
  try {
    await navigator.clipboard.writeText(text)
    copyStatus.value = { success: true, message: `${label} copied to clipboard!` }
  } catch (err) {
    // Fallback for older browsers
    try {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      copyStatus.value = { success: true, message: `${label} copied to clipboard!` }
    } catch (fallbackErr) {
      console.error('Failed to copy to clipboard:', fallbackErr)
      copyStatus.value = { success: false, message: `Failed to copy ${label}` }
    }
  }
  
  // Clear status after 3 seconds
  setTimeout(() => { copyStatus.value = null }, 3000)
}

// Task checking functions
async function checkFileTasks() {
  if (!file.value?.id) return
  
  checkingTasks.value = true
  try {
    const response = await apiService.getFileTasks(file.value.id)
    fileTasks.value = response.tasks || []
    hasActiveTasks.value = response.has_active_tasks || false
  } catch (error) {
    console.error('Failed to check file tasks:', error)
    fileTasks.value = []
    hasActiveTasks.value = false
  } finally {
    checkingTasks.value = false
  }
}

function handleTaskCompleted() {
  // Refresh file data when task completes
  loadFile()
}

function handleRefreshRequested() {
  // Refresh task status
  checkFileTasks()
}

// Lifecycle
onMounted(async () => {
  // Load all field definitions and presets using centralized loading
  allPresets.value = getAllPresets()
  console.log('Loaded presets:', allPresets.value)
  allFieldDefinitions.value = await loadFieldDefinitions()
  await loadFile()
  // Check for active tasks after loading file
  await checkFileTasks()
})

// Watch for prop changes
watch(() => props.treeItemId, async () => {
  await loadFile()
  await checkFileTasks()
})
</script>

<style scoped>
.file-viewer {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow: hidden;
}

.viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border-bottom: 1px solid #eee;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  flex-wrap: wrap;
}

/* Mobile header styles */
@media (max-width: 768px) {
  .viewer-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .edit-btn, .login-btn {
    flex: 1;
    justify-content: center;
    min-height: 44px;
  }
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-icon {
  flex-shrink: 0;
}

.file-details {
  min-width: 0;
}

.file-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  word-break: break-word;
}

.file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
  color: #666;
}

/* Mobile file info styles */
@media (max-width: 768px) {
  .file-info-header {
    padding: 0.75rem;
    margin-bottom: 0.5rem;
  }
  
  .file-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .file-name {
    font-size: 1.25rem;
  }
  
  .file-meta {
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
  }
}

.file-type {
  text-transform: uppercase;
  font-weight: 500;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  color: #666;
  transition: all 0.15s;
  /* Better touch targets for mobile */
  min-height: 44px;
}

.back-btn:hover {
  background: #f8f9fa;
  border-color: #007bff;
  color: #007bff;
}

/* Mobile back button */
@media (max-width: 768px) {
  .back-btn {
    width: 100%;
    justify-content: center;
    padding: 0.75rem 1rem;
  }
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
  background: #007bff;
  color: white;
  border: none;
  min-height: 44px;
}

.edit-btn:hover {
  background: #0056b3;
}

.login-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  text-decoration: none;
  font-size: 0.9rem;
  transition: all 0.15s;
  background: #7b1fa2;
  color: white;
  border: none;
  min-height: 44px;
}

.login-btn:hover {
  background: #4a148c;
}


.viewer-content {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
}

/* Mobile viewer content */
@media (max-width: 768px) {
  .viewer-content {
    padding: 0.75rem;
  }
}

.content-layout {
  display: flex;
  gap: 2rem;
}

.content-main {
  flex: 1;
  min-width: 0;
}

.content-sidebar {
  width: 350px;
  flex-shrink: 0;
}

/* Mobile responsive layout */
@media (max-width: 768px) {
  .content-layout {
    flex-direction: column;
    gap: 1rem;
  }
  
  .content-sidebar {
    width: 100%;
    order: -1; /* Show sidebar first on mobile */
  }
}

.loading, .error, .not-found, .task-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error i, .not-found i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #dc3545;
}

.not-found i {
  color: #6c757d;
}

.retry-btn {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.retry-btn:hover {
  background: #0056b3;
}

.file-content {
  width: 100%;
}

.raster-viewer, .vector-viewer, .generic-viewer {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  margin-top: 1rem;
  color: #6c757d;
}

.preview-placeholder i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.file-tags {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.tags-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.tag-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.tag-key {
  font-weight: 500;
  color: #495057;
  min-width: 80px;
}

.tag-value {
  color: #333;
  word-break: break-word;
}

/* Collection viewer styles */
.collection-viewer {
  width: 100%;
}

.collection-info {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
  box-sizing: border-box;
}

.collection-description {
  color: #666;
  margin-bottom: 1.5rem;
}

.collection-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

/* Mobile collection styles */
@media (max-width: 768px) {
  .collection-info {
    padding: 1rem;
    margin-bottom: 1rem;
    width: 100%;
  }
  
  .collection-stats {
    flex-direction: column;
    gap: 1rem;
  }
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.collection-actions {
  text-align: center;
}

.view-collection-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background-color 0.15s;
}

.view-collection-btn:hover {
  background: #0056b3;
}

/* File viewer styles */
.file-viewer {
  width: 100%;
}

/* File info section in sidebar */
.file-info-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.file-info-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.info-label {
  font-size: 0.9rem;
  color: #495057;
  font-weight: 500;
  min-width: 80px;
}

.info-value {
  font-size: 0.9rem;
  color: #212529;
  text-align: right;
  word-break: break-word;
  max-width: 200px;
}

/* Content sections */
.raster-content,
.vector-content,
.generic-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Unified properties section */
.unified-properties-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  top: 1rem;
}

.unified-properties-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.object-type-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.preset-icon-container {
  flex-shrink: 0;
}

.preset-icon {
  display: block;
  width: 32px;
  height: 32px;
}

.object-type-info {
  flex: 1;
}

.object-type-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: #212529;
  margin-bottom: 0.25rem;
}

.object-type-description {
  font-size: 0.9rem;
  color: #6c757d;
}

.properties-section {
  margin-top: 1.5rem;
}

.properties-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.properties-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.property-label {
  font-weight: 500;
  color: #333;
  font-size: 0.9rem;
}

.property-value {
  color: #666;
  word-break: break-word;
  font-size: 1rem;
}

/* Fallback for raw tags */
.object-tags {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Interactive map container */
.interactive-map-container {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  min-height: 400px;
  height: 80vh;
}

/* Collection content */
.collection-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
}

.collection-content p {
  color: #666;
  margin-bottom: 1.5rem;
}

/* Mobile collection content */
@media (max-width: 768px) {
  .collection-content {
    padding: 1rem;
    margin-bottom: 1rem;
    width: 100%;
    box-sizing: border-box;
  }
}

/* Georeferencing needed styles */
.georeferencing-needed {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  background: #fff;
  border-radius: 8px;
  margin: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Georeferencing section when in right panel */
.content-sidebar .georeferencing-needed {
  padding: 1.5rem;
  margin: 1.5rem 0 0 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Adjust georef icon size for right panel */
.content-sidebar .georef-icon {
  margin-bottom: 1rem;
}

.content-sidebar .georef-icon svg {
  width: 48px;
  height: 48px;
}

/* Adjust text sizing for right panel */
.content-sidebar .georeferencing-needed h3 {
  font-size: 1.1rem;
  margin-bottom: 0.75rem;
}

.content-sidebar .georeferencing-needed p {
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 1rem;
}

/* Adjust button sizing for right panel */
.content-sidebar .georef-actions {
  width: 100%;
  display: flex;
  justify-content: center;
}

.content-sidebar .georef-actions .btn {
  width: 100%;
  font-size: 0.9rem;
  padding: 0.75rem 1rem;
}

/* Adjust file info for right panel */
.content-sidebar .file-info {
  margin-top: 1rem;
  font-size: 0.85rem;
}

/* Adjust georef status for right panel */
.content-sidebar .georef-status {
  margin-top: 1rem;
  font-size: 0.85rem;
}

.georef-header {
  margin-bottom: 2rem;
}

.georef-icon {
  margin-bottom: 1rem;
}

.georef-header h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.georef-header p {
  margin: 0;
  color: #666;
  font-size: 1rem;
  max-width: 500px;
}

.georef-actions {
  margin-bottom: 1rem;
}

.georef-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.georef-btn:hover {
  background: #0056b3;
}

.georef-status {
  min-height: 40px;
}

.status-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
}

.status-error {
  color: #dc3545;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Probe status styles */
.probe-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  color: #666;
}

.probe-status .spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.probe-error,
.cannot-georeference,
.can-georeference,
.already-georeferenced {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
}

.file-preview-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.file-preview-container {
  width: 100%;
  max-width: 100%;
}

.preview-header {
  text-align: center;
  margin-bottom: 1rem;
}

.preview-header h3 {
  color: #495057;
  margin-bottom: 0.5rem;
}

.preview-header p {
  color: #6c757d;
  font-size: 0.9rem;
}

.no-preview-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.no-preview-note {
  color: #6c757d;
  font-size: 0.9rem;
  font-style: italic;
}

.probe-error .georef-icon,
.cannot-georeference .georef-icon {
  margin-bottom: 1rem;
}

.can-georeference {
  background: #f8f9fa;
  border: 2px solid #28a745;
  border-radius: 12px;
}

.needs-georeferencing {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  background: #fff8e1;
  border: 2px solid #ffc107;
  border-radius: 12px;
}

.convert-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.15s;
  margin-top: 1rem;
}

.convert-btn:hover:not(:disabled) {
  background: #218838;
}

.convert-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.7;
}

.convert-btn .spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.file-info {
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #495057;
}

.already-georeferenced {
  background: #e7f3ff;
  border: 2px solid #17a2b8;
  border-radius: 12px;
}

.regeoref-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #ffc107;
  color: #212529;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.15s;
  margin-top: 1rem;
}

.regeoref-btn:hover {
  background: #e0a800;
}

.georef-actions-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.georef-actions-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  color: #333;
}

.georef-actions-section p {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.default-georeferencing {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* Layer Filter Block */
.layer-filter-block {
  background: white;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
  border-radius: 8px;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  border-radius: 8px 8px 0 0;
  transition: background-color 0.2s ease;
}

.filter-header:hover {
  background: #e9ecef;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.filter-icon {
  color: #666;
}

.filter-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  color: #666;
}

.filter-toggle:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

.filter-toggle.expanded svg {
  transform: rotate(180deg);
}

.filter-toggle svg {
  transition: transform 0.2s ease;
}

.filter-content {
  padding: 16px;
  background: white;
  max-height: 200px;
  overflow-y: auto;
  border-radius: 0 0 8px 8px;
}

.layer-controls-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.layer-filter-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.layer-filter-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.layer-filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  margin-bottom: 4px;
}

.layer-filter-checkbox {
  width: 16px;
  height: 16px;
  margin: 0;
  cursor: pointer;
  accent-color: #007bff;
}

.layer-filter-name {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.layer-description {
  font-size: 12px;
  color: #666;
  margin-left: 24px;
  margin-bottom: 8px;
}

.layer-opacity-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.opacity-section-label {
  display: block;
  font-size: 12px;
  color: #666;
  font-weight: 500;
  margin-bottom: 6px;
}

.layer-filter-opacity-slider {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: #e0e0e0;
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.layer-filter-opacity-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-filter-opacity-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.layer-filter-opacity-slider:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
  opacity: 0.6;
}

.layer-filter-opacity-slider:disabled::-webkit-slider-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-filter-opacity-slider:disabled::-moz-range-thumb {
  background: #6c757d;
  cursor: not-allowed;
}

.layer-opacity-section .opacity-section-label {
  color: #333;
}

.layer-filter-item:has(.layer-filter-opacity-slider:disabled) .opacity-section-label {
  color: #6c757d;
  opacity: 0.7;
}

/* Map Links Section */
.map-links-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.links-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: #333;
  font-weight: 600;
}

.links-header p {
  margin: 0 0 1.5rem 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
}

.links-grid {
  display: grid;
  gap: 1.5rem;
}

.link-item {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1.25rem;
  background: #f8f9fa;
  transition: all 0.2s ease;
}

.link-item:hover {
  border-color: #007bff;
  background: #f0f7ff;
}

.link-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.link-main-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
}

.link-info {
  flex: 1;
}

.link-icon {
  flex-shrink: 0;
  color: #007bff;
  background: white;
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.link-info h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.link-info p {
  margin: 0;
  color: #666;
  font-size: 0.85rem;
  line-height: 1.3;
}

.link-url-container {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.link-url {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.8rem;
  color: #333;
  word-break: break-all;
  resize: none;
}

.link-url:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.copy-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 44px;
  height: 44px;
}

.copy-btn:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

.copy-btn:active {
  transform: translateY(0);
}

.link-details {
  font-size: 0.8rem;
  color: #495057;
  background: white;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.link-details div {
  margin-bottom: 0.25rem;
}

.link-details div:last-child {
  margin-bottom: 0;
}

.copy-status {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  text-align: center;
  transition: all 0.3s ease;
}

.copy-status.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.copy-status.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* Remote Control Links */
.remote-control-links {
  display: flex;
  gap: 0.375rem;
  align-items: flex-start;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.remote-control {
  display: inline-block;
}

.remote-control-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  background: #6c757d;
  color: white;
  text-decoration: none;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  transition: all 0.15s ease;
  border: 1px solid #5a6268;
  line-height: 1;
  min-height: 20px;
  opacity: 0.8;
}

.remote-control-btn:hover {
  background: #28a745;
  border-color: #1e7e34;
  color: white;
  text-decoration: none;
  opacity: 1;
  transform: translateY(-1px);
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

.remote-control-btn:active {
  transform: translateY(0);
}

/* Type badge styling */
.type {
  display: inline-block;
  background: #6c757d;
  color: white;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  margin-left: 0.5rem;
  line-height: 1;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .layer-controls-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-content {
    max-height: 150px;
  }
  
  .filter-header {
    padding: 10px 12px;
  }
  
  .links-grid {
    grid-template-columns: 1fr;
  }
  
  .link-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .link-icon {
    align-self: flex-start;
  }
  
  .copy-btn {
    width: 100%;
    height: auto;
    padding: 0.75rem 1rem;
  }
  
  .link-url-container {
    flex-direction: column;
  }
  
  .link-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .link-main-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .remote-control-links {
    align-self: flex-end;
    margin-top: 0;
  }
  
  .remote-control-btn {
    font-size: 0.65rem;
    padding: 0.2rem 0.4rem;
    min-height: 18px;
  }
}

/* Reset Confirmation Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1.5rem 0 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1rem;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.modal-close {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 6px;
  color: #6b7280;
  transition: all 0.15s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 0 1.5rem 1rem 1.5rem;
  text-align: center;
}

.warning-icon {
  margin-bottom: 1rem;
}

.modal-body h4 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
}

.modal-body p {
  margin: 0 0 1rem 0;
  color: #6b7280;
  line-height: 1.5;
  text-align: left;
}

.modal-body p:last-child {
  margin-bottom: 0;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem 1.5rem 1.5rem;
  justify-content: flex-end;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: 1px solid #dc2626;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
  border-color: #b91c1c;
}

.btn-danger .spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
</style> 