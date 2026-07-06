<script setup lang="ts">
import { computed } from 'vue'

import type { PipelineStep, TaskStatus } from '@/types/project'

const props = defineProps<{
  activeStep: PipelineStep
  progress: number
  status: TaskStatus
}>()

const steps: Array<{ key: PipelineStep; label: string }> = [
  { key: 'source', label: '视频来源' },
  { key: 'extract', label: '文案提取' },
  { key: 'rewrite', label: '文案改写' },
  { key: 'tts', label: '生成语音' },
  { key: 'lipsync', label: '数字人视频' },
  { key: 'subtitles', label: '字幕质检' },
  { key: 'cover', label: '封面设计' },
  { key: 'export', label: '导出视频' },
]

const activeIndex = computed(() => steps.findIndex((step) => step.key === props.activeStep))
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <h2 class="panel-title">执行进度</h2>
      <span class="status">{{ status }}</span>
    </div>

    <div class="progress-track">
      <div class="progress-fill" :style="{ width: `${progress}%` }" />
    </div>

    <ol class="steps">
      <li
        v-for="(step, index) in steps"
        :key="step.key"
        class="step"
        :class="{ 'step-active': index === activeIndex, 'step-done': index < activeIndex }"
      >
        <span class="step-index">{{ index + 1 }}</span>
        <span class="step-label">{{ step.label }}</span>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.panel {
  padding: 18px;
  border: 1px solid #d7dee3;
  border-radius: 8px;
  background: #ffffff;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  margin: 0;
  font-size: 18px;
}

.status {
  color: #53636f;
  font-size: 13px;
}

.progress-track {
  height: 8px;
  margin: 16px 0;
  overflow: hidden;
  border-radius: 8px;
  background: #e5eaee;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: #148f77;
  transition: width 180ms ease;
}

.steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: #60717c;
}

.step-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #e5eaee;
  font-size: 12px;
}

.step-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.step-active,
.step-done {
  color: #172026;
}

.step-active .step-index {
  background: #0b6bcb;
  color: #ffffff;
}

.step-done .step-index {
  background: #148f77;
  color: #ffffff;
}

@media (max-width: 860px) {
  .steps {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
