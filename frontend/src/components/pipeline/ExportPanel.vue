<script setup lang="ts">
defineProps<{
  latestLog: string
  logs: readonly string[]
  exportPath: string
  issues: ReadonlyArray<Record<string, unknown>>
}>()
</script>

<template>
  <section class="panel export-panel">
    <div class="summary">
      <h2 class="panel-title">导出与质检</h2>
      <p class="latest-log">{{ latestLog }}</p>
      <p class="export-path">{{ exportPath || '暂无导出文件' }}</p>
    </div>

    <div class="issue-list">
      <h3 class="block-title">质检结果</h3>
      <p v-if="issues.length === 0" class="muted">暂无问题</p>
      <div v-for="(issue, index) in issues" :key="index" class="issue">
        {{ issue.message ?? '未命名问题' }}
      </div>
    </div>

    <div class="logs">
      <h3 class="block-title">任务日志</h3>
      <p v-for="(log, index) in logs" :key="index" class="log">{{ log }}</p>
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

.export-panel {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.summary {
  grid-column: 1 / -1;
}

.panel-title {
  margin: 0 0 10px;
  font-size: 18px;
}

.latest-log,
.export-path,
.muted,
.log {
  margin: 0;
  color: #53636f;
  line-height: 1.55;
}

.export-path {
  margin-top: 6px;
  word-break: break-all;
}

.block-title {
  margin: 0 0 10px;
  color: #172026;
  font-size: 14px;
}

.issue-list,
.logs {
  min-height: 120px;
  padding: 14px;
  border: 1px solid #e0e6ea;
  border-radius: 8px;
  background: #fbfcfd;
}

.issue {
  padding: 8px 0;
  color: #8a4b00;
}

.log + .log {
  margin-top: 6px;
}

@media (max-width: 860px) {
  .export-panel {
    grid-template-columns: 1fr;
  }
}
</style>
