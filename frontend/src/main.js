import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import i18n from './i18n/index.js'
import 'viewerjs/dist/viewer.css'
import VueViewer from 'v-viewer'

createApp(App).use(router).use(i18n).use(VueViewer).mount('#app') 