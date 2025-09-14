<template>
  <div class="landing-page">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">GeoDocs Hub</h1>
        <p class="hero-subtitle">Велика колекція геопросторової документації</p>
        <p class="hero-description">
          Знайдіть у нас все, що потрібно: генеральні плани, детальні плани, 
          георастрові дані та векторні файли. Усе зручно організовано з розумним тегуванням та метаданими.
        </p>
        <div class="hero-actions">
          <button @click="navigateToFileList" class="btn btn-primary">
            <i class="icon">🗂️</i>
            Переглянути колекцію
          </button>
          <router-link v-if="!isAuthenticated" :to="loginUrl" class="btn btn-secondary">
            <i class="icon">🔐</i>
            Увійти
          </router-link>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-image">
          <div class="mockup-window">
            <div class="mockup-header">
              <div class="mockup-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
            <div class="mockup-content">
              <div class="mockup-sidebar">
                <div class="mockup-item active"></div>
                <div class="mockup-item"></div>
                <div class="mockup-item"></div>
              </div>
              <div class="mockup-main">
                <div class="mockup-file-card">
                  <div class="mockup-file-icon">📄</div>
                  <div class="mockup-file-info">
                    <div class="mockup-file-name"></div>
                    <div class="mockup-file-meta"></div>
                  </div>
                </div>
                <div class="mockup-file-card">
                  <div class="mockup-file-icon">🗺️</div>
                  <div class="mockup-file-info">
                    <div class="mockup-file-name"></div>
                    <div class="mockup-file-meta"></div>
                  </div>
                </div>
                <div class="mockup-file-card">
                  <div class="mockup-file-icon">📊</div>
                  <div class="mockup-file-info">
                    <div class="mockup-file-name"></div>
                    <div class="mockup-file-meta"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Collections Section -->
    <section id="collections" class="collections">
      <div class="container">
        <h2 class="section-title">Що у нас є</h2>
        <p class="section-subtitle">Перегляньте нашу документацію за категоріями</p>
        <div class="collections-grid">
          <div class="collection-card" @click="navigateToCollection('master_plan')">
            <div class="collection-icon">
              <svg width='48' height='48' viewBox='0 0 24 24'>
                <rect x='3' y='3' width='18' height='18' rx='3' fill='#f5f5f5' stroke='#2196F3' stroke-width='2'/>
                <rect x='10' y='3' width='4' height='18' fill='#90caf9'/>
                <rect x='3' y='10' width='18' height='4' fill='#bbdefb'/>
                <rect x='5' y='5' width='3' height='3' fill='#4CAF50'/>
                <rect x='16' y='5' width='3' height='3' fill='#FF9800'/>
                <rect x='5' y='16' width='3' height='3' fill='#9C27B0'/>
                <rect x='16' y='16' width='3' height='3' fill='#FFC107'/>
                <circle cx='12' cy='12' r='2' fill='#2196F3' stroke='#1976D2' stroke-width='1'/>
              </svg>
            </div>
            <h3>Генеральні плани</h3>
            <p>Основні плани містобудування з зонуванням, інфраструктурою та планами розвитку територій.</p>
            <div class="collection-stats">
              <span class="stat">📄 Різні формати</span>
              <span class="stat">🏗️ Плани розвитку</span>
            </div>
          </div>
          
          <div class="collection-card" @click="navigateToCollection('detailed_plan')">
            <div class="collection-icon">
              <svg width='48' height='48' viewBox='0 0 24 24'>
                <rect x='3' y='3' width='18' height='18' rx='3' fill='#f5f5f5' stroke='#2196F3' stroke-width='2'/>
                <line x1='9' y1='3' x2='9' y2='21' stroke='#bbdefb' stroke-width='1'/>
                <line x1='15' y1='3' x2='15' y2='21' stroke='#bbdefb' stroke-width='1'/>
                <line x1='3' y1='9' x2='21' y2='9' stroke='#bbdefb' stroke-width='1'/>
                <line x1='3' y1='15' x2='21' y2='15' stroke='#bbdefb' stroke-width='1'/>
                <rect x='13' y='13' width='5' height='5' fill='#fffde7' stroke='#FF9800' stroke-width='2'/>
                <rect x='13' y='13' width='5' height='5' fill='none' stroke='#FF9800' stroke-width='1' stroke-dasharray='2,2'/>
                <circle cx='18' cy='18' r='2' fill='none' stroke='#1976D2' stroke-width='1'/>
                <line x1='19.4' y1='19.4' x2='21' y2='21' stroke='#1976D2' stroke-width='1'/>
              </svg>
            </div>
            <h3>Детальні плани</h3>
            <p>Детальні плани конкретних ділянок з точними розмірами, специфікаціями та деталями будівництва.</p>
            <div class="collection-stats">
              <span class="stat">📐 Точні розміри</span>
              <span class="stat">🏢 Плани ділянок</span>
            </div>
          </div>
          
          <div class="collection-card" @click="navigateToCollection('georaster')">
            <div class="collection-icon">🗺️</div>
            <h3>Георастрові дані</h3>
            <p>Якісні растрові дані: супутникові знімки, аерофотозйомка та відскановані карти.</p>
            <div class="collection-stats">
              <span class="stat">🛰️ Супутникові знімки</span>
              <span class="stat">📷 Аерозйомка</span>
            </div>
          </div>
          
          <div class="collection-card" @click="navigateToCollection('geotiff')">
            <div class="collection-icon">📊</div>
            <h3>GeoTIFF файли</h3>
            <p>TIFF зображення з геоприв'язкою для точного картування та просторових додатків.</p>
            <div class="collection-stats">
              <span class="stat">📍 Геоприв'язка</span>
              <span class="stat">🗺️ Просторові дані</span>
            </div>
          </div>
          
          <div class="collection-card" @click="navigateToCollection('geovector')">
            <div class="collection-icon">🔷</div>
            <h3>Векторні дані</h3>
            <p>Векторні дані: shapefiles, GeoJSON та інші формати для детального картування.</p>
            <div class="collection-stats">
              <span class="stat">📐 Векторні форми</span>
              <span class="stat">🗺️ GIS дані</span>
            </div>
          </div>
          
          <div class="collection-card" @click="navigateToCollection('word')">
            <div class="collection-icon">📝</div>
            <h3>Документація</h3>
            <p>Звіти, документація та текстові матеріали по геопросторових проектах та плануванні.</p>
            <div class="collection-stats">
              <span class="stat">📄 Звіти</span>
              <span class="stat">📋 Документація</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- About Section -->
    <section class="about">
      <div class="container">
        <div class="about-content">
          <div class="about-text">
            <h2>Про нашу колекцію</h2>
            <p>
              У нас зібрано та зручно організовано плани, карти та просторові дані. 
              Кожен файл має метадані для швидкого пошуку та зручної роботи.
            </p>
            <p>
              Планувальник ви, розробник чи дослідник - знайдете потрібну документацію 
              завдяки розумному тегуванню та зручному пошуку.
            </p>
                          <div class="about-features">
                <div class="about-feature">
                  <span class="feature-icon">🏷️</span>
                  <span>Розумні теги</span>
                </div>
                <div class="about-feature">
                  <span class="feature-icon">🔍</span>
                  <span>Зручний пошук</span>
                </div>
                <div class="about-feature">
                  <span class="feature-icon">📱</span>
                  <span>Працює всюди</span>
                </div>
              </div>
          </div>
          <div class="about-visual">
            <div class="stats-card">
              <div class="stat-item">
                <div class="stat-number">6+</div>
                <div class="stat-label">Типів файлів</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">100%</div>
                <div class="stat-label">Позначено тегами</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">24/7</div>
                <div class="stat-label">Завжди доступно</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta">
      <div class="container">
        <h2>Готові почати?</h2>
        <p v-if="isAuthenticated">Перегляньте нашу колекцію геопросторової документації</p>
        <p v-else>Увійдіть в систему для доступу до повної колекції геопросторової документації</p>
        <div class="cta-actions">
          <button v-if="isAuthenticated" @click="navigateToFileList" class="btn btn-primary btn-large">
            <i class="icon">🗂️</i>
            Переглянути колекцію
          </button>
          <router-link v-else :to="loginUrl" class="btn btn-primary btn-large">
            <i class="icon">🔐</i>
            Увійти в систему
          </router-link>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
      <div class="container">
        <p>&copy; 2024 GeoDocs Hub. Платформа для роботи з геопросторовою документацією.</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { isAuthenticated } from '../stores/auth.js'

const router = useRouter()
const route = useRoute()

// Create login URL with current path as redirect
const loginUrl = computed(() => {
  const redirectParam = encodeURIComponent(route.fullPath)
  return `/login?redirect=${redirectParam}`
})

function navigateToFileList() {
  // Navigate directly to FileList
  router.push('/explorer/list')
}

function navigateToCollection(collectionType) {
  // Navigate to explorer with specific collection filter
  router.push(`/explorer/list?collection=${collectionType}`)
}
</script>

<style scoped>
.landing-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* Hero Section */
.hero {
  display: flex;
  align-items: center;
  min-height: 100vh;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  gap: 4rem;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-title {
  font-size: 4rem;
  font-weight: 700;
  margin-bottom: 1rem;
  background: linear-gradient(45deg, #fff, #f0f8ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.5rem;
  font-weight: 300;
  margin-bottom: 1rem;
  color: #e0e7ff;
}

.hero-description {
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 2rem;
  color: #c7d2fe;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(45deg, #4f46e5, #7c3aed);
  color: white;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.icon {
  font-size: 1.2em;
}

/* Hero Visual */
.hero-visual {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.hero-image {
  position: relative;
  width: 100%;
  max-width: 500px;
}

.mockup-window {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.mockup-header {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.mockup-dots {
  display: flex;
  gap: 0.5rem;
}

.mockup-dots span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
}

.mockup-content {
  display: flex;
  height: 300px;
}

.mockup-sidebar {
  width: 200px;
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mockup-item {
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.mockup-item.active {
  background: rgba(255, 255, 255, 0.3);
}

.mockup-main {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.mockup-file-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.mockup-file-icon {
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
}

.mockup-file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.mockup-file-name {
  height: 12px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  width: 80%;
}

.mockup-file-meta {
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  width: 60%;
}

/* Collections Section */
.collections {
  background: white;
  color: #1f2937;
  padding: 5rem 2rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #1f2937;
}

.section-subtitle {
  text-align: center;
  font-size: 1.1rem;
  color: #6b7280;
  margin-bottom: 3rem;
}

.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 2rem;
}

.collection-card {
  background: #f8fafc;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  cursor: pointer;
}

.collection-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
  background: #f0f9ff;
}

.collection-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  display: flex;
  justify-content: center;
}

.collection-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1f2937;
}

.collection-card p {
  color: #6b7280;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.collection-stats {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.stat {
  background: #e0f2fe;
  color: #0277bd;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
}

/* About Section */
.about {
  background: #f8fafc;
  color: #1f2937;
  padding: 5rem 2rem;
}

.about-content {
  display: flex;
  align-items: center;
  gap: 4rem;
  max-width: 1200px;
  margin: 0 auto;
}

.about-text {
  flex: 1;
}

.about-text h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: #1f2937;
}

.about-text p {
  font-size: 1.1rem;
  line-height: 1.6;
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.about-features {
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
}

.about-feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.about-visual {
  flex: 1;
  display: flex;
  justify-content: center;
}

.stats-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 200px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

/* CTA Section */
.cta {
  background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
  color: white;
  padding: 5rem 2rem;
  text-align: center;
}

.cta-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.cta h2 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.cta p {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  color: #d1d5db;
}

/* Footer */
.footer {
  background: #111827;
  color: #9ca3af;
  padding: 2rem;
  text-align: center;
}

/* Responsive Design */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
    gap: 2rem;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.25rem;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .collections-grid {
    grid-template-columns: 1fr;
  }
  
  .section-title {
    font-size: 2rem;
  }
  
  .about-content {
    flex-direction: column;
    text-align: center;
    gap: 2rem;
  }
  
  .about-features {
    justify-content: center;
  }
  
  .cta h2 {
    font-size: 2rem;
  }
}
</style> 