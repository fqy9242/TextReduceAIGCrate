<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { createUser, listUsers, updateUserRole } from "@/api/users";
import { listPromptMetadata, reloadPrompts } from "@/api/prompts";
import type { PromptMeta, UserOut } from "@/types";

const users = ref<UserOut[]>([]);
const prompts = ref<PromptMeta[]>([]);
const loadingUsers = ref(false);
const loadingPrompts = ref(false);
const forbidden = ref(false);

const createForm = reactive({
  username: "",
  password: "",
  role: "operator",
});

async function loadUsers() {
  loadingUsers.value = true;
  try {
    users.value = await listUsers();
    forbidden.value = false;
  } catch (error: any) {
    if (error?.response?.status === 403) {
      forbidden.value = true;
      ElMessage.warning("当前账号无管理员权限");
    } else {
      ElMessage.error(error?.response?.data?.detail ?? "加载用户列表失败");
    }
  } finally {
    loadingUsers.value = false;
  }
}

async function loadPrompts() {
  loadingPrompts.value = true;
  try {
    prompts.value = await listPromptMetadata();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? "加载 Prompt 元数据失败");
  } finally {
    loadingPrompts.value = false;
  }
}

async function createNewUser() {
  if (!createForm.username || !createForm.password) {
    ElMessage.warning("请填写用户名和密码");
    return;
  }
  try {
    await createUser(createForm.username, createForm.password, createForm.role);
    ElMessage.success("用户创建成功");
    createForm.username = "";
    createForm.password = "";
    createForm.role = "operator";
    await loadUsers();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? "创建用户失败");
  }
}

async function changeRole(userId: number, role: string) {
  try {
    await updateUserRole(userId, role);
    ElMessage.success("角色更新成功");
    await loadUsers();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? "角色更新失败");
  }
}

async function reloadPromptDefinitions() {
  try {
    await reloadPrompts();
    ElMessage.success("Prompt 已热重载");
    await loadPrompts();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? "Prompt 重载失败");
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadPrompts()]);
});
</script>

<template>
  <section>
    <div class="page-heading">
      <div>
        <h2 class="page-title">管理中心</h2>
        <p class="page-subtitle">用户与 Prompt 管理</p>
      </div>
      <el-button @click="reloadPromptDefinitions" :loading="loadingPrompts">重载 Prompt</el-button>
    </div>

    <el-alert
      v-if="forbidden"
      title="当前账号缺少管理员权限，部分功能不可用。"
      type="warning"
      show-icon
      :closable="false"
      class="alert"
    />

    <div class="grid-two">
      <article class="app-card panel">
        <h3>用户管理</h3>
        <div class="create-form">
          <el-input v-model="createForm.username" placeholder="用户名" />
          <el-input v-model="createForm.password" placeholder="密码" type="password" show-password />
          <el-select v-model="createForm.role">
            <el-option label="admin" value="admin" />
            <el-option label="operator" value="operator" />
            <el-option label="viewer" value="viewer" />
          </el-select>
          <el-button type="primary" @click="createNewUser">创建</el-button>
        </div>

        <el-table :data="users" v-loading="loadingUsers">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" min-width="130" />
          <el-table-column label="角色" min-width="160">
            <template #default="{ row }">
              <el-select
                :model-value="row.roles[0]"
                size="small"
                @change="(value: string) => changeRole(row.id, value)"
              >
                <el-option label="admin" value="admin" />
                <el-option label="operator" value="operator" />
                <el-option label="viewer" value="viewer" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="170">
            <template #default="{ row }">
              {{ new Date(row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
        </el-table>
      </article>

      <article class="app-card panel">
        <h3>Prompt 元数据</h3>
        <el-table :data="prompts" v-loading="loadingPrompts">
          <el-table-column prop="group" label="Group" width="90" />
          <el-table-column prop="name" label="Name" width="120" />
          <el-table-column prop="version" label="Version" width="110" />
          <el-table-column label="Variables" min-width="180">
            <template #default="{ row }">
              {{ row.variables.join(", ") }}
            </template>
          </el-table-column>
          <el-table-column prop="file_path" label="Path" min-width="220" />
        </el-table>
      </article>
    </div>
  </section>
</template>

<style scoped>
.alert {
  margin-bottom: 14px;
}

.panel {
  padding: 16px;
}

.panel h3 {
  margin: 0 0 12px;
}

.create-form {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 120px 90px;
  gap: 8px;
  margin-bottom: 12px;
}

@media (max-width: 900px) {
  .create-form {
    grid-template-columns: 1fr;
  }
}
</style>
