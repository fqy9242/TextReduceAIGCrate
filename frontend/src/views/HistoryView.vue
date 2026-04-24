<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import ScoreTag from "@/components/ScoreTag.vue";
import { useTaskStore } from "@/stores/task";
import { getTask, createTask } from "@/api/tasks";

const router = useRouter();
const taskStore = useTaskStore();
const page = ref(1);
const pageSize = ref(10);
const loading = ref(false);

function formatElapsed(seconds: number | null | undefined): string {
  if (seconds == null) return "--";
  const total = Math.max(0, Math.floor(seconds));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  if (h > 0) {
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s
      .toString()
      .padStart(2, "0")}`;
  }
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

async function load() {
  loading.value = true;
  try {
    await taskStore.loadTaskList(page.value, pageSize.value);
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? "加载历史任务失败";
    ElMessage.error(String(message));
  } finally {
    loading.value = false;
  }
}

function openTask(taskId: string) {
  router.push({ name: "task-detail", params: { id: taskId } });
}

async function retryTask(taskId: string) {
  try {
    await ElMessageBox.confirm("确定要使用相同的内容重新创建一个任务吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    loading.value = true;
    const detail = await getTask(taskId);
    if (!detail.input_text) {
      throw new Error("无法获取原任务文本");
    }
    const newTask = await createTask({
      input_text: detail.input_text,
      target_score: detail.target_score,
      max_rounds: detail.max_rounds,
      style: detail.style as any,
    });
    ElMessage.success("任务已重新创建");
    router.push({ name: "task-detail", params: { id: newTask.id } });
  } catch (error: any) {
    if (error !== "cancel") {
      const message = error?.response?.data?.detail ?? error?.message ?? "重试任务失败";
      ElMessage.error(String(message));
    }
  } finally {
    loading.value = false;
  }
}

async function onPageChange(val: number) {
  page.value = val;
  await load();
}

onMounted(load);
</script>

<template>
  <section>
    <div class="page-actions">
      <el-button @click="load" :loading="loading">刷新</el-button>
    </div>

    <article class="app-card panel">
      <div class="table-toolbar">
        <span>总任务数：{{ taskStore.taskList?.total ?? 0 }}</span>
        <span>当前页：{{ page }}</span>
      </div>
      <el-table :data="taskStore.taskList?.items ?? []" v-loading="loading">
        <el-table-column prop="id" label="任务ID" min-width="220">
          <template #default="{ row }">
            <span class="mono-id">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="分数" width="130">
          <template #default="{ row }">
            <ScoreTag :score="row.best_score" />
          </template>
        </el-table-column>
        <el-table-column prop="rounds_used" label="轮次" width="100" />
        <el-table-column label="已执行时间" width="120">
          <template #default="{ row }">
            {{ formatElapsed(row.elapsed_seconds) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTask(row.id)">详情</el-button>
            <el-button link type="success" @click="retryTask(row.id)">重试</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        background
        layout="prev, pager, next, total"
        :total="taskStore.taskList?.total ?? 0"
        :current-page="page"
        :page-size="pageSize"
        @current-change="onPageChange"
      />
    </article>
  </section>
</template>

<style scoped>
.panel {
  padding: 16px;
}

.page-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.table-toolbar {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
  margin-bottom: 10px;
  color: #667f9b;
  font-size: 12px;
}

.pagination {
  margin-top: 14px;
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .page-actions {
    justify-content: flex-start;
  }

  .table-toolbar {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
