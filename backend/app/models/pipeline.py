from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class PipelineStep(str, Enum):
    source = "source"
    extract = "extract"
    rewrite = "rewrite"
    tts = "tts"
    lipsync = "lipsync"
    subtitles = "subtitles"
    cover = "cover"
    export = "export"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    douyin_url: str | None = None
    douyin_cookie: str | None = None
    douyin_request_url: str | None = None


class ScriptSegment(BaseModel):
    index: int
    start: float | None = None
    end: float | None = None
    text: str
    emotion: str | None = None


class ProjectState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    douyin_url: str | None = None
    douyin_cookie: str = ""
    douyin_request_url: str = ""
    source_video_path: str | None = None
    transcript: str = ""
    rewrite_prompt: str = ""
    rewritten_script: str = ""
    cover_title: str = ""
    segments: list[ScriptSegment] = Field(default_factory=list)
    audio_path: str | None = None
    avatar_image_path: str | None = None
    lip_sync_video_path: str | None = None
    cover_path: str | None = None
    export_path: str | None = None
    issues: list[dict[str, Any]] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.queued
    active_step: PipelineStep = PipelineStep.source
    progress: int = 0
    logs: list[str] = Field(default_factory=list)

    def project_dir(self, root: Path) -> Path:
        path = root / self.id
        path.mkdir(parents=True, exist_ok=True)
        return path
