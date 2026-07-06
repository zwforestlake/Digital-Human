import { computed, readonly, shallowRef } from 'vue'

import { createProject, getProject, runProject, runProjectStep, uploadAvatarImage, uploadVideo } from '@/api/projects'
import type { ProjectState } from '@/types/project'

export function useProjectPipeline() {
  const project = shallowRef<ProjectState | null>(null)
  const error = shallowRef('')
  const isBusy = shallowRef(false)
  const pollTimer = shallowRef<number | null>(null)
  const progressTimer = shallowRef<number | null>(null)
  const activeTask = shallowRef('')
  const taskProgress = shallowRef(0)
  const taskMessage = shallowRef('等待开始')

  const canRun = computed(() => Boolean(project.value) && !isBusy.value)

  async function createNewProject(name: string, douyinUrl: string, douyinCookie = '', douyinRequestUrl = '') {
    await withBusy(async () => {
      project.value = await createProject({
        name,
        douyin_url: douyinUrl || undefined,
        douyin_cookie: douyinCookie || undefined,
        douyin_request_url: douyinRequestUrl || undefined,
      })
    })
  }

  async function uploadSource(file: File) {
    if (!project.value) return
    await withBusy(async () => {
      project.value = await uploadVideo(project.value!.id, file)
    })
  }

  async function uploadAvatar(file: File) {
    if (!project.value) return
    await withBusy(async () => {
      project.value = await uploadAvatarImage(project.value!.id, file)
    })
  }

  async function startPipeline() {
    if (!project.value) return
    await withBusy(async () => {
      project.value = await runProject(project.value!.id)
      startPolling(project.value!.id)
    })
  }

  async function runStep(stepKey: string, payload: Record<string, unknown> = {}) {
    if (!project.value) return
    await withBusy(async () => {
      startTaskProgress(stepKey)
      project.value = await runProjectStep(project.value!.id, stepKey, payload)
      finishTaskProgress(stepKey)
    })
  }

  function startPolling(projectId: string) {
    stopPolling()
    pollTimer.value = window.setInterval(async () => {
      try {
        const nextProject = await getProject(projectId)
        project.value = nextProject
        if (nextProject.status === 'completed' || nextProject.status === 'failed') {
          stopPolling()
        }
      } catch (caught) {
        error.value = caught instanceof Error ? caught.message : '轮询任务状态失败'
        stopPolling()
      }
    }, 1200)
  }

  function stopPolling() {
    if (pollTimer.value !== null) {
      window.clearInterval(pollTimer.value)
      pollTimer.value = null
    }
  }

  function startTaskProgress(stepKey: string) {
    stopTaskProgress()
    activeTask.value = stepKey
    taskProgress.value = 8
    taskMessage.value = `${stepLabel(stepKey)}处理中`
    progressTimer.value = window.setInterval(() => {
      if (taskProgress.value < 88) {
        taskProgress.value += taskProgress.value < 45 ? 7 : 3
      }
    }, 450)
  }

  function finishTaskProgress(stepKey: string) {
    stopTaskProgress()
    activeTask.value = stepKey
    taskProgress.value = 100
    taskMessage.value = `${stepLabel(stepKey)}完成`
  }

  function stopTaskProgress() {
    if (progressTimer.value !== null) {
      window.clearInterval(progressTimer.value)
      progressTimer.value = null
    }
  }

  function resetTaskProgressOnError() {
    stopTaskProgress()
    taskProgress.value = 0
    taskMessage.value = '执行失败'
  }

  function stepLabel(stepKey: string) {
    const labels: Record<string, string> = {
      extract: '提取文案',
      rewrite: '文案创作',
      tts: '语音生成',
      lipsync: '数字人视频',
      subtitles: '字幕识别',
      cover: '封面设计',
      export: '导出',
    }
    return labels[stepKey] ?? '任务'
  }

  async function withBusy(action: () => Promise<void>) {
    error.value = ''
    isBusy.value = true
    try {
      await action()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : '请求失败'
      resetTaskProgressOnError()
    } finally {
      isBusy.value = false
    }
  }

  return {
    project: readonly(project),
    error: readonly(error),
    isBusy: readonly(isBusy),
    activeTask: readonly(activeTask),
    taskProgress: readonly(taskProgress),
    taskMessage: readonly(taskMessage),
    canRun,
    createNewProject,
    uploadSource,
    uploadAvatar,
    startPipeline,
    runStep,
    stopPolling,
  }
}
