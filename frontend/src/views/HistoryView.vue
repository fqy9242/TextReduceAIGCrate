<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import ScoreTag from "@/components/ScoreTag.vue";
import { useTaskStore } from "@/stores/task";

const router = useRouter();
const taskStore = useTaskStore();
const page = ref(1);
const pageSize = ref(10);
const loading = ref(false);

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

async function onPageChange(val: number) {
  page.value = val;
  await load();
}

onMounted(load);
</script>

<template>
  <section>
    <div class="page-heading">
      <div>
        <h2 class="page-title">历史任务</h2>
        <p class="page-subtitle">分页查看改写任务执行结果</p>
      </div>
      <el-button @click="load" :loading="loading">刷新</el-button>
    </div>

    <article class="app-card panel">
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
        <el-table-column prop="created_at" label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTask(row.id)">详情</el-button>
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

.pagination {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
