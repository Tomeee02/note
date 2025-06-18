import { createRouter, createWebHistory } from 'vue-router'
import BoardView from '../views/BoardView.vue'

const routes = [
  { path: '/boards/:id', name: 'Board', component: BoardView },
  { path: '/', redirect: '/boards/1' }  // ez az alapértelmezett kezdőlap
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
