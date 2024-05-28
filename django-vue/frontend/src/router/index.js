import Vue from 'vue'
import Router from 'vue-router'
import Studies from '@/components/Studies'
import Edit from '@/components/Edit'
import Release from '@/components/Release'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'Studies',
      component: Studies
    },
    {
      path: '/edit',
      name: 'Edit',
      component: Edit
    },
    {
      path: '/release',
      name: 'Release',
      component: Release
    }

  ]
})
