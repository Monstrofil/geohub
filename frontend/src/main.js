import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import i18n from './i18n/index.js'
import 'viewerjs/dist/viewer.css'
import VueViewer from 'v-viewer'
import { createVfm } from 'vue-final-modal'
import 'vue-final-modal/style.css'
import './style/main.css'

const vfm = createVfm()

createApp(App).use(router).use(i18n).use(VueViewer).use(vfm).mount('#app') 