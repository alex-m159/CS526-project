import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

/*
  As the name suggests, this maintains the association between the route portion of the URL 
  and the Vue component associated with it. It's possible to pass in Vue props to each
  of the components if necessary for component initialization.
*/
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/income',
      name: 'income',
      component: () => import('../views/Income.vue')
    },
    {
      path: '/income-inequality',
      name: 'income-inequality',
      component: () => import('../views/IncomeInequality.vue')
    },
    {
      path: '/population',
      name: 'population',
      component: () => import('../views/Population.vue')
    },
    {
      path: '/taxation',
      name: 'taxation',
      component: () => import('../views/Taxation.vue')
    }
  ]
})

export default router
