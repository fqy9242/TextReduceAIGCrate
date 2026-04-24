<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Monitor, Histogram, Setting } from "@element-plus/icons-vue";
import { useAuthStore } from "@/stores/auth";
import logoUrl from "@/assets/logo.png";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const activePath = computed(() => route.path);
const routeTitle = computed(() => String(route.meta.title ?? "控制台"));
const routeSubtitle = computed(() => {
  if (route.name === "task-detail" && route.params.id) {
    return `任务ID: ${String(route.params.id)}`;
  }
  return String(route.meta.subtitle ?? "智能文本改写管理系统");
});

async function handleLogout() {
  await authStore.logout();
  await router.push({ name: "login" });
}
</script>

<template>
  <div class="layout-shell">
    <aside class="sidebar">
      <div class="brand">
        <img :src="logoUrl" alt="Text AIGC Reducer Logo" class="logo-image" />
        <div>
          <h1>TextOps Console</h1>
          <p>AIGC Reduction System</p>
        </div>
      </div>

      <el-menu
        :default-active="activePath"
        router
        class="nav-menu"
        background-color="transparent"
        text-color="#AFC0D8"
        active-text-color="#FFFFFF"
      >
        <el-menu-item index="/workspace">
          <el-icon><Monitor /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Histogram /></el-icon>
          <span>历史任务</span>
        </el-menu-item>
        <el-menu-item index="/admin">
          <el-icon><Setting /></el-icon>
          <span>管理中心</span>
        </el-menu-item>
      </el-menu>

      <div class="user-box">
        <div class="user-avatar">{{ (authStore.username || "U").slice(0, 1).toUpperCase() }}</div>
        <div class="user-meta">
          <strong>{{ authStore.username || "Unknown" }}</strong>
          <span>Administrator Portal</span>
        </div>
      </div>
    </aside>

    <section class="workspace-shell">
      <header class="workspace-topbar">
        <div>
          <h2>{{ routeTitle }}</h2>
          <p>{{ routeSubtitle }}</p>
        </div>
        <div class="topbar-actions">
          <el-tag type="success" effect="light">Online</el-tag>
          <el-button type="primary" plain @click="handleLogout">退出登录</el-button>
        </div>
      </header>

      <main class="content-area">
        <router-view />
      </main>
    </section>
  </div>
</template>

<style scoped>
.layout-shell {
  display: grid;
  grid-template-columns: 236px 1fr;
  gap: 0;
  min-height: 100vh;
}

.sidebar {
  display: flex;
  flex-direction: column;
  padding: 16px 14px;
  background: linear-gradient(180deg, #18263b 0%, #141f2f 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.brand h1 {
  margin: 0;
  color: #f4f8ff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.brand p {
  margin: 3px 0 0;
  color: #8ea4c2;
  font-size: 11px;
}

.logo-image {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 6px 18px rgba(9, 18, 34, 0.45);
}

.nav-menu {
  flex: 1;
  border: none;
  background: transparent;
  margin-top: 8px;
}

:deep(.nav-menu .el-menu-item) {
  margin-bottom: 6px;
  border-radius: 8px;
  height: 42px;
  line-height: 42px;
}

:deep(.nav-menu .el-menu-item.is-active) {
  background: linear-gradient(90deg, #0f6dde 0%, #2d8cff 100%);
}

:deep(.nav-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
  box-shadow: none;
}

.user-box {
  margin-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  padding-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: linear-gradient(135deg, #1f78f2, #0ec1f3);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-meta strong {
  color: #f2f7ff;
  font-size: 13px;
  line-height: 1.2;
}

.user-meta span {
  color: #90a6c3;
  font-size: 11px;
  line-height: 1.2;
}

.workspace-shell {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.workspace-topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 72px;
  background: rgba(255, 255, 255, 0.88);
  border-bottom: 1px solid #d8e1ef;
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
}

.workspace-topbar h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.workspace-topbar p {
  margin: 3px 0 0;
  font-size: 12px;
  color: #6a7f98;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.content-area {
  min-width: 0;
  padding: 16px 18px 20px;
}

@media (max-width: 900px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.16);
  }

  .workspace-topbar {
    height: auto;
    padding: 12px;
    gap: 10px;
    flex-direction: column;
    align-items: flex-start;
  }

  .topbar-actions {
    width: 100%;
    justify-content: space-between;
  }

  .content-area {
    padding: 12px;
  }
}
</style>
