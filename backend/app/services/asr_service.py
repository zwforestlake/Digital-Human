import subprocess
from pathlib import Path

import imageio_ffmpeg


class AsrService:
    def extract_audio(self, video_path: Path, project_dir: Path) -> Path:
        if not video_path.exists():
            raise RuntimeError(f"Source video does not exist: {video_path}")

        audio_dir = project_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / "source.wav"
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-acodec",
            "pcm_s16le",
            str(audio_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown ffmpeg error").strip()
            raise RuntimeError(f"Audio extraction failed: {detail[-800:]}")
        return audio_path


asr_service = AsrService()
