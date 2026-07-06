<script setup lang="ts">
import type { ScriptSegment } from '@/types/project'

defineProps<{
  transcript: string
  rewrittenScript: string
  segments: readonly ScriptSegment[]
}>()
</script>

<template>
  <section class="panel script-panel">
    <h2 class="panel-title">文案与分段</h2>

    <div class="script-grid">
      <article class="script-block">
        <h3 class="block-title">原始识别文案</h3>
        <p class="script-text">{{ transcript || '暂无文案' }}</p>
      </article>

      <article class="script-block">
        <h3 class="block-title">改写后文案</h3>
        <p class="script-text">{{ rewrittenScript || '等待模型改写' }}</p>
      </article>
    </div>

    <div class="segments">
      <div v-for="segment in segments" :key="segment.index" class="segment">
        <span class="segment-time">
          {{ segment.start ?? '-' }}s - {{ segment.end ?? '-' }}s
        </span>
        <span class="segment-text">{{ segment.text }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  padding: 18px;
  border: 1px solid #d7dee3;
  border-radius: 8px;
  background: #ffffff;
}

.script-panel {
  grid-column: 1 / -1;
}

.panel-title {
  margin: 0 0 16px;
  font-size: 18px;
}

.script-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.script-block {
  min-height: 140px;
  padding: 14px;
  border: 1px solid #e0e6ea;
  border-radius: 8px;
  background: #fbfcfd;
}

.block-title {
  margin: 0 0 10px;
  color: #53636f;
  font-size: 14px;
}

.script-text {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.65;
}

.segments {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.segment {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr);
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  background: #eef4f4;
}

.segment-time {
  color: #53636f;
  font-size: 13px;
}

.segment-text {
  min-width: 0;
}

@media (max-width: 860px) {
  .script-grid,
  .segment {
    grid-template-columns: 1fr;
  }
}
</style>
