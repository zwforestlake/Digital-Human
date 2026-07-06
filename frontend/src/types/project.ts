export type TaskStatus = 'queued' | 'running' | 'completed' | 'failed'

export type PipelineStep =
  | 'source'
  | 'extract'
  | 'rewrite'
  | 'tts'
  | 'lipsync'
  | 'subtitles'
  | 'cover'
  | 'export'

export interface ScriptSegment {
  index: number
  start?: number | null
  end?: number | null
  text: string
  emotion?: string | null
}

export interface ProjectState {
  id: string
  name: string
  douyin_url?: string | null
  douyin_cookie: string
  douyin_request_url: string
  source_video_path?: string | null
  transcript: string
  rewrite_prompt: string
  rewritten_script: string
  cover_title: string
  segments: ScriptSegment[]
  audio_path?: string | null
  avatar_image_path?: string | null
  lip_sync_video_path?: string | null
  cover_path?: string | null
  export_path?: string | null
  issues: Array<Record<string, unknown>>
  status: TaskStatus
  active_step: PipelineStep
  progress: number
  logs: string[]
}
