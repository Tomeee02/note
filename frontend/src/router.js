import { createRouter, createWebHistory } from 'vue-router';
import Documents from './components/Documents.vue';
import UploadDocument from './components/UploadDocument.vue';

const routes = [
  { path: '/', component: Documents },
  { path: '/upload', component: UploadDocument }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
