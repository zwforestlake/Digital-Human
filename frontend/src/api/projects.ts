import type { ProjectState } from '@/types/project'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function createProject(payload: {
  name: string
  douyin_url?: string
  douyin_cookie?: string
  douyin_request_url?: string
}) {
  return request<ProjectState>('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getProject(projectId: string) {
  return request<ProjectState>(`/api/projects/${projectId}`)
}

export function uploadVideo(projectId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<ProjectState>(`/api/projects/${projectId}/upload`, {
    method: 'POST',
    body: formData,
  })
}

export function uploadAvatarImage(projectId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<ProjectState>(`/api/projects/${projectId}/avatar`, {
    method: 'POST',
    body: formData,
  })
}

export function runProject(projectId: string) {
  return request<ProjectState>(`/api/projects/${projectId}/run`, {
    method: 'POST',
  })
}

export function runProjectStep(projectId: string, stepKey: string, payload: Record<string, unknown> = {}) {
  return request<ProjectState>(`/api/projects/${projectId}/steps/${stepKey}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
