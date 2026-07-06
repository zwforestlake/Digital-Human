import asyncio
import base64
import binascii
import json
import mimetypes
from pathlib import Path
from typing import Any

import dashscope
import httpx

from app.core.config import settings
from app.core.models import get_step_config


class ModelRouter:
    """Central place for step-specific model calls."""

    def step_config(self, step: str) -> dict[str, Any]:
        return get_step_config(step)

    async def chat_completion(self, step: str, messages: list[dict[str, Any]]) -> str:
        config = self.step_config(step)
        api_key = settings.dashscope_api_key
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

        payload = {
            "model": config.get("model") or config.get("prompt_model"),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1200),
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.dashscope_compatible_api_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as error:
                detail = error.response.text[:500]
                raise RuntimeError(
                    f"Model request failed for {payload['model']}: "
                    f"{error.response.status_code} {detail}"
                ) from error
            data = response.json()

        return data["choices"][0]["message"]["content"]

    async def streaming_chat_completion(self, step: str, messages: list[dict[str, Any]]) -> str:
        config = self.step_config(step)
        api_key = settings.dashscope_api_key
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

        payload = {
            "model": config["model"],
            "messages": messages,
            "modalities": config.get("modalities", ["text"]),
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if "temperature" in config:
            payload["temperature"] = config["temperature"]
        if "max_tokens" in config:
            payload["max_tokens"] = config["max_tokens"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        chunks: list[str] = []

        async with httpx.AsyncClient(timeout=180) as client:
            async with client.stream(
                "POST",
                f"{settings.dashscope_compatible_api_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as error:
                    detail = (await error.response.aread()).decode("utf-8", errors="ignore")[:500]
                    raise RuntimeError(
                        f"Model request failed for {config['model']}: "
                        f"{error.response.status_code} {detail}"
                    ) from error

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data_line = line.removeprefix("data:").strip()
                    if not data_line or data_line == "[DONE]":
                        continue
                    try:
                        event = json.loads(data_line)
                    except json.JSONDecodeError:
                        continue
                    for choice in event.get("choices") or []:
                        delta = choice.get("delta") or {}
                        content = delta.get("content")
                        if isinstance(content, str):
                            chunks.append(content)
                        elif isinstance(content, list):
                            chunks.extend(
                                str(item.get("text") or "")
                                for item in content
                                if isinstance(item, dict) and item.get("text")
                            )

        content = "".join(chunks).strip()
        if not content:
            raise RuntimeError(f"Model request failed for {config['model']}: empty streamed response")
        return content

    async def transcribe_video_speech(self, source: str, media_path: Path | None = None) -> dict[str, Any]:
        config = self.step_config("douyin_extract")
        if media_path and media_path.exists():
            content = await self._transcribe_media_file(media_path)
        else:
            content = await self.chat_completion(
                "douyin_extract",
                [
                    {
                        "role": "system",
                        "content": (
                            "你是短视频语音文案提取助手。请根据用户提供的视频来源信息输出 JSON。"
                            "字段为 transcript 和 segments。segments 是数组，每项包含 index、start、end、text。"
                            "如果没有真实音视频内容可识别，必须明确说明无法从当前输入直接识别语音，"
                            "不要编造视频里说了什么。"
                        ),
                    },
                    {"role": "user", "content": f"视频来源：{source}"},
                ],
            )
        parsed = self._parse_transcript_response(content)
        return {
            "model": config.get("model"),
            "transcript": parsed["transcript"],
            "segments": parsed["segments"],
        }

    async def transcribe_audio_speech(self, audio_path: Path) -> dict[str, Any]:
        config = self.step_config("douyin_extract")
        content = await self._transcribe_audio_file(audio_path, config)
        parsed = self._parse_transcript_response(content)
        return {
            "model": config.get("model"),
            "transcript": parsed["transcript"],
            "segments": parsed["segments"],
        }

    async def _transcribe_audio_file(self, audio_path: Path, config: dict[str, Any]) -> str:
        api_key = settings.dashscope_api_key
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")
        if not audio_path.exists():
            raise RuntimeError(f"Audio file does not exist: {audio_path}")

        dashscope.base_http_api_url = settings.dashscope_http_api_url

        def call() -> str:
            response = dashscope.MultiModalConversation.call(
                model=config["model"],
                api_key=api_key,
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "text": (
                                    "你是短视频音频文案提取助手。请识别音频中的中文口播内容。"
                                    "只输出 JSON，字段为 transcript 和 segments。segments 是数组，"
                                    "每项包含 index、start、end、text。无法判断时间戳时 start/end 用 null。"
                                    "不要加入音频里没有说出的内容。"
                                )
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {"audio": str(audio_path)},
                            {"text": "请提取这个音频中的口播文案。"},
                        ],
                    },
                ],
            )
            if getattr(response, "status_code", None) != 200:
                code = getattr(response, "code", "") or "unknown"
                message = getattr(response, "message", "") or "empty error message"
                raise RuntimeError(f"Model request failed for {config['model']}: {code} {message}")
            return self._extract_multimodal_text(response)

        return await asyncio.to_thread(call)

    def _extract_multimodal_text(self, response: Any) -> str:
        output = getattr(response, "output", None)
        if not output:
            raise RuntimeError("Model request failed: empty output")

        text = getattr(output, "text", None) or output.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

        choices = getattr(output, "choices", None) or output.get("choices") or []
        for choice in choices:
            message = getattr(choice, "message", None) or choice.get("message")
            content = getattr(message, "content", None) or (message.get("content") if isinstance(message, dict) else None)
            extracted = self._content_to_text(content)
            if extracted:
                return extracted

        raise RuntimeError("Model request failed: empty text response")

    def _content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
            return "".join(parts).strip()
        return ""

    async def _transcribe_media_file(self, media_path: Path) -> str:
        mime_type = mimetypes.guess_type(media_path.name)[0] or "video/mp4"
        encoded = base64.b64encode(media_path.read_bytes()).decode("ascii")
        media_data_url = f"data:{mime_type};base64,{encoded}"
        is_audio = mime_type.startswith("audio/")
        prompt = "请提取这个音频中的中文口播文案。" if is_audio else "请提取这个视频中的画面文字、字幕和口播文案。"
        messages = [
            {
                "role": "system",
                "content": (
                    "你是短视频文案提取助手。请识别视频画面中的文字、字幕、标题，以及音频中的中文口播内容。"
                    "只输出 JSON，字段为 transcript 和 segments。segments 是数组，"
                    "每项包含 index、start、end、text。无法判断时间戳时 start/end 用 null。"
                    "不要加入视频里没有出现或说出的内容。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": media_data_url}},
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        return await self.streaming_chat_completion("douyin_extract", messages)

    async def rewrite_script(self, transcript: str, rewrite_prompt: str = "") -> dict[str, Any]:
        config = self.step_config("rewrite")
        cleaned = transcript.strip() or "请上传或解析视频后再改写文案。"
        content = await self.chat_completion(
            "rewrite",
            [
                {
                    "role": "system",
                    "content": (
                        "你是短视频文案改写助手。请保留事实含义，改写成适合中文短视频口播的文案。"
                        "不得新增原文没有的产品、价格、库存、功效、数据、品牌或承诺。"
                        "如果原文信息不足，只能围绕已给文本做表达优化，并明确保持泛化。"
                        "只输出 JSON，字段为 rewritten_script 和 segments。segments 是数组，"
                        "每项包含 index、text、emotion。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"原始文案：\n{cleaned}\n\n改写要求：\n{rewrite_prompt.strip() or '保持原意，增强短视频口播节奏。'}",
                },
            ],
        )
        parsed = self._parse_rewrite_response(content)
        return {
            "model": config.get("model"),
            "rewritten_script": parsed["rewritten_script"],
            "segments": parsed["segments"],
        }

    async def synthesize_speech(self, text: str, output_path: Path) -> dict[str, Any]:
        config = self.step_config("text_to_speech")
        api_key = settings.dashscope_api_key
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

        cleaned = text.strip()
        if not cleaned:
            raise RuntimeError("没有可用于语音合成的文案，请先完成文案改写。")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        dashscope.base_http_api_url = settings.dashscope_http_api_url

        result = await asyncio.to_thread(self._collect_qwen_tts_response, cleaned, config, api_key)
        audio_content = result["audio_content"]
        audio_url = result["audio_url"]

        if audio_content:
            output_path.write_bytes(audio_content)
        elif audio_url:
            await self._download_audio(audio_url, output_path)
        else:
            raise RuntimeError(f"Model request failed for {config['model']}: empty audio response")

        return {
            "model": config.get("model"),
            "voice": config.get("voice"),
            "audio_path": str(output_path),
        }

    def _collect_qwen_tts_response(self, text: str, config: dict[str, Any], api_key: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": config["model"],
            "api_key": api_key,
            "text": text,
            "voice": config.get("voice", "Cherry"),
            "stream": True,
        }
        instructions = config.get("instructions")
        if instructions:
            kwargs["instructions"] = instructions
            kwargs["optimize_instructions"] = config.get("optimize_instructions", True)
        response = dashscope.MultiModalConversation.call(**kwargs)
        audio_chunks: list[bytes] = []
        encoded_chunks: list[str] = []
        audio_url = ""

        for chunk in response:
            if getattr(chunk, "status_code", None) != 200:
                code = getattr(chunk, "code", "") or "unknown"
                message = getattr(chunk, "message", "") or "empty error message"
                raise RuntimeError(f"Model request failed for {config['model']}: {code} {message}")

            output = getattr(chunk, "output", None)
            audio = getattr(output, "audio", None) if output else None
            if not audio:
                continue

            data = getattr(audio, "data", None)
            if data:
                try:
                    audio_chunks.append(base64.b64decode(data, validate=True))
                except (binascii.Error, ValueError):
                    encoded_chunks.append(data)

            url = getattr(audio, "url", None)
            if url:
                audio_url = url

        if encoded_chunks:
            audio_chunks.append(base64.b64decode("".join(encoded_chunks)))

        return {"audio_content": b"".join(audio_chunks), "audio_url": audio_url}

    async def _download_audio(self, audio_url: str, output_path: Path) -> None:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            output_path.write_bytes(response.content)

    async def quality_check_video_subtitles(self, video_path: Path, expected_script: str) -> dict[str, Any]:
        config = self.step_config("subtitle_quality")
        api_key = settings.dashscope_api_key
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")
        if not video_path.exists():
            raise RuntimeError(f"Final video does not exist: {video_path}")

        dashscope.base_http_api_url = settings.dashscope_http_api_url

        def call() -> str:
            response = dashscope.MultiModalConversation.call(
                model=config["model"],
                api_key=api_key,
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "text": (
                                    "你是最终视频字幕识别和文案一致性质检助手。"
                                    "请识别视频中的中文口播，生成字幕段落，并检查它是否和期望文案一致。"
                                    "只输出 JSON，不要输出 Markdown。JSON 字段为 segments 和 issues。"
                                    "segments 是数组，每项包含 index、start、end、text。"
                                    "issues 是数组，每项包含 type、start、end、message。"
                                    "如果没有问题，issues 输出空数组。时间戳无法准确判断时用 null。"
                                )
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {"video": str(video_path)},
                            {
                                "text": (
                                    "请识别这个最终视频的口播字幕，并和下面的期望文案做一致性检查。"
                                    "重点检查漏字、错字、语义偏离、明显重复、静音空白和口播不完整。\n\n"
                                    f"期望文案：\n{expected_script.strip()}"
                                )
                            },
                        ],
                    },
                ],
            )
            if getattr(response, "status_code", None) != 200:
                code = getattr(response, "code", "") or "unknown"
                message = getattr(response, "message", "") or "empty error message"
                raise RuntimeError(f"Model request failed for {config['model']}: {code} {message}")
            return self._extract_multimodal_text(response)

        content = await asyncio.to_thread(call)
        parsed = self._parse_subtitle_quality_response(content)
        return {
            "model": config.get("model"),
            "segments": parsed["segments"],
            "issues": parsed["issues"],
        }

    async def generate_cover_image(self, script: str, cover_title: str, output_path: Path) -> dict[str, Any]:
        config = self.step_config("cover_design")
        copy = await self.generate_cover_copy(script, cover_title)
        image_url = await self._generate_qwen_image(copy["prompt"], output_path, config)
        return {
            **copy,
            "model": config.get("image_model"),
            "prompt_model": config.get("prompt_model"),
            "image_url": image_url,
            "cover_path": str(output_path),
        }

    async def generate_cover_copy(self, script: str, cover_title: str = "") -> dict[str, Any]:
        config = self.step_config("cover_design")
        title_hint = cover_title.strip()
        content = await self.chat_completion(
            "cover_design",
            [
                {
                    "role": "system",
                    "content": (
                        "你是中文短视频封面策划助手。请根据口播文案生成封面标题、副标题和图像生成提示词。"
                        "标题必须醒目、短、适合短视频封面；不得新增事实、金额、功效或法律结论。"
                        "只输出 JSON，字段为 title、subtitle、style、prompt。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"用户指定标题：{title_hint or '无'}\n\n"
                        f"口播文案：\n{script.strip() or '暂无文案'}"
                    ),
                },
            ],
        )
        parsed = self._load_json_or_text(content, "title")
        title = str(parsed.get("title") or title_hint or "3秒看懂核心风险").strip()
        subtitle = str(parsed.get("subtitle") or "很多人第一步就做错了").strip()
        style = str(parsed.get("style") or "高对比中文短视频封面，醒目标题，真实质感").strip()
        prompt = str(parsed.get("prompt") or "").strip()
        if not prompt:
            prompt = (
                f"中文短视频封面图，主题标题“{title}”，副标题“{subtitle}”。"
                f"{style}。画面主体清晰，适合手机竖屏封面，高级信息图风格，文字排版醒目。"
            )
        return {
            "model": config.get("prompt_model"),
            "title": title,
            "subtitle": subtitle,
            "style": style,
            "prompt": prompt,
        }

    async def _generate_qwen_image(self, prompt: str, output_path: Path, config: dict[str, Any]) -> str:
        api_key = settings.dashscope_api_key
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured.")

        dashscope.base_http_api_url = settings.dashscope_http_api_url

        def call():
            response = dashscope.MultiModalConversation.call(
                api_key=api_key,
                model=config["image_model"],
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                result_format="message",
                stream=False,
                watermark=config.get("watermark", False),
                prompt_extend=config.get("prompt_extend", True),
                negative_prompt=config.get("negative_prompt"),
                size=config.get("size", "2048*2048"),
            )
            if getattr(response, "status_code", None) != 200:
                code = getattr(response, "code", "") or "unknown"
                message = getattr(response, "message", "") or "empty error message"
                raise RuntimeError(f"Model request failed for {config['image_model']}: {code} {message}")
            return self._extract_image_url(response)

        image_url = await asyncio.to_thread(call)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            output_path.write_bytes(response.content)
        return image_url

    def _extract_image_url(self, response: Any) -> str:
        output = getattr(response, "output", None)
        if not output:
            raise RuntimeError("Image generation failed: empty output")

        choices = getattr(output, "choices", None) or output.get("choices") or []
        for choice in choices:
            message = getattr(choice, "message", None) or choice.get("message")
            content = getattr(message, "content", None) or (message.get("content") if isinstance(message, dict) else None)
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    image = item.get("image") or item.get("image_url") or item.get("url")
                    if isinstance(image, dict):
                        image = image.get("url")
                    if isinstance(image, str) and image:
                        return image

        results = getattr(output, "results", None) or output.get("results") or []
        for result in results:
            url = getattr(result, "url", None) or result.get("url")
            if url:
                return str(url)

        raise RuntimeError(f"Image generation failed: image url not found in {response}")

    def _parse_rewrite_response(self, content: str) -> dict[str, Any]:
        parsed = self._load_json_or_text(content, "rewritten_script")
        segments = parsed.get("segments") or []
        normalized_segments = []
        for index, segment in enumerate(segments, start=1):
            normalized_segments.append(
                {
                    "index": int(segment.get("index") or index),
                    "text": str(segment.get("text") or "").strip(),
                    "emotion": segment.get("emotion") or "natural",
                }
            )

        if not normalized_segments:
            normalized_segments = [
                {
                    "index": 1,
                    "text": str(parsed.get("rewritten_script") or content).strip(),
                    "emotion": "natural",
                }
            ]

        return {
            "rewritten_script": str(parsed.get("rewritten_script") or content).strip(),
            "segments": normalized_segments,
        }

    def _parse_subtitle_quality_response(self, content: str) -> dict[str, Any]:
        parsed = self._load_json_or_text(content, "transcript")
        segments = parsed.get("segments") or []
        normalized_segments = []
        for index, segment in enumerate(segments, start=1):
            normalized_segments.append(
                {
                    "index": int(segment.get("index") or index),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": str(segment.get("text") or "").strip(),
                }
            )

        if not normalized_segments:
            transcript = str(parsed.get("transcript") or content).strip()
            if transcript:
                normalized_segments.append({"index": 1, "start": None, "end": None, "text": transcript})

        issues = []
        raw_issues = parsed.get("issues") or []
        if isinstance(raw_issues, dict):
            raw_issues = [raw_issues]
        for issue in raw_issues:
            if not isinstance(issue, dict):
                continue
            message = str(issue.get("message") or "").strip()
            if not message:
                continue
            issues.append(
                {
                    "type": str(issue.get("type") or "quality_check"),
                    "start": issue.get("start"),
                    "end": issue.get("end"),
                    "message": message,
                }
            )

        return {"segments": normalized_segments, "issues": issues}

    def _parse_transcript_response(self, content: str) -> dict[str, Any]:
        parsed = self._load_json_or_text(content, "transcript")
        transcript = str(parsed.get("transcript") or content).strip()
        segments = parsed.get("segments") or []
        normalized_segments = []
        for index, segment in enumerate(segments, start=1):
            normalized_segments.append(
                {
                    "index": int(segment.get("index") or index),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": str(segment.get("text") or "").strip(),
                }
            )

        if not normalized_segments and transcript:
            normalized_segments = [{"index": 1, "start": None, "end": None, "text": transcript}]

        return {"transcript": transcript, "segments": normalized_segments}

    def _load_json_or_text(self, content: str, text_field: str) -> dict[str, Any]:
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.removeprefix("json").strip()

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {text_field: content.strip(), "segments": []}


model_router = ModelRouter()
