import { createRouter, createWebHistory } from "vue-router";
import { tokenStore } from "@/api/client";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
    },
    {
      path: "/",
      component: () => import("@/layouts/MainLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          redirect: "/workspace",
        },
        {
          path: "workspace",
          name: "workspace",
          component: () => import("@/views/WorkspaceView.vue"),
        },
        {
          path: "tasks/:id",
          name: "task-detail",
          component: () => import("@/views/TaskDetailView.vue"),
        },
        {
          path: "history",
          name: "history",
          component: () => import("@/views/HistoryView.vue"),
        },
        {
          path: "admin",
          name: "admin",
          component: () => import("@/views/AdminView.vue"),
        },
      ],
    },
  ],
});

router.beforeEach((to) => {
  const authed = Boolean(tokenStore.getAccessToken());
  if (to.meta.requiresAuth && !authed) {
    return { name: "login" };
  }
  if (to.name === "login" && authed) {
    return { name: "workspace" };
  }
  return true;
});

export default router;
