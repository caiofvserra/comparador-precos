import { createRouter, createWebHistory } from 'vue-router'
import { defineComponent, h } from 'vue'
import AppLayout from '../layouts/AppLayout.vue'

const HomeRoute = defineComponent({ render: () => h('span') })

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: () => import('../App.vue') },
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
