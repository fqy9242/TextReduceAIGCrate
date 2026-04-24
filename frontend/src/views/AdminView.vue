<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { createUser, listUsers, updateUserRole } from "@/api/users";
import { getPromptDetail, listPromptMetadata, reloadPrompts, updatePrompt } from "@/api/prompts";
import type { PromptMeta, UserOut } from "@/types";

const users = ref<UserOut[]>([]);
const prompts = ref<PromptMeta[]>([]);
const loadingUsers = ref(false);
const loadingPrompts = ref(false);
const loadingPromptDetail = ref(false);
const savingPrompt = ref(false);
const forbidden = ref(false);
const selectedPromptKey = ref("");

const createForm = reactive({
  username: "",
  password: "",
  role: "operator",
});

const promptForm = reactive({
  group: "",
  name: "",
  version: "",
  variablesText: "",
  system: "",
  human: "",
  instruction: "",
});

const promptLabel = computed(() => {
  if (!promptForm.group || !promptForm.name) return "";
  return `${promptForm.group}.${promptForm.name}`;
});

function toPromptKey(group: string, name: string): string {
  return `${group}:${name}`;
}

function clearPromptForm() {
  promptForm.group = "";
  promptForm.name = "";
  promptForm.version = "";
  promptForm.variablesText = "";
  promptForm.system = "";
  promptForm.human = "";
  promptForm.instruction = "";
}

function parseVariables(value: string): string[] {
  return value
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter((item, index, arr) => item.length > 0 && arr.indexOf(item) === index);
}

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

async function loadPromptDetail(group: string, name: string) {
  loadingPromptDetail.value = true;
  try {
    const detail = await getPromptDetail(group, name);
    promptForm.group = detail.group;
    promptForm.name = detail.name;
    promptForm.version = detail.version;
    promptForm.variablesText = detail.variables.join(", ");
    promptForm.system = detail.system ?? "";
    promptForm.human = detail.human ?? "";
    promptForm.instruction = detail.instruction ?? "";
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? "加载 Prompt 详情失败");
  } finally {
    loadingPromptDetail.value = false;
  }
}

async function loadPrompts() {
  loadingPrompts.value = true;
  try {
    const previousKey = selectedPromptKey.value;
    prompts.value = await listPromptMetadata();
    if (prompts.value.length === 0) {
      selectedPromptKey.value = "";
      clearPromptForm();
      return;
    }

    const selected =
      prompts.value.find((item) => toPromptKey(item.group, item.name) === previousKey) ?? prompts.value[0];
    selectedPromptKey.value = toPromptKey(selected.group, selected.name);
    await loadPromptDetail(selected.group, selected.name);
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

async function selectPrompt(row: PromptMeta) {
  selectedPromptKey.value = toPromptKey(row.group, row.name);
  await loadPromptDetail(row.group, row.name);
}

function promptRowClassName({ row }: { row: PromptMeta }): string {
  return toPromptKey(row.group, row.name) === selectedPromptKey.value ? "is-selected-row" : "";
}

async function reloadCurrentPrompt() {
  if (!promptForm.group || !promptForm.name) return;
  await loadPromptDetail(promptForm.group, promptForm.name);
}

async function savePromptChanges() {
  if (!promptForm.group || !promptForm.name) {
    ElMessage.warning("请先选择一个 Prompt");
    return;
  }

  if (!promptForm.version.trim()) {
    ElMessage.warning("版本号不能为空");
    return;
  }

  if (promptForm.group === "rewrite") {
    if (!promptForm.system.trim() || !promptForm.human.trim()) {
      ElMessage.warning("rewrite Prompt 必须包含 system 和 human");
      return;
    }
  } else if (!promptForm.instruction.trim()) {
    ElMessage.warning("instruction 不能为空");
    return;
  }

  savingPrompt.value = true;
  try {
    await updatePrompt(promptForm.group, promptForm.name, {
      version: promptForm.version.trim(),
      variables: parseVariables(promptForm.variablesText),
      system: promptForm.system,
      human: promptForm.human,
      instruction: promptForm.instruction,
    });
    ElMessage.success("Prompt 保存成功");
    await loadPrompts();
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail ?? "Prompt 保存失败");
  } finally {
    savingPrompt.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadUsers(), loadPrompts()]);
});
</script>

<template>
  <section>
    <div class="page-actions">
      <el-button @click="reloadPromptDefinitions" :loading="loadingPrompts || loadingPromptDetail">
        重载 Prompt
      </el-button>
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
        <p class="panel-tip">创建账号并分配角色，权限即时生效。</p>
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
        <h3>Prompt 管理</h3>
        <p class="panel-tip">支持在线查看、编辑和保存 Prompt 文件内容。</p>
        <el-table
          :data="prompts"
          v-loading="loadingPrompts"
          class="prompt-table"
          :row-class-name="promptRowClassName"
          @row-click="selectPrompt"
        >
          <el-table-column prop="group" label="Group" width="90" />
          <el-table-column prop="name" label="Name" width="130" />
          <el-table-column prop="version" label="Version" width="110" />
          <el-table-column label="Variables" min-width="180">
            <template #default="{ row }">
              {{ row.variables.join(", ") }}
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-if="!promptLabel" description="暂无 Prompt 数据" />
        <el-form v-else label-position="top" class="prompt-form" v-loading="loadingPromptDetail">
          <div class="prompt-head">
            <el-form-item label="Prompt">
              <el-input :model-value="promptLabel" readonly />
            </el-form-item>
            <el-form-item label="版本">
              <el-input v-model="promptForm.version" />
            </el-form-item>
          </div>

          <el-form-item label="Variables（逗号或换行分隔）">
            <el-input v-model="promptForm.variablesText" type="textarea" :rows="2" />
          </el-form-item>

          <template v-if="promptForm.group === 'rewrite'">
            <el-form-item label="System">
              <el-input v-model="promptForm.system" type="textarea" :rows="7" />
            </el-form-item>
            <el-form-item label="Human">
              <el-input v-model="promptForm.human" type="textarea" :rows="10" />
            </el-form-item>
          </template>

          <template v-else>
            <el-form-item label="Instruction">
              <el-input v-model="promptForm.instruction" type="textarea" :rows="12" />
            </el-form-item>
          </template>

          <div class="prompt-actions">
            <el-button
              type="primary"
              :loading="savingPrompt || loadingPromptDetail"
              @click="savePromptChanges"
            >
              保存 Prompt
            </el-button>
            <el-button :disabled="!promptLabel" :loading="loadingPromptDetail" @click="reloadCurrentPrompt">
              重新加载当前
            </el-button>
          </div>
        </el-form>
      </article>
    </div>
  </section>
</template>

<style scoped>
.alert {
  margin-bottom: 14px;
}

.page-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.panel {
  padding: 16px;
}

.panel h3 {
  margin: 0;
}

.panel-tip {
  margin: 6px 0 12px;
  font-size: 12px;
  color: #69809b;
}

.create-form {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 120px 90px;
  gap: 8px;
  margin-bottom: 12px;
}

.prompt-table {
  margin-bottom: 14px;
}

.prompt-form {
  margin-top: 8px;
  border-top: 1px dashed #d7e3f1;
  padding-top: 12px;
}

.prompt-head {
  display: grid;
  grid-template-columns: 1fr 180px;
  gap: 10px;
}

.prompt-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

:deep(.is-selected-row > td) {
  background: rgba(64, 158, 255, 0.12) !important;
}

@media (max-width: 1200px) {
  .prompt-head {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .page-actions {
    justify-content: flex-start;
  }

  .create-form {
    grid-template-columns: 1fr;
  }
}
</style>
