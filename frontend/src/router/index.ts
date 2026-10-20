import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../layouts/AppLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: () => import('../views/HomeView.vue') },
        { path: 'buscar', name: 'catalog', component: () => import('../App.vue') },
        {
          path: 'comparacao',
          name: 'comparison',
          component: () => import('../views/ComparisonView.vue'),
        },
        {
          path: 'produto/:id',
          name: 'product',
          component: () => import('../views/ProductDetailView.vue'),
        },
        {
          path: 'lista',
          name: 'shopping-list',
          component: () => import('../views/ShoppingListView.vue'),
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
  ],
})

export default router
