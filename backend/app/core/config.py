from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    dashscope_api_key: str = ""
    dashscope_api_host: str = "https://dashscope.aliyuncs.com"
    storage_dir: Path = Path("./storage")
    export_dir: Path = Path("./exports")
    douyin_cookies_file: Path | None = None
    douyin_cookies_browser: str = "chrome"
    allowed_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def dashscope_base_url(self) -> str:
        return self.dashscope_api_host.rstrip("/")

    @property
    def dashscope_http_api_url(self) -> str:
        return f"{self.dashscope_base_url}/api/v1"

    @property
    def dashscope_compatible_api_url(self) -> str:
        return f"{self.dashscope_base_url}/compatible-mode/v1"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
settings.export_dir.mkdir(parents=True, exist_ok=True)
settings.allowed_origins = ",".join(settings.allowed_origin_list)
