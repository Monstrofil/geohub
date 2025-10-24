import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../pages/LangingPage/LandingPage.vue'
import Login from '../pages/Login/Login.vue'
import Explorer from '../components/Explorer.vue'
import FileEditor from '../pages/FileEditor/FileEditor.vue'
import FileList from '../pages/FileList/FileList.vue'
import FileViewer from '../pages/FileViewer/FileViewer.vue'
import PresetWiki from '../pages/PresetWiki/PresetWiki.vue'
import { isAuthenticated, initializeAuth } from '../stores/auth.js'

const routes = [
  {
    path: '/',
    name: 'LandingPage',
    component: LandingPage
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { 
      requiresGuest: true  // Only accessible when not logged in
    }
  },
  {
    path: '/explorer',
    name: 'Explorer',
    component: Explorer,
    children: [
      {
          path: 'edit',
          name: 'FileEditor',
          component: FileEditor,
          props: route => ({ 
            treeItemId: route.query.id
          }),
          meta: { 
            requiresAuth: true  // Editing requires authentication
          }
      },
      {
          path: 'list',
          name: 'FileList',
          component: FileList,
          props: route => ({ 
            treePath: route.query.treePath 
          })
      },
      {
          path: 'view',
          name: 'FileViewer',
          component: FileViewer,
          props: route => ({ 
            treeItemId: route.query.id
          })
      },
      {
          path: 'preset-wiki',
          name: 'PresetWiki',
          component: PresetWiki
      },
    ],
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  // Initialize auth state on first navigation
  await initializeAuth()
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)
  const authenticated = isAuthenticated.value

  if (requiresAuth && !authenticated) {
    // Redirect to login if authentication is required but user is not authenticated
    // Store the intended destination for redirect after login
    const redirectTo = encodeURIComponent(to.fullPath)
    next(`/login?redirect=${redirectTo}`)
  } else if (requiresGuest && authenticated) {
    // Redirect to explorer if guest route is accessed but user is authenticated
    next('/explorer/list')
  } else {
    next()
  }
})

export default router 