<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Document, Histogram, Monitor, Setting } from "@element-plus/icons-vue";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const activePath = computed(() => route.path);

async function handleLogout() {
  await authStore.logout();
  await router.push({ name: "login" });
}
</script>

<template>
  <div class="layout-shell">
    <aside class="app-card sidebar">
      <div class="brand">
        <div class="logo-dot"></div>
        <div>
          <h1>Text AIGC Reducer</h1>
          <p>智能改写控制台</p>
        </div>
      </div>

      <el-menu :default-active="activePath" router class="nav-menu">
        <el-menu-item index="/workspace">
          <el-icon><Monitor /></el-icon>
          <span>改写工作台</span>
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
        <el-icon><Document /></el-icon>
        <span>{{ authStore.username || "Unknown" }}</span>
        <el-button link type="primary" @click="handleLogout">退出</el-button>
      </div>
    </aside>

    <main class="content-area">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.layout-shell {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 18px;
  min-height: 100vh;
  padding: 18px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.brand h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
}

.brand p {
  margin: 2px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
}

.logo-dot {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand-600), #74aff9);
}

.nav-menu {
  flex: 1;
  border: none;
  background: transparent;
}

.user-box {
  margin-top: 12px;
  border-top: 1px solid var(--line-color);
  padding-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.content-area {
  min-width: 0;
}

@media (max-width: 900px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    padding: 12px;
  }
}
</style>
