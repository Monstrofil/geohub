import { createI18n } from 'vue-i18n'
import uk from './locales/uk.json'
import en from './locales/en.json'
import de from './locales/de.json'

// Get saved language preference or default to Ukrainian
function getInitialLocale() {
  if (typeof window !== 'undefined') {
    const savedLocale = localStorage.getItem('preferred-language')
    if (savedLocale && ['uk', 'en', 'de'].includes(savedLocale)) {
      return savedLocale
    }
  }
  return 'uk' // default locale - Ukrainian
}

const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
  fallbackLocale: 'en',
  messages: {
    uk,
    en,
    de
  }
})

export default i18n
