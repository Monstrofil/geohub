<template>
  <div class="language-switcher">
    <select v-model="currentLocale" @change="changeLanguage" class="pure-input">
      <option value="uk">Українська</option>
      <option value="en">English</option>
      <option value="de">Deutsch</option>
    </select>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const currentLocale = ref(locale.value)

function changeLanguage() {
  locale.value = currentLocale.value
}

// Watch for external locale changes
watch(locale, (newLocale) => {
  currentLocale.value = newLocale
})
</script>

<style scoped>
.language-switcher {
  display: inline-block;
}

.language-switcher select {
  padding: 0.25rem 0.5rem;
  font-size: 0.9rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
}
</style>
