<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  score: number | null;
  label?: string;
}>();

const scoreText = computed(() => (props.score === null ? "-" : `${props.score.toFixed(2)}%`));
const tagType = computed(() => {
  if (props.score === null) return "info";
  if (props.score <= 20) return "success";
  if (props.score <= 45) return "warning";
  return "danger";
});
</script>

<template>
  <el-tag :type="tagType" effect="light">{{ scoreText }}</el-tag>
</template>
