import { createRouter, createWebHistory } from 'vue-router'
import Explorer from '../components/Explorer.vue'
import FileEditor from '../components/FileEditor.vue'
import FileList from '../components/FileList.vue'
import FileViewer from '../components/FileViewer.vue'

const routes = [
  {
    path: '/explorer/:branch',
    name: 'Explorer',
    component: Explorer,
    children: [
      {
          path: ':treePath(.*)/edit',
          name: 'FileEditor',
          component: FileEditor,
          props: true
      },
      {
          path: ':treePath*/view',
          name: 'FileList',
          component: FileList,
          props: true
      },
      {
          path: ':treePath*/view',
          name: 'FileViewer',
          component: FileViewer,
          props: true
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