<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";
import logoUrl from "@/assets/logo.png";

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
    <section class="intro">
      <div class="intro-head">
        <img :src="logoUrl" alt="TextOps Logo" class="intro-logo" />
        <div>
          <div class="intro-badge">TextOps Console</div>
          <h1>文本改写与 AIGC 风险控制系统</h1>
        </div>
      </div>
      <p>面向业务团队的专业改写控制台，支持任务闭环、历史追踪、权限治理与 Prompt 在线管理。</p>
      <div class="intro-grid">
        <div class="intro-metric">
          <span>默认阈值</span>
          <strong>≤ 20%</strong>
        </div>
        <div class="intro-metric">
          <span>最大轮次</span>
          <strong>3 轮</strong>
        </div>
        <div class="intro-metric">
          <span>策略模式</span>
          <strong>deai_external</strong>
        </div>
      </div>
      <ul class="feature-list">
        <li>改写 -> 检测 -> 决策闭环自动执行</li>
        <li>任务状态与迭代轨迹全程可追踪</li>
        <li>管理员在线管理 Prompt 与用户权限</li>
      </ul>
    </section>

    <section class="app-card form-panel">
      <div class="form-brand">
        <img :src="logoUrl" alt="TextOps Logo" />
        <div>
          <h2>控制台登录</h2>
          <p>请输入管理员或业务账号</p>
        </div>
      </div>
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
      <p class="form-footer">企业内部系统，请勿向无权限人员泄露账号信息。</p>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  align-items: center;
  gap: 28px;
  padding: 32px 48px;
  position: relative;
  overflow: hidden;
}

.login-page::before {
  content: "";
  position: absolute;
  inset: -20% 42% auto -10%;
  height: 380px;
  background: radial-gradient(circle, rgba(24, 102, 219, 0.22) 0%, rgba(24, 102, 219, 0) 72%);
  pointer-events: none;
}

.intro {
  border-radius: 14px;
  border: 1px solid #cad8ea;
  background: linear-gradient(135deg, #1a3459 0%, #214773 58%, #1c4069 100%);
  padding: 28px;
  color: #f4f8ff;
  box-shadow: 0 16px 34px rgba(16, 40, 76, 0.24);
  position: relative;
  z-index: 1;
}

.intro-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.intro-logo {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 8px 20px rgba(8, 19, 37, 0.34);
}

.intro-badge {
  display: inline-flex;
  align-items: center;
  height: 28px;
  border-radius: 999px;
  padding: 0 12px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.28);
}

.intro h1 {
  margin: 0;
  margin-top: 10px;
  font-size: 34px;
  line-height: 1.2;
  letter-spacing: 0.2px;
}

.intro p {
  margin: 12px 0 0;
  max-width: 620px;
  color: #d5e4f8;
  font-size: 14px;
  line-height: 1.6;
}

.intro-grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.intro-metric {
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
}

.intro-metric span {
  display: block;
  color: #c8dbf3;
  font-size: 12px;
}

.intro-metric strong {
  display: block;
  margin-top: 2px;
  color: #fff;
  font-size: 18px;
  letter-spacing: 0.1px;
}

.feature-list {
  margin: 20px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 8px;
}

.feature-list li {
  position: relative;
  padding-left: 24px;
  color: #d8e8fb;
  font-size: 13px;
}

.feature-list li::before {
  content: "✓";
  position: absolute;
  left: 0;
  top: -1px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #1b3d69;
  background: #cde3ff;
}

.form-panel {
  padding: 24px 22px 18px;
  position: relative;
  z-index: 1;
}

.form-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.form-brand img {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 6px 16px rgba(29, 64, 111, 0.24);
}

.form-brand h2 {
  margin: 0;
  font-size: 18px;
}

.form-brand p {
  margin: 2px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
  height: 40px;
}

.form-footer {
  margin: 14px 0 0;
  color: #7f92ab;
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 900px) {
  .login-page {
    grid-template-columns: 1fr;
    padding: 14px;
  }

  .intro-head {
    flex-direction: column;
  }

  .intro h1 {
    font-size: 28px;
  }

  .intro-grid {
    grid-template-columns: 1fr;
  }
}
</style>
