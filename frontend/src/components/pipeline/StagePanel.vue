<script setup lang="ts">
import { computed } from 'vue'

import type { ScriptSegment, TaskStatus } from '@/types/project'

interface ProjectView {
  id: string
  status: TaskStatus
  source_video_path?: string | null
  audio_path?: string | null
  avatar_image_path?: string | null
  lip_sync_video_path?: string | null
  cover_path?: string | null
}

const props = defineProps<{
  stepIndex: number
  actionLabel: string
  isBusy: boolean
  project: ProjectView | null
  transcript: string
  rewrittenScript: string
  segments: readonly ScriptSegment[]
  issues: ReadonlyArray<Record<string, unknown>>
  exportPath: string
  error: string
  taskProgress: number
  taskMessage: string
  isCurrentStepRunning: boolean
}>()

const projectName = defineModel<string>('projectName', { required: true })
const douyinUrl = defineModel<string>('douyinUrl', { required: true })
const douyinCookie = defineModel<string>('douyinCookie', { required: true })
const douyinRequestUrl = defineModel<string>('douyinRequestUrl', { required: true })
const rewritePrompt = defineModel<string>('rewritePrompt', { required: true })
const coverTitle = defineModel<string>('coverTitle', { required: true })

const emit = defineEmits<{
  upload: [file: File]
  uploadAvatar: [file: File]
  run: []
}>()

const stepTitle = computed(() => {
  const titles = [
    '第一步：提取抖音文案',
    '第二步：文案创作改写',
    '第三步：语音克隆合成',
    '第四步：视频对口型',
    '第五步：字幕识别',
    '第六步：封面设计',
    '第七步：导出',
  ]
  return titles[props.stepIndex] ?? '任务'
})

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    emit('upload', file)
  }
}

function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    emit('uploadAvatar', file)
  }
}
</script>

<template>
  <section class="stage-card">
    <header class="stage-heading">
      <span class="stage-line" />
      <strong class="stage-title">{{ stepTitle }}</strong>
      <span class="stage-line" />
    </header>

    <div v-if="stepIndex === 0" class="stage-body">
      <label class="field">
        <span class="field-label">抖音地址</span>
        <input v-model="douyinUrl" class="input" type="url" placeholder="https://v.douyin.com/..." />
      </label>
      <div class="action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
        <button class="secondary-action" type="button" disabled>停止中断</button>
        <button class="secondary-action" type="button" disabled>模型配置</button>
      </div>
      <article class="result-box">
        <div class="result-head">
          <strong>提取文案</strong>
          <span>模型：qwen3.5-omni-plus</span>
        </div>
        <p v-if="error" class="error-note">{{ error }}</p>
        <p v-else-if="!transcript" class="empty-note">模型生成结果会显示在下方内容框中。</p>
        <div class="task-progress">
          <div class="task-progress-head">
            <span>{{ taskMessage }}</span>
            <strong>{{ taskProgress }}%</strong>
          </div>
          <div class="task-track">
            <div class="task-fill" :class="{ 'task-fill-running': isCurrentStepRunning }" :style="{ width: `${taskProgress}%` }" />
          </div>
        </div>
        <p v-if="project?.source_video_path" class="path-text">视频保存位置：{{ project.source_video_path }}</p>
        <p v-if="project?.audio_path" class="path-text">音频保存位置：{{ project.audio_path }}</p>
        <textarea class="textarea" readonly :value="transcript" placeholder="暂无模型输出" />
      </article>
    </div>

    <div v-else-if="stepIndex === 1" class="stage-body">
      <label class="field">
        <span class="field-label">改写要求</span>
        <textarea v-model="rewritePrompt" class="textarea short" placeholder="例如：更适合女性用户，开头三秒更强。" />
      </label>
      <div class="action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
        <button class="secondary-action" type="button" disabled>停止中断</button>
        <button class="secondary-action" type="button" disabled>模型配置</button>
      </div>
      <article class="result-box">
        <div class="result-head">
          <strong>文案创作</strong>
          <span>模型：qwen3.5-flash</span>
        </div>
        <p v-if="error" class="error-note">{{ error }}</p>
        <p v-else-if="!rewrittenScript" class="empty-note">模型改写结果会显示在下方内容框中。</p>
        <div class="task-progress">
          <div class="task-progress-head">
            <span>{{ taskMessage }}</span>
            <strong>{{ taskProgress }}%</strong>
          </div>
          <div class="task-track">
            <div class="task-fill" :class="{ 'task-fill-running': isCurrentStepRunning }" :style="{ width: `${taskProgress}%` }" />
          </div>
        </div>
        <textarea class="textarea" readonly :value="rewrittenScript" placeholder="暂无模型输出" />
      </article>
    </div>

    <div v-else-if="stepIndex === 2" class="stage-body">
      <div class="action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
        <button class="secondary-action" type="button" disabled>停止中断</button>
        <button class="secondary-action" type="button" disabled>模型配置</button>
      </div>
      <label class="field">
        <span class="field-label">选择音色</span>
        <select class="input">
          <option>Cherry</option>
        </select>
      </label>
      <div class="audio-preview">模型：qwen3-tts-flash</div>
      <p class="path-text">{{ project?.audio_path || '暂无语音文件' }}</p>
    </div>

    <div v-else-if="stepIndex === 3" class="stage-body">
      <div class="action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
        <button class="secondary-action" type="button" disabled>停止中断</button>
        <button class="secondary-action" type="button" disabled>模型配置</button>
      </div>
      <div class="video-file-head">
        <strong>视频文件</strong>
        <span>视频已就绪，点击按钮弹出播放器预览</span>
      </div>
      <div class="video-tools">
        <label class="upload-box wide">
          <span>上传视频</span>
          <input class="file-input" type="file" accept="video/*" @change="handleFileChange" />
        </label>
        <button class="secondary-action" type="button" disabled>打开视频预览</button>
      </div>
      <label class="upload-box">
        <span>上传人物图片</span>
        <input class="file-input" type="file" accept="image/*" @change="handleAvatarChange" />
      </label>
      <div class="video-preview">
        {{ project?.avatar_image_path ? '人物图片已就绪，点击执行生成数字人视频' : '等待上传人物图片' }}
      </div>
      <p class="path-text">形象图片：{{ project?.avatar_image_path || '暂无图片' }}</p>
      <p class="path-text">驱动音频：{{ project?.audio_path || '请先完成第三步语音合成' }}</p>
      <p class="path-text">生成视频：{{ project?.lip_sync_video_path || '暂无视频' }}</p>
    </div>

    <div v-else-if="stepIndex === 4" class="stage-body">
      <label class="field">
        <span class="field-label row-label">
          音频文件
          <em>自动</em>
        </span>
        <input class="input" readonly :value="project?.audio_path || ''" placeholder="请先完成第三步语音合成" />
      </label>
      <label class="field">
        <span class="field-label row-label">
          视频文件
          <em>自动</em>
        </span>
        <input class="input" readonly :value="project?.lip_sync_video_path || ''" placeholder="请先完成第四步数字人视频生成" />
      </label>
      <div class="action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
        <button class="secondary-action" type="button" disabled>停止中断</button>
        <button class="secondary-action" type="button" disabled>模型配置</button>
      </div>
      <p class="status-line">状态：{{ project?.status ?? 'queued' }}</p>
      <div class="segments">
        <div v-for="segment in segments" :key="segment.index" class="segment-row">
          <span>{{ segment.start ?? '-' }} - {{ segment.end ?? '-' }}</span>
          <strong>{{ segment.text }}</strong>
        </div>
      </div>
      <div class="issue-list">
        <strong>质检结果</strong>
        <p v-if="issues.length === 0">暂无问题</p>
        <p v-for="(issue, index) in issues" :key="index">{{ issue.message ?? '未命名问题' }}</p>
      </div>
    </div>

    <div v-else-if="stepIndex === 5" class="stage-body">
      <div class="cover-grid">
        <button class="cover-option" type="button">
          <span>来上海市区游玩</span>
        </button>
        <button class="cover-option muted" type="button">
          <span>10号线景点酒店</span>
        </button>
        <button class="cover-option selected" type="button">
          <i>✓</i>
          <span>你只要选对了酒店</span>
        </button>
      </div>
      <label class="field">
        <span class="field-label row-label">
          截取位置
          <strong>10%</strong>
        </span>
        <input class="range" type="range" min="0" max="100" value="10" />
      </label>
      <div class="font-row">
        <label class="field">
          <span class="field-label">字体</span>
          <select class="input">
            <option>微软雅黑（粗体）</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label row-label">
            字号
            <strong>10px</strong>
          </span>
          <input class="range" type="range" min="8" max="48" value="10" />
        </label>
      </div>
      <label class="field">
        <span class="field-label">封面标题</span>
        <textarea v-model="coverTitle" class="textarea short" placeholder="可选：指定封面标题方向" />
      </label>
      <div class="action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
        <button class="secondary-action" type="button" disabled>停止中断</button>
        <button class="secondary-action" type="button" disabled>模型配置</button>
      </div>
      <p class="path-text">{{ project?.cover_path || '暂无封面文件' }}</p>
    </div>

    <div v-else class="stage-body">
      <div class="export-action-row">
        <button class="primary-action" type="button" :disabled="isBusy" @click="emit('run')">
          {{ isCurrentStepRunning ? `${actionLabel}中` : actionLabel }}
        </button>
      </div>
      <article class="export-box">
        <strong>{{ exportPath ? '导出完成' : '等待导出' }}</strong>
        <span>{{ exportPath || '点击一键导出后保存到本地 exports 目录' }}</span>
      </article>
      <div class="issue-list">
        <strong>质检结果</strong>
        <p v-if="issues.length === 0">暂无问题</p>
        <p v-for="(issue, index) in issues" :key="index">{{ issue.message ?? '未命名问题' }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.stage-card {
  min-height: 0;
  padding: 18px 14px;
  border: 1px solid #dfe5ea;
  border-radius: 6px;
  background: #ffffff;
  box-shadow: 0 1px 4px rgb(23 32 38 / 0.08);
}

.stage-heading {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.stage-line {
  height: 1px;
  background: #d9e0e5;
}

.stage-title {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 136px;
  height: 34px;
  padding: 0 16px;
  border: 1px solid #d9e0e5;
  border-radius: 999px;
  background: #ffffff;
  box-shadow: 0 2px 7px rgb(23 32 38 / 0.12);
  color: #34495a;
  font-size: 14px;
  font-weight: 800;
  white-space: nowrap;
}

.stage-body {
  display: grid;
  gap: 12px;
}

.field {
  display: grid;
  gap: 7px;
}

.field-label {
  color: #2f4553;
  font-size: 13px;
  font-weight: 700;
}

.input,
.textarea,
.range {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.input,
.textarea {
  border: 1px solid #d2dbe1;
  border-radius: 6px;
  background: #ffffff;
  color: #172026;
  font-size: 13px;
}

.input {
  height: 38px;
  padding: 0 12px;
}

.textarea {
  min-height: 178px;
  padding: 10px 11px;
  resize: vertical;
  line-height: 1.58;
}

.short {
  min-height: 78px;
}

.cookie-box {
  min-height: 86px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

.request-url-box {
  min-height: 92px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
}

.row-label,
.video-file-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.row-label em {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #9aa8b0;
  font-size: 12px;
  font-style: normal;
  font-weight: 600;
}

.row-label em::before {
  content: "";
  width: 8px;
  height: 8px;
  border: 1px solid #cfd8de;
  border-radius: 999px;
  background: #eef3f6;
}

.row-label strong {
  color: #7a8b96;
  font-size: 12px;
}

.result-box,
.issue-list,
.export-box {
  display: grid;
  gap: 9px;
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #2f4553;
  font-size: 12px;
}

.empty-note {
  margin: 0;
  color: #7a8b96;
  font-size: 13px;
}

.error-note {
  margin: 0;
  padding: 9px 10px;
  border: 1px solid #f1b8b8;
  border-radius: 6px;
  background: #fff5f5;
  color: #b42318;
  font-size: 12px;
  line-height: 1.5;
}

.task-progress {
  display: grid;
  gap: 7px;
  padding: 8px 10px;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  background: #f7fafb;
}

.task-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #526775;
  font-size: 12px;
}

.task-track {
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  background: #e4ebef;
}

.task-fill {
  height: 100%;
  border-radius: inherit;
  background: #2d7da3;
  transition: width 240ms ease;
}

.task-fill-running {
  background: linear-gradient(90deg, #2d7da3, #35a6bf);
}

.action-row,
.toolbar,
.video-tools {
  display: grid;
  grid-template-columns: 1fr 120px 120px;
  gap: 8px;
}

.video-tools {
  grid-template-columns: 116px minmax(0, 1fr);
}

.primary-action,
.secondary-action,
.tool-button {
  height: 36px;
  border: 1px solid #d2dbe1;
  border-radius: 6px;
  background: #ffffff;
  color: #526775;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.primary-action,
.tool-button.active {
  border-color: #2d7da3;
  background: #2d7da3;
  color: #ffffff;
}

.primary-action:disabled,
.secondary-action:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.secondary-action {
  background: #ffffff;
}

.export-action-row {
  display: grid;
}

.audio-preview,
.video-preview,
.upload-box,
.cover-option,
.export-box,
.issue-list {
  border: 1px solid #d8e0e6;
  border-radius: 6px;
  background: #fbfcfd;
}

.audio-preview {
  min-height: 54px;
  padding: 16px;
  color: #526775;
  font-size: 13px;
}

.video-preview {
  min-height: 330px;
  display: grid;
  place-items: center;
  background: #0f1724;
  color: #d7dee3;
}

.upload-box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 128px;
  height: 36px;
  color: #2d7da3;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.upload-box.wide {
  width: 100%;
  border-style: dashed;
}

.file-input {
  display: none;
}

.video-file-head {
  color: #2f4553;
  font-size: 12px;
}

.video-file-head span {
  color: #8b9ba5;
  font-weight: 600;
}

.status-line {
  margin: 0;
  color: #34495a;
  font-size: 13px;
  font-weight: 800;
}

.segments {
  display: grid;
  gap: 7px;
}

.segment-row {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e2e8ed;
  border-radius: 6px;
  font-size: 12px;
}

.segment-row span {
  color: #60717c;
}

.cover-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.cover-option {
  position: relative;
  min-height: 178px;
  overflow: hidden;
  color: #ffffff;
  font-size: 13px;
  font-weight: 800;
  background:
    linear-gradient(180deg, rgb(115 123 128 / 0.36), rgb(45 125 163 / 0.1) 54%, rgb(45 125 163 / 0.96) 55%),
    #9aa1a5;
}

.cover-option span {
  position: absolute;
  right: 8px;
  bottom: 18px;
  left: 8px;
  line-height: 1.45;
  text-align: left;
}

.cover-option::after {
  content: "";
  position: absolute;
  right: 7px;
  bottom: 6px;
  width: 24px;
  height: 34px;
  border-radius: 12px 12px 4px 4px;
  background: linear-gradient(180deg, #f2f4f5, #202832);
}

.cover-option.muted {
  background:
    linear-gradient(180deg, rgb(75 82 88 / 0.35), rgb(21 31 45 / 0.12) 54%, rgb(21 31 45 / 0.96) 55%),
    #8d959b;
}

.cover-option i {
  position: absolute;
  top: 6px;
  right: 6px;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #2d7da3;
  color: #ffffff;
  font-size: 12px;
  font-style: normal;
}

.cover-option.selected {
  outline: 3px solid #2d7da3;
  outline-offset: -3px;
}

.range {
  accent-color: #21869b;
}

.font-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(140px, 0.72fr);
  gap: 14px;
  align-items: end;
}

.export-box,
.issue-list {
  padding: 14px;
}

.export-box span,
.issue-list p,
.path-text {
  margin: 0;
  color: #526775;
  font-size: 12px;
  word-break: break-all;
}

@media (max-width: 860px) {
  .stage-card {
    min-height: auto;
  }

  .toolbar,
  .cover-grid,
  .font-row,
  .segment-row {
    grid-template-columns: 1fr;
  }
}
</style>
