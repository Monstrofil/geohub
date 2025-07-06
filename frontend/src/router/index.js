import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../components/LandingPage.vue'
import Explorer from '../components/Explorer.vue'
import FileEditor from '../components/FileEditor.vue'
import FileList from '../components/FileList.vue'
import FileViewer from '../components/FileViewer.vue'

const routes = [
  {
    path: '/',
    name: 'LandingPage',
    component: LandingPage
  },
  {
    path: '/explorer/:branch',
    name: 'Explorer',
    component: Explorer,
    children: [
      {
          path: 'edit',
          name: 'FileEditor',
          component: FileEditor,
          props: route => ({ 
            refName: route.params.branch,
            treePath: route.query.treePath 
          })
      },
      {
          path: 'list',
          name: 'FileList',
          component: FileList,
          props: route => ({ 
            refName: route.params.branch,
            treePath: route.query.treePath 
          })
      },
      {
          path: 'view',
          name: 'FileViewer',
          component: FileViewer,
          props: route => ({ 
            refName: route.params.branch,
            treePath: route.query.treePath 
          })
      },
    ],
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 