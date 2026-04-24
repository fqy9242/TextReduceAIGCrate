<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  username: "admin",
  password: "Admin@123456",
});
const loading = ref(false);

async function onSubmit() {
  loading.value = true;
  try {
    await authStore.login(form.username, form.password);
    await router.push({ name: "workspace" });
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? "登录失败，请检查账号或服务状态";
    ElMessage.error(String(message));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="intro">
      <h1>文本降 AIGC 率智能体</h1>
      <p>基于 LangChain/LangGraph 的多轮改写闭环，兼顾自然表达和业务可读性。</p>
      <div class="stats">
        <div class="stat-card">
          <span>默认阈值</span>
          <strong>≤ 20%</strong>
        </div>
        <div class="stat-card">
          <span>最大轮次</span>
          <strong>3 轮</strong>
        </div>
      </div>
    </div>

    <section class="app-card form-panel">
      <h2>账号登录</h2>
      <el-form label-position="top" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="submit-btn" @click="onSubmit">
          进入工作台
        </el-button>
      </el-form>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.2fr 420px;
  align-items: center;
  gap: 36px;
  padding: 32px;
}

.intro h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.1;
  letter-spacing: 0.3px;
}

.intro p {
  margin: 14px 0 0;
  max-width: 520px;
  color: var(--text-secondary);
}

.stats {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}

.stat-card {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(11, 94, 207, 0.22);
  background: rgba(255, 255, 255, 0.7);
}

.stat-card span {
  display: block;
  color: var(--text-secondary);
  font-size: 12px;
}

.stat-card strong {
  font-size: 20px;
}

.form-panel {
  padding: 24px;
}

.form-panel h2 {
  margin: 0 0 14px;
}

.submit-btn {
  width: 100%;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 16px;
  }

  .intro h1 {
    font-size: 30px;
  }
}
</style>
