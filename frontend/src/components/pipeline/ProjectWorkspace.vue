<script setup lang="ts">
import { computed, shallowRef } from 'vue'

import StagePanel from './StagePanel.vue'
import { useProjectPipeline } from '@/composables/useProjectPipeline'

type PipelineStepKey = 'extract' | 'rewrite' | 'tts' | 'lipsync' | 'subtitles' | 'cover' | 'export'

const projectName = shallowRef('数字人口播项目')
const douyinUrl = shallowRef('')
const douyinCookie = shallowRef('')
const douyinRequestUrl = shallowRef('')
const rewritePrompt = shallowRef('')
const coverTitle = shallowRef('上海市区游玩，你只要选对了酒店')

const {
  project,
  error,
  isBusy,
  activeTask,
  taskProgress,
  taskMessage,
  createNewProject,
  uploadSource,
  uploadAvatar,
  runStep,
} = useProjectPipeline()

const latestLog = computed(() => project.value?.logs.at(-1) ?? '等待开始')

async function ensureProject() {
  if (project.value) return
  await createNewProject(projectName.value, douyinUrl.value, douyinCookie.value, douyinRequestUrl.value)
}

async function handleRunStep(stepKey: PipelineStepKey) {
  if (stepKey === 'extract') {
    await createNewProject(projectName.value, douyinUrl.value, douyinCookie.value, douyinRequestUrl.value)
  } else {
    await ensureProject()
  }
  await runStep(stepKey, {
    douyin_cookie: douyinCookie.value,
    douyin_request_url: douyinRequestUrl.value,
    rewrite_prompt: rewritePrompt.value,
    cover_title: coverTitle.value,
  })
}

async function handleUploadSource(file: File) {
  await ensureProject()
  await uploadSource(file)
}

async function handleUploadAvatar(file: File) {
  await ensureProject()
  await uploadAvatar(file)
}

function isStepRunning(stepKey: PipelineStepKey) {
  return isBusy.value && activeTask.value === stepKey
}
</script>

<template>
  <main class="workspace">
    <section class="board">
      <div class="board-column">
        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="0"
          action-label="提取文案"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('extract')"
          @run="handleRunStep('extract')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />

        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="1"
          action-label="文案创作"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('rewrite')"
          @run="handleRunStep('rewrite')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />
      </div>

      <div class="board-column">
        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="2"
          action-label="语音生成"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('tts')"
          @run="handleRunStep('tts')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />

        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="3"
          action-label="视频对口型"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('lipsync')"
          @run="handleRunStep('lipsync')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />
      </div>

      <div class="board-column">
        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="4"
          action-label="字幕识别"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('subtitles')"
          @run="handleRunStep('subtitles')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />
      </div>

      <div class="board-column">
        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="5"
          action-label="生成封面"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('cover')"
          @run="handleRunStep('cover')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />

        <StagePanel
          v-model:project-name="projectName"
          v-model:douyin-url="douyinUrl"
          v-model:douyin-cookie="douyinCookie"
          v-model:douyin-request-url="douyinRequestUrl"
          v-model:rewrite-prompt="rewritePrompt"
          v-model:cover-title="coverTitle"
          :step-index="6"
          action-label="一键导出"
          :is-busy="isBusy"
          :project="project"
          :transcript="project?.transcript ?? ''"
          :rewritten-script="project?.rewritten_script ?? ''"
          :segments="project?.segments ?? []"
          :issues="project?.issues ?? []"
          :export-path="project?.export_path ?? ''"
          :error="error"
          :task-progress="taskProgress"
          :task-message="taskMessage"
          :is-current-step-running="isStepRunning('export')"
          @run="handleRunStep('export')"
          @upload="handleUploadSource"
          @upload-avatar="handleUploadAvatar"
        />
      </div>
    </section>

    <footer class="workspace-footer">
      <span>作者试试看</span>
      <span>|</span>
      <span>操作文档 https://5x-class.feishu.cn/wiki/SEbcwBFO0iS98ekvBwHc0KTzndf</span>
      <span>|</span>
      <span>任务状态：{{ project?.status ?? 'queued' }}，{{ latestLog }}</span>
    </footer>
  </main>
</template>

<style scoped>
.workspace {
  min-height: 100vh;
  overflow-x: auto;
  padding: 22px 0 0;
  background: #f4f6f8;
  color: #172026;
}

.board {
  display: grid;
  grid-template-columns: repeat(4, minmax(360px, 1fr));
  gap: 16px;
  min-width: 1480px;
  padding: 0 14px 20px;
}

.board-column {
  display: grid;
  align-content: start;
  gap: 14px;
  min-width: 0;
}

.workspace-footer {
  position: sticky;
  bottom: 0;
  display: flex;
  justify-content: center;
  gap: 8px;
  min-width: 1480px;
  padding: 7px 16px;
  border-top: 1px solid #e2e8ec;
  background: rgb(255 255 255 / 0.94);
  color: #6a7a86;
  font-size: 12px;
}
</style>
