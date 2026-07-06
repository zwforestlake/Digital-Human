import asyncio
import shutil
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

import httpx
from yt_dlp.cookies import load_cookies
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from app.core.config import settings


class DouyinService:
    async def download_video(
        self,
        url: str,
        project_dir: Path,
        cookie_header: str = "",
        request_url: str = "",
    ) -> Path:
        downloads_dir = project_dir / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        aweme_id = self._extract_aweme_id(url)
        cached_video = self._find_cached_video(aweme_id, project_dir)
        if cached_video:
            target = downloads_dir / "source.mp4"
            if cached_video.resolve() != target.resolve():
                shutil.copy2(cached_video, target)
            return target

        if request_url.strip():
            direct_path = await self._download_from_request_url(url, request_url, downloads_dir, cookie_header)
            if direct_path.exists():
                self._cache_video(aweme_id, direct_path)
                return direct_path

        output_template = str(downloads_dir / "source.%(ext)s")

        def run_download() -> Path:
            options = {
                "format": "best[ext=mp4]/best",
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "merge_output_format": "mp4",
                "http_headers": {
                    "Referer": "https://www.douyin.com/",
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                },
            }
            self._apply_cookie_options(options, cookie_header)
            try:
                with YoutubeDL(options) as downloader:
                    info = downloader.extract_info(url, download=True)
                    downloaded = Path(downloader.prepare_filename(info))
                    if downloaded.exists():
                        self._cache_video(aweme_id, downloaded)
                        return downloaded
            except DownloadError as error:
                message = str(error)
                if "Fresh cookies" in message:
                    raise RuntimeError(
                        "Douyin video download failed: 当前抖音 Cookie 不可用。"
                        "请在 Edge 中登录抖音并打开一次该视频，或导出 cookies.txt 到 "
                        "backend/cookies/douyin.txt 后重试。原始错误："
                        f"{message}"
                    ) from error
                raise RuntimeError(f"Douyin video download failed: {error}") from error

            candidates = sorted(downloads_dir.glob("source.*"), key=lambda item: item.stat().st_mtime, reverse=True)
            if not candidates:
                raise RuntimeError("Douyin video download failed: output file was not created.")
            self._cache_video(aweme_id, candidates[0])
            return candidates[0]

        return await asyncio.to_thread(run_download)

    def _find_cached_video(self, aweme_id: str, current_project_dir: Path) -> Path | None:
        if not aweme_id:
            return None

        cache_path = settings.storage_dir / "_douyin_cache" / aweme_id / "source.mp4"
        if cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path

        for candidate in settings.storage_dir.glob("*/downloads/source.mp4"):
            if current_project_dir in candidate.parents:
                continue
            if candidate.exists() and candidate.stat().st_size > 0:
                self._cache_video(aweme_id, candidate)
                return candidate
        return None

    def _cache_video(self, aweme_id: str, source: Path) -> None:
        if not aweme_id or not source.exists() or source.stat().st_size == 0:
            return
        cache_dir = settings.storage_dir / "_douyin_cache" / aweme_id
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / "source.mp4"
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)

    async def _download_from_request_url(
        self,
        douyin_url: str,
        request_url: str,
        downloads_dir: Path,
        cookie_header: str = "",
    ) -> Path:
        aweme_id = self._extract_aweme_id(douyin_url)
        if not aweme_id:
            raise RuntimeError("Douyin video download failed: could not extract aweme id from URL.")

        params = dict(parse_qsl(urlparse(request_url).query))
        params["aweme_id"] = aweme_id
        detail_url = "https://www-hj.douyin.com/aweme/v1/web/aweme/detail/?" + urlencode(params)
        headers = self._browser_headers(douyin_url)
        if cookie_header.strip():
            headers["Cookie"] = cookie_header.strip()
        else:
            browser_cookie_header = self._browser_cookie_header()
            if browser_cookie_header:
                headers["Cookie"] = browser_cookie_header

        async with httpx.AsyncClient(timeout=30, verify=False, follow_redirects=True) as client:
            response = await client.get(detail_url, headers=headers)
            response.raise_for_status()
            if not response.text.strip():
                raise RuntimeError("Douyin video download failed: aweme detail response was empty.")
            data = response.json()

            detail = data.get("aweme_detail")
            if not detail:
                raise RuntimeError("Douyin video download failed: aweme_detail was empty.")

            video_url = self._select_video_url(detail)
            video_response = await client.get(video_url, headers=headers)
            video_response.raise_for_status()

        target = downloads_dir / "source.mp4"
        target.write_bytes(video_response.content)
        return target

    def _extract_aweme_id(self, url: str) -> str:
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)
        match = re.search(r"(\d{12,})", url)
        return match.group(1) if match else ""

    def _select_video_url(self, detail: dict) -> str:
        video = detail.get("video") or {}
        candidates = []
        for item in video.get("bit_rate") or []:
            play_addr = item.get("play_addr") or {}
            candidates.extend(play_addr.get("url_list") or [])
        for key in ("play_addr", "play_addr_h264", "download_addr"):
            candidates.extend((video.get(key) or {}).get("url_list") or [])
        if not candidates:
            raise RuntimeError("Douyin video download failed: no playable video URL found.")
        return candidates[0]

    def _browser_headers(self, referer: str) -> dict[str, str]:
        return {
            "Referer": referer,
            "Accept": "application/json, text/plain, */*",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
            ),
        }

    def _browser_cookie_header(self) -> str:
        if not settings.douyin_cookies_browser:
            return ""
        try:
            jar = load_cookies(None, (settings.douyin_cookies_browser, "Default", None, None), YoutubeDL({"quiet": True}))
        except Exception:
            return ""
        cookie_pairs = [f"{cookie.name}={cookie.value}" for cookie in jar if "douyin.com" in cookie.domain]
        return "; ".join(cookie_pairs)

    def _apply_cookie_options(self, options: dict, cookie_header: str = "") -> None:
        if cookie_header.strip():
            options.setdefault("http_headers", {})
            options["http_headers"]["Cookie"] = cookie_header.strip()
            return

        cookies_file = settings.douyin_cookies_file
        if cookies_file and cookies_file.exists():
            options["cookiefile"] = str(cookies_file)
            return

        if settings.douyin_cookies_browser:
            options["cookiesfrombrowser"] = (settings.douyin_cookies_browser,)


douyin_service = DouyinService()
