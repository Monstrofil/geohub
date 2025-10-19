<template>
  <div class="language-switcher">
    <select v-model="currentLocale" @change="changeLanguage" class="language-select">
      <option value="uk">🇺🇦 Українська</option>
      <option value="en">🇺🇸 English</option>
      <option value="de">🇩🇪 Deutsch</option>
    </select>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const currentLocale = ref(locale.value)

// Load saved language preference from localStorage
onMounted(() => {
  const savedLocale = localStorage.getItem('preferred-language')
  if (savedLocale && ['uk', 'en', 'de'].includes(savedLocale)) {
    currentLocale.value = savedLocale
    locale.value = savedLocale
  }
})

function changeLanguage() {
  locale.value = currentLocale.value
  // Save language preference to localStorage
  localStorage.setItem('preferred-language', currentLocale.value)
}

// Watch for external locale changes
watch(locale, (newLocale) => {
  currentLocale.value = newLocale
})
</script>

<style scoped>
.language-switcher {
  display: inline-block;
  margin-right: 16px;
}

.language-select {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 120px;
}

.language-select:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.language-select:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
}

.language-select option {
  background: #667eea;
  color: white;
  padding: 8px;
}
</style>
