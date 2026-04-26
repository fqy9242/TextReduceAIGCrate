<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { exportTask, createTask, cancelTask } from "@/api/tasks";
import { useTaskStore } from "@/stores/task";
import ScoreTag from "@/components/ScoreTag.vue";
import IterationTimeline from "@/components/IterationTimeline.vue";
import type { TaskLog } from "@/types";

const route = useRoute();
const router = useRouter();
const taskStore = useTaskStore();
const loading = ref(false);

const taskId = computed(() => String(route.params.id ?? ""));

watch(taskId, () => fetchDetail());

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

function logTagType(level: string): "success" | "warning" | "danger" | "info" {
  const normalized = level.toLowerCase();
  if (normalized === "error") return "danger";
  if (normalized === "warning") return "warning";
  if (normalized === "info") return "success";
  return "info";
}

function renderLogDetail(detail: Record<string, unknown> | undefined): string {
  if (!detail || Object.keys(detail).length === 0) return "-";
  try {
    return JSON.stringify(detail, null, 2);
  } catch {
    return String(detail);
  }
}

function buildLogText(item: TaskLog): string {
  return [
    `[${new Date(item.created_at).toLocaleString()}] [${item.level.toUpperCase()}] [${item.stage}]`,
    item.message,
    `detail: ${renderLogDetail(item.detail)}`,
  ].join("\n");
}

async function copyText(text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textArea = document.createElement("textarea");
      textArea.value = text;
      textArea.style.position = "fixed";
      textArea.style.opacity = "0";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
    }
    ElMessage.success("已复制到剪贴板");
  } catch {
    ElMessage.error("复制失败，请手动复制");
  }
}

async function copyLog(item: TaskLog) {
  await copyText(buildLogText(item));
}

async function copyAllLogs() {
  const logs = taskStore.currentTask?.logs ?? [];
  if (logs.length === 0) {
    ElMessage.warning("暂无日志可复制");
    return;
  }
  await copyText(logs.map(buildLogText).join("\n\n----------------\n\n"));
}

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

async function retryTask() {
  const currentTask = taskStore.currentTask;
  if (!currentTask) return;
  try {
    await ElMessageBox.confirm("确定要使用相同的内容重新创建一个任务吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    loading.value = true;
    const newTask = await createTask({
      input_text: currentTask.input_text,
      target_score: currentTask.target_score,
      max_rounds: currentTask.max_rounds,
      style: currentTask.style as any,
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

async function cancelCurrentTask() {
  if (!taskId.value) return;
  try {
    await ElMessageBox.confirm("确定要终止该任务吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    loading.value = true;
    await cancelTask(taskId.value);
    ElMessage.success("任务已成功终止");
    await fetchDetail();
  } catch (error: any) {
    if (error !== "cancel") {
      const message = error?.response?.data?.detail ?? error?.message ?? "终止任务失败";
      ElMessage.error(String(message));
    }
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
    <div class="page-actions">
      <div class="actions">
        <el-button @click="fetchDetail" :loading="loading">刷新</el-button>
        <el-button 
          v-if="['queued', 'running'].includes(taskStore.currentTask?.status ?? '')" 
          type="danger" 
          @click="cancelCurrentTask" 
          :loading="loading">
          终止
        </el-button>
        <el-button type="success" @click="retryTask" :loading="loading">重试</el-button>
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
        <el-descriptions-item label="已执行时间">
          {{ formatElapsed(taskStore.currentTask.elapsed_seconds) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        v-if="taskStore.currentTask.error_message"
        class="error-alert"
        type="error"
        show-icon
        :closable="false"
        :title="taskStore.currentTask.error_message"
      />

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

      <div class="text-block">
        <div class="section-head">
          <h3>执行日志</h3>
          <el-button size="small" @click="copyAllLogs">复制全部日志</el-button>
        </div>
        <el-empty v-if="taskStore.currentTask.logs.length === 0" description="暂无日志记录" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="(item, index) in taskStore.currentTask.logs"
            :key="`${index}-${item.created_at}`"
            :timestamp="new Date(item.created_at).toLocaleString()"
            placement="top"
          >
            <div class="log-head">
              <el-tag size="small" :type="logTagType(item.level)">{{ item.level.toUpperCase() }}</el-tag>
              <span class="log-stage">{{ item.stage }}</span>
              <el-button size="small" link type="primary" class="copy-btn" @click="copyLog(item)">
                复制
              </el-button>
            </div>
            <p class="log-message">{{ item.message }}</p>
            <el-input
              type="textarea"
              :rows="2"
              :model-value="renderLogDetail(item.detail)"
              readonly
            />
          </el-timeline-item>
        </el-timeline>
      </div>
    </article>
  </section>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 8px;
}

.page-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.panel {
  padding: 18px;
}

.error-alert {
  margin-top: 14px;
}

.text-block {
  margin-top: 18px;
  border: 1px solid #e1e8f2;
  border-radius: 10px;
  padding: 12px;
  background: #fbfdff;
}

.text-block h3 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #223d5f;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.section-head h3 {
  margin: 0;
}

.log-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.copy-btn {
  margin-left: auto;
}

.log-stage {
  font-size: 12px;
  color: #627c98;
}

.log-message {
  margin: 0 0 8px;
  color: #243f5e;
  font-size: 13px;
}

@media (max-width: 900px) {
  .page-actions {
    justify-content: flex-start;
  }

  .actions {
    width: 100%;
  }

  .actions .el-button {
    flex: 1;
  }

  :deep(.el-descriptions__body .el-descriptions__table) {
    display: block;
    overflow-x: auto;
  }
}
</style>
