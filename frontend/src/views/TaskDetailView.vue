<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { exportTask } from "@/api/tasks";
import { useTaskStore } from "@/stores/task";
import ScoreTag from "@/components/ScoreTag.vue";
import IterationTimeline from "@/components/IterationTimeline.vue";

const route = useRoute();
const taskStore = useTaskStore();
const loading = ref(false);

const taskId = computed(() => String(route.params.id ?? ""));

async function fetchDetail() {
  if (!taskId.value) return;
  loading.value = true;
  try {
    await taskStore.fetchTask(taskId.value);
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? "加载任务详情失败";
    ElMessage.error(String(message));
  } finally {
    loading.value = false;
  }
}

async function downloadExport() {
  if (!taskId.value) return;
  try {
    const text = await exportTask(taskId.value);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `task-${taskId.value}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? "导出失败";
    ElMessage.error(String(message));
  }
}

onMounted(fetchDetail);
</script>

<template>
  <section>
    <div class="page-heading">
      <div>
        <h2 class="page-title">任务详情</h2>
        <p class="page-subtitle mono-id">{{ taskId }}</p>
      </div>
      <div class="actions">
        <el-button @click="fetchDetail" :loading="loading">刷新</el-button>
        <el-button type="primary" @click="downloadExport">导出报告</el-button>
      </div>
    </div>

    <article v-if="taskStore.currentTask" class="app-card panel">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态">{{ taskStore.currentTask.status }}</el-descriptions-item>
        <el-descriptions-item label="最佳分数">
          <ScoreTag :score="taskStore.currentTask.best_score" />
        </el-descriptions-item>
        <el-descriptions-item label="目标阈值">{{ taskStore.currentTask.target_score }}</el-descriptions-item>
        <el-descriptions-item label="轮次">
          {{ taskStore.currentTask.rounds_used }} / {{ taskStore.currentTask.max_rounds }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="text-block">
        <h3>原始文本</h3>
        <el-input type="textarea" :rows="8" :model-value="taskStore.currentTask.input_text" readonly />
      </div>

      <div class="text-block">
        <h3>最优改写文本</h3>
        <el-input
          type="textarea"
          :rows="10"
          :model-value="taskStore.currentTask.best_text ?? ''"
          readonly
        />
      </div>

      <div class="text-block">
        <h3>迭代轨迹</h3>
        <IterationTimeline :iterations="taskStore.currentTask.iterations" />
      </div>
    </article>
  </section>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 8px;
}

.panel {
  padding: 18px;
}

.text-block {
  margin-top: 18px;
}

.text-block h3 {
  margin: 0 0 8px;
}

@media (max-width: 900px) {
  :deep(.el-descriptions__body .el-descriptions__table) {
    display: block;
    overflow-x: auto;
  }
}
</style>
