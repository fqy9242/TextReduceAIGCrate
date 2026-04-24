<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useTaskStore } from "@/stores/task";
import ScoreTag from "@/components/ScoreTag.vue";

const router = useRouter();
const taskStore = useTaskStore();
const DEFAULT_STYLE = "deai_external" as const;

const form = reactive({
  input_text:
    "请输入需要降AIGC率的中文文本。系统会在保持语义和逻辑的前提下进行多轮改写，并使用检测适配层进行闭环评估。",
  target_score: 20,
  max_rounds: 3,
});

const working = ref(false);
const latestTaskId = ref("");

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

async function submitTask() {
  if (form.input_text.trim().length < 20) {
    ElMessage.warning("文本至少需要 20 个字符");
    return;
  }

  working.value = true;
  try {
    const task = await taskStore.submitTask({
      input_text: form.input_text,
      target_score: form.target_score,
      max_rounds: form.max_rounds,
      style: DEFAULT_STYLE,
    });
    latestTaskId.value = task.id;
    ElMessage.success("任务已提交，正在执行闭环改写");
    const finalTask = await taskStore.pollTask(task.id, 60, 1000);
    if (finalTask.status === "success") {
      ElMessage.success("任务达标完成");
    } else if (finalTask.status === "not_met") {
      ElMessage.warning("达到最大轮次，已返回最优版本");
    } else if (finalTask.status === "failed") {
      ElMessage.error(finalTask.error_message ?? "任务执行失败");
    } else {
      ElMessage.info("任务仍在排队或执行中，可到历史任务或任务详情继续查看");
    }
  } catch (error: any) {
    const message = error?.response?.data?.detail ?? "任务提交失败";
    ElMessage.error(String(message));
  } finally {
    working.value = false;
  }
}

function openTaskDetail() {
  if (!latestTaskId.value) return;
  router.push({ name: "task-detail", params: { id: latestTaskId.value } });
}
</script>

<template>
  <section>
    <div class="page-actions">
      <el-button type="primary" :disabled="!latestTaskId" @click="openTaskDetail">查看最新任务</el-button>
    </div>

    <div class="kpi-row">
      <div class="kpi-card">
        <span>策略模式</span>
        <strong>deai_external</strong>
      </div>
      <div class="kpi-card">
        <span>目标阈值</span>
        <strong>{{ form.target_score }}%</strong>
      </div>
      <div class="kpi-card">
        <span>最大轮次</span>
        <strong>{{ form.max_rounds }} 轮</strong>
      </div>
    </div>

    <div class="grid-two">
      <article class="app-card panel">
        <el-form label-position="top">
          <el-form-item label="原始文本">
            <el-input
              v-model="form.input_text"
              type="textarea"
              :rows="14"
              placeholder="输入待改写文本"
              maxlength="20000"
              show-word-limit
            />
          </el-form-item>
          <div class="params">
            <el-form-item label="目标AIGC率(%)">
              <el-input-number v-model="form.target_score" :min="1" :max="100" />
            </el-form-item>
            <el-form-item label="最大轮次">
              <el-input-number v-model="form.max_rounds" :min="1" :max="10" />
            </el-form-item>
            <el-form-item label="策略">
              <el-input model-value="deai_external（固定）" readonly />
            </el-form-item>
          </div>
          <el-button type="primary" :loading="working" class="submit-btn" @click="submitTask">启动智能改写</el-button>
        </el-form>
      </article>

      <article class="app-card panel side-panel">
        <h3>任务状态</h3>
        <el-empty v-if="!taskStore.currentTask" description="尚未提交任务" />
        <template v-else>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="任务ID">
              <span class="mono-id">{{ taskStore.currentTask.id }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="状态">{{ taskStore.currentTask.status }}</el-descriptions-item>
            <el-descriptions-item label="最佳分数">
              <ScoreTag :score="taskStore.currentTask.best_score" />
            </el-descriptions-item>
            <el-descriptions-item label="已用轮次">
              {{ taskStore.currentTask.rounds_used }} / {{ taskStore.currentTask.max_rounds }}
            </el-descriptions-item>
            <el-descriptions-item label="已执行时间">
              {{ formatElapsed(taskStore.currentTask.elapsed_seconds) }}
            </el-descriptions-item>
          </el-descriptions>
          <h4>最佳文本</h4>
          <el-input
            type="textarea"
            :rows="12"
            :model-value="taskStore.currentTask.best_text ?? ''"
            readonly
          />
        </template>
      </article>
    </div>
  </section>
</template>

<style scoped>
.panel {
  padding: 18px;
}

.page-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kpi-card {
  border-radius: 10px;
  border: 1px solid #d8e4f2;
  background: linear-gradient(180deg, #fff 0%, #f7fbff 100%);
  padding: 12px;
}

.kpi-card span {
  color: #657d99;
  font-size: 12px;
}

.kpi-card strong {
  display: block;
  margin-top: 3px;
  font-size: 16px;
  color: #1d3656;
  font-weight: 700;
}

.params {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.submit-btn {
  min-width: 130px;
}

.side-panel h3 {
  margin-top: 0;
  margin-bottom: 10px;
}

.side-panel h4 {
  margin: 16px 0 8px;
}

@media (max-width: 900px) {
  .page-actions {
    justify-content: flex-start;
  }

  .kpi-row {
    grid-template-columns: 1fr;
  }

  .params {
    grid-template-columns: 1fr;
  }
}
</style>
