import asyncio
from pathlib import Path
from typing import Any

import dashscope
import httpx
from dashscope.utils.oss_utils import check_and_upload_local

from app.core.config import settings


class LipSyncService:
    async def generate(self, avatar_image: Path, audio_path: Path, output_path: Path) -> dict[str, Any]:
        if not settings.dashscope_api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")
        if not avatar_image.exists():
            raise RuntimeError(f"Avatar image does not exist: {avatar_image}")
        if not audio_path.exists():
            raise RuntimeError(f"Speech audio does not exist: {audio_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        dashscope.base_http_api_url = settings.dashscope_http_api_url

        image_url, audio_url = await asyncio.to_thread(self._upload_inputs, avatar_image, audio_path)
        task_id = await self._submit_s2v_task(image_url, audio_url)
        result = await self._wait_s2v_task(task_id)
        video_url = result.get("video_url")
        if not video_url:
            raise RuntimeError(f"wan2.2-s2v task succeeded but video_url is empty: {result}")

        await self._download_video(video_url, output_path)
        return {
            "model": "wan2.2-s2v",
            "task_id": task_id,
            "video_url": video_url,
            "video_path": str(output_path),
        }

    def _upload_inputs(self, avatar_image: Path, audio_path: Path) -> tuple[str, str]:
        _, image_url, certificate = check_and_upload_local(
            "wan2.2-s2v",
            str(avatar_image),
            settings.dashscope_api_key,
        )
        _, audio_url, _ = check_and_upload_local(
            "wan2.2-s2v",
            str(audio_path),
            settings.dashscope_api_key,
            certificate,
        )
        return image_url, audio_url

    async def _submit_s2v_task(self, image_url: str, audio_url: str) -> str:
        payload = {
            "model": "wan2.2-s2v",
            "input": {
                "image_url": image_url,
                "audio_url": audio_url,
            },
            "parameters": {
                "resolution": "480P",
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.dashscope_api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{settings.dashscope_http_api_url}/services/aigc/image2video/video-synthesis/",
                headers=headers,
                json=payload,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                detail = error.response.text[:800]
                raise RuntimeError(f"wan2.2-s2v task submit failed: {error.response.status_code} {detail}") from error
            data = response.json()

        output = data.get("output") or {}
        task_id = output.get("task_id")
        if not task_id:
            raise RuntimeError(f"wan2.2-s2v task submit failed: missing task_id in {data}")
        return str(task_id)

    async def _wait_s2v_task(self, task_id: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {settings.dashscope_api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            for _ in range(180):
                response = await client.get(
                    f"{settings.dashscope_http_api_url}/tasks/{task_id}",
                    headers=headers,
                )
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    detail = error.response.text[:800]
                    raise RuntimeError(f"wan2.2-s2v task fetch failed: {error.response.status_code} {detail}") from error
                data = response.json()
                output = data.get("output") or {}
                status = str(output.get("task_status") or "").upper()
                if status == "SUCCEEDED":
                    return output
                if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                    raise RuntimeError(f"wan2.2-s2v task failed: {data}")
                await asyncio.sleep(5)

        raise RuntimeError(f"wan2.2-s2v task timeout: {task_id}")

    async def _download_video(self, video_url: str, output_path: Path) -> None:
        async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
            response = await client.get(video_url)
            response.raise_for_status()
            output_path.write_bytes(response.content)


lipsync_service = LipSyncService()
