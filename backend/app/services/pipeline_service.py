import shutil
import json
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.models.pipeline import PipelineStep, ProjectCreate, ProjectState, ScriptSegment, TaskStatus
from app.services.asr_service import asr_service
from app.services.douyin_service import douyin_service
from app.services.lipsync_service import lipsync_service
from app.services.model_router import model_router
from app.services.project_store import project_store


class PipelineService:
    def create_project(self, payload: ProjectCreate) -> ProjectState:
        project = ProjectState(
            name=payload.name,
            douyin_url=payload.douyin_url,
            douyin_cookie=payload.douyin_cookie or "",
            douyin_request_url=payload.douyin_request_url or "",
        )
        project.logs.append("项目已创建。")
        return project_store.create(project)

    async def save_upload(self, project: ProjectState, file: UploadFile) -> ProjectState:
        project_dir = project.project_dir(settings.storage_dir)
        suffix = Path(file.filename or "source.mp4").suffix or ".mp4"
        target = project_dir / f"source{suffix}"
        with target.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        project.source_video_path = str(target)
        project.active_step = PipelineStep.source
        project.progress = 10
        project.logs.append(f"已上传本地视频：{target.name}")
        return project_store.save(project)

    async def save_avatar_image(self, project: ProjectState, file: UploadFile) -> ProjectState:
        project_dir = project.project_dir(settings.storage_dir)
        avatar_dir = project_dir / "avatar"
        avatar_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "avatar.png").suffix or ".png"
        target = avatar_dir / f"source{suffix}"
        with target.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        project.avatar_image_path = str(target)
        project.active_step = PipelineStep.lipsync
        project.logs.append(f"已上传数字人形象图片：{target.name}")
        return project_store.save(project)

    async def run_pipeline(self, project: ProjectState) -> ProjectState:
        project.status = TaskStatus.running
        project.logs.append("开始执行 MVP 流水线。")
        for step in ["extract", "rewrite", "tts", "lipsync", "subtitles", "cover", "export"]:
            await self.run_step(project, step)
        project.status = TaskStatus.completed
        project.progress = 100
        project.logs.append("流水线执行完成。")
        return project_store.save(project)

    async def run_step(self, project: ProjectState, step: str) -> ProjectState:
        project.status = TaskStatus.running
        handlers = {
            "extract": self.extract_script,
            "rewrite": self.rewrite_script,
            "tts": self.generate_voice,
            "lipsync": self.lip_sync,
            "subtitles": self.recognize_subtitles,
            "cover": self.generate_cover,
            "export": self.export_video,
        }
        handler = handlers.get(step)
        if handler is None:
            raise ValueError(f"Unsupported pipeline step: {step}")

        updated = await handler(project)
        updated.status = TaskStatus.completed
        return project_store.save(updated)

    async def extract_script(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.extract
        project.progress = 14
        project_dir = project.project_dir(settings.storage_dir)
        if project.douyin_url and not project.source_video_path:
            project.logs.append("开始下载抖音视频。")
            project_store.save(project)
            video_path = await douyin_service.download_video(
                project.douyin_url,
                project_dir,
                project.douyin_cookie,
                project.douyin_request_url,
            )
            project.source_video_path = str(video_path)
            project.progress = 30
            project.logs.append(f"抖音视频已下载：{video_path}")
            project_store.save(project)

        if not project.source_video_path:
            raise RuntimeError("请先提供抖音地址或上传本地视频。")

        source_video = Path(project.source_video_path)
        project.logs.append("开始从视频中提取本地音频。")
        project.progress = 42
        project_store.save(project)
        source_audio = asr_service.extract_audio(source_video, project_dir)
        project.audio_path = str(source_audio)
        project.logs.append(f"本地音频已提取：{source_audio}")
        project.progress = 58
        project_store.save(project)
        project.logs.append("开始调用 qwen3.5-omni-plus 提取音频文案。")
        project_store.save(project)
        result = await model_router.transcribe_audio_speech(source_audio)
        project.transcript = result["transcript"]
        project.segments = [ScriptSegment(**segment) for segment in result["segments"]]
        project.progress = 100
        project.logs.append(f"文案提取完成，模型：{result['model']}。")
        return project_store.save(project)

    async def rewrite_script(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.rewrite
        project.progress = 38
        result = await model_router.rewrite_script(project.transcript, project.rewrite_prompt)
        project.rewritten_script = result["rewritten_script"]
        project.segments = [ScriptSegment(**segment) for segment in result["segments"]]
        project.logs.append(f"文案改写完成，模型：{result['model']}。")
        return project_store.save(project)

    async def generate_voice(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.tts
        project.progress = 52
        audio_dir = project.project_dir(settings.storage_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / "final_voice.wav"
        script = project.rewritten_script.strip() or project.transcript.strip()
        result = await model_router.synthesize_speech(script, audio_path)
        project.audio_path = result["audio_path"]
        project.progress = 100
        project.logs.append(f"语音生成完成，模型：{result['model']}，音色：{result['voice']}。")
        return project_store.save(project)

    async def lip_sync(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.lipsync
        project.progress = 66
        if not project.avatar_image_path:
            raise RuntimeError("请先上传数字人形象图片。")
        if not project.audio_path:
            raise RuntimeError("请先完成第三步语音合成。")

        output_path = project.project_dir(settings.storage_dir) / "lipsync" / "result.mp4"
        project.logs.append("开始调用 wan2.2-s2v 生成人物说话视频。")
        project_store.save(project)
        result = await lipsync_service.generate(Path(project.avatar_image_path), Path(project.audio_path), output_path)
        project.lip_sync_video_path = result["video_path"]
        project.progress = 100
        project.logs.append(f"数字人视频生成完成，模型：{result['model']}，任务：{result['task_id']}。")
        return project_store.save(project)

    async def recognize_subtitles(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.subtitles
        project.progress = 76
        video_path = Path(project.lip_sync_video_path or "")
        if not video_path.exists():
            raise RuntimeError("请先完成第四步数字人视频生成。")

        expected_script = project.rewritten_script.strip() or project.transcript.strip()
        project.logs.append("开始调用 qwen3.5-omni-plus 识别最终视频字幕并检查一致性。")
        project_store.save(project)
        result = await model_router.quality_check_video_subtitles(video_path, expected_script)
        project.segments = [ScriptSegment(**segment) for segment in result["segments"]]
        project.issues = result["issues"]

        subtitles_dir = project.project_dir(settings.storage_dir) / "subtitles"
        subtitles_dir.mkdir(parents=True, exist_ok=True)
        subtitles_path = subtitles_dir / "subtitles.json"
        subtitles_path.write_text(
            json.dumps({"segments": result["segments"], "issues": result["issues"]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        project.progress = 100
        project.logs.append(f"字幕识别与质检完成，模型：{result['model']}。")
        return project_store.save(project)

    async def generate_cover(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.cover
        project.progress = 88
        cover_dir = project.project_dir(settings.storage_dir) / "cover"
        cover_path = cover_dir / "final.png"
        project.logs.append("开始调用 qwen-image-2.0-pro 生成封面图。")
        project_store.save(project)
        cover = await model_router.generate_cover_image(project.rewritten_script, project.cover_title, cover_path)
        metadata_path = cover_dir / "cover.json"
        metadata_path.write_text(json.dumps(cover, ensure_ascii=False, indent=2), encoding="utf-8")
        project.cover_path = str(cover_path)
        project.cover_title = cover["title"]
        project.progress = 100
        project.logs.append(f"封面生成完成，模型：{cover['model']}。")
        return project_store.save(project)

    async def export_video(self, project: ProjectState) -> ProjectState:
        project.active_step = PipelineStep.export
        project.progress = 96
        export_path = settings.export_dir / f"{project.name}_{project.id[:8]}_final.txt"
        export_path.write_text(
            "\n".join(
                [
                    f"project={project.name}",
                    f"source={project.source_video_path or project.douyin_url}",
                    f"script={project.rewritten_script}",
                    f"cover={project.cover_path}",
                ]
            ),
            encoding="utf-8",
        )
        project.export_path = str(export_path)
        project.logs.append(f"导出占位文件已生成：{export_path.name}")
        return project_store.save(project)


pipeline_service = PipelineService()
