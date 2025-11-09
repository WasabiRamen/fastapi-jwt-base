import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class appSettings(BaseSettings):
    """애플리케이션 전반 설정"""

    APP_NAME: str = Field("HiLi FastAPI OAuth2.0 Boilerplate", description="애플리케이션 이름")
    APP_VERSION: str = Field("0.0.0", description="애플리케이션 버전")  # 미완성이라 0.0.0
    CORS_ORIGINS: str = Field("", description="허용된 CORS 출처 목록 (콤마로 구분된 문자열)")
    CORS_ALLOW_CREDENTIALS: bool = Field(True, description="CORS credentials 허용 여부")
    LOG_LEVEL: str = Field("INFO", description="로그 레벨")
    LOG_FILE_PATH: str = Field("logs/app.log", description="로그 파일 경로")
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[5] / "config" / ".env.app",
        env_file_encoding="utf-8"
    )

app_settings = appSettings()
