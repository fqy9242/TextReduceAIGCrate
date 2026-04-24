<script setup lang="ts">
import type { TaskIteration } from "@/types";
import ScoreTag from "@/components/ScoreTag.vue";

defineProps<{
  iterations: TaskIteration[];
}>();
</script>

<template>
  <el-empty v-if="iterations.length === 0" description="暂无迭代记录" />
  <el-timeline v-else>
    <el-timeline-item
      v-for="item in iterations"
      :key="item.round"
      :timestamp="new Date(item.created_at).toLocaleString()"
      placement="top"
    >
      <div class="timeline-header">
        <strong>第 {{ item.round }} 轮</strong>
        <ScoreTag :score="item.detector_score" :label="item.detector_label" />
      </div>
      <p class="meta">
        prompt v{{ item.prompt_version }} · LLM: {{ item.llm_mode ?? "unknown" }} · 耗时 {{ item.latency_ms }}ms · {{ item.detector_label }}
      </p>
      <el-input type="textarea" :rows="6" :model-value="item.rewritten_text" readonly />
    </el-timeline-item>
  </el-timeline>
</template>

<style scoped>
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.meta {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
