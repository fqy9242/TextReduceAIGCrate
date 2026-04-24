import { ref } from "vue";
import { defineStore } from "pinia";
import * as taskApi from "@/api/tasks";
import type { CreateTaskPayload } from "@/api/tasks";
import type { TaskListResponse, TaskResult } from "@/types";

const FINAL_STATUSES = new Set(["success", "not_met", "failed"]);

export const useTaskStore = defineStore("task", () => {
  const currentTask = ref<TaskResult | null>(null);
  const taskList = ref<TaskListResponse | null>(null);
  const loading = ref(false);

  async function submitTask(payload: CreateTaskPayload): Promise<TaskResult> {
    loading.value = true;
    try {
      const task = await taskApi.createTask(payload);
      currentTask.value = task;
      return task;
    } finally {
      loading.value = false;
    }
  }

  async function fetchTask(taskId: string): Promise<TaskResult> {
    const task = await taskApi.getTask(taskId);
    currentTask.value = task;
    return task;
  }

  async function pollTask(taskId: string, maxAttempts = 50, intervalMs = 1000): Promise<TaskResult> {
    let latest = await fetchTask(taskId);
    for (let i = 0; i < maxAttempts; i += 1) {
      if (FINAL_STATUSES.has(latest.status)) {
        return latest;
      }
      await new Promise((resolve) => {
        window.setTimeout(resolve, intervalMs);
      });
      latest = await fetchTask(taskId);
    }
    return latest;
  }

  async function loadTaskList(page = 1, pageSize = 10): Promise<TaskListResponse> {
    const result = await taskApi.listTasks(page, pageSize);
    taskList.value = result;
    return result;
  }

  return {
    currentTask,
    taskList,
    loading,
    submitTask,
    fetchTask,
    pollTask,
    loadTaskList,
  };
});
