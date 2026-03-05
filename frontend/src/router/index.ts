import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/layouts/AppShell.vue'
import DashboardView from '@/views/DashboardView.vue'
import JobDetailsView from '@/views/JobDetailsView.vue'
import JobFormView from '@/views/JobFormView.vue'
import JobsListView from '@/views/JobsListView.vue'
import LoginView from '@/views/LoginView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import RegisterView from '@/views/RegisterView.vue'
import { authGuard } from '@/router/guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: AppShell,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
          meta: { requiresAuth: true },
        },
        {
          path: 'jobs',
          name: 'jobs',
          component: JobsListView,
          meta: { requiresAuth: true },
        },
        {
          path: 'jobs/new',
          name: 'job-create',
          component: JobFormView,
          meta: { requiresAuth: true },
        },
        {
          path: 'jobs/:jobUuid/edit',
          name: 'job-edit',
          component: JobFormView,
          meta: { requiresAuth: true },
        },
        {
          path: 'jobs/:jobUuid',
          name: 'job-details',
          component: JobDetailsView,
          meta: { requiresAuth: true },
        },
      ],
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { guestOnly: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
    },
  ],
})

router.beforeEach(authGuard)

export default router
