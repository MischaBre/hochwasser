import { createRouter, createWebHistory } from "vue-router";
import AppShell from "@/layouts/AppShell.vue";
import DashboardView from "@/views/DashboardView.vue";
import JobDetailsView from "@/views/JobDetailsView.vue";
import JobFormView from "@/views/JobFormView.vue";
import JobsListView from "@/views/JobsListView.vue";
import ImprintView from "@/views/ImprintView.vue";
import LandingView from "@/views/LandingView.vue";
import NotFoundView from "@/views/NotFoundView.vue";
import PrivacyPolicyView from "@/views/PrivacyPolicyView.vue";
import RegisterView from "@/views/RegisterView.vue";
import { authGuard } from "@/router/guards";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "landing",
      component: LandingView,
    },
    {
      path: "/app",
      component: AppShell,
      children: [
        {
          path: "",
          name: "dashboard",
          component: DashboardView,
          meta: { requiresAuth: true },
        },
        {
          path: "jobs",
          name: "jobs",
          component: JobsListView,
          meta: { requiresAuth: true },
        },
        {
          path: "jobs/new",
          name: "job-create",
          component: JobFormView,
          meta: { requiresAuth: true },
        },
        {
          path: "jobs/:jobUuid/edit",
          name: "job-edit",
          component: JobFormView,
          meta: { requiresAuth: true },
        },
        {
          path: "jobs/:jobUuid",
          name: "job-details",
          component: JobDetailsView,
          meta: { requiresAuth: true },
        },
      ],
    },
    {
      path: "/login",
      name: "login",
      component: LandingView,
      meta: { guestOnly: true },
    },
    {
      path: "/impressum",
      name: "impressum",
      component: ImprintView,
    },
    {
      path: "/datenschutz",
      name: "privacy",
      component: PrivacyPolicyView,
    },
    {
      path: "/register",
      name: "register",
      component: RegisterView,
      meta: { guestOnly: true },
    },
    {
      path: "/:pathMatch(.*)*",
      name: "not-found",
      component: NotFoundView,
    },
  ],
});

router.beforeEach(authGuard);

export default router;
