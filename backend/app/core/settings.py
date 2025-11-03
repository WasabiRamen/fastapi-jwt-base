import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""

    DB_HOST: str = Field("localhost", description="데이터베이스 호스트")
    DB_PORT: int = Field(5432, description="데이터베이스 포트")
    DB_USER: str = Field("postgres", description="데이터베이스 사용자 이름")
    DB_PASSWORD: str = Field("postgres", description="데이터베이스 비밀번호")
    DB_NAME: str = Field("app_db", description="데이터베이스 이름")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / "config" / ".env.database",
        env_file_encoding="utf-8"
    )

database_setting = DatabaseSettings()

class RedisSettings(BaseSettings):
    """Redis 설정"""

    REDIS_HOST: str = Field("localhost", description="Redis 호스트")
    REDIS_PORT: int = Field(6379, description="Redis 포트")
    REDIS_DB: int = Field(0, description="Redis 데이터베이스 번호")
    REDIS_PASSWORD: str = Field("", description="Redis 비밀번호 (없으면 빈 문자열)")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / "config" / ".env.redis",
        env_file_encoding="utf-8"
    )
redis_settings = RedisSettings()


class appSettings(BaseSettings):
    """애플리케이션 전반 설정"""

    APP_NAME: str = Field("HiLi FastAPI OAuth2.0 Boilerplate", description="애플리케이션 이름")
    APP_VERSION: str = Field("0.0.0", description="애플리케이션 버전")  # 미완성이라 0.0.0
    CORS_ORIGINS: str = Field("", description="허용된 CORS 출처 목록 (콤마로 구분된 문자열)")
    CORS_ALLOW_CREDENTIALS: bool = Field(True, description="CORS credentials 허용 여부")
    LOG_LEVEL: str = Field("INFO", description="로그 레벨")
    LOG_FILE_PATH: str = Field("logs/app.log", description="로그 파일 경로")
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / "config" / ".env.app",
        env_file_encoding="utf-8"
    )

app_settings = appSettings()


class smtpSettings(BaseSettings):
    """SMTP 설정"""

    SMTP_HOST: str = Field("smtp.gmail.com", description="SMTP 호스트")
    SMTP_PORT: int = Field(587, description="SMTP 포트")
    SMTP_USER: str = Field(..., description="SMTP 사용자 이름")
    SMTP_PASSWORD: str = Field(..., description="SMTP 비밀번호")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / "config" / ".env.smtp",
        env_file_encoding="utf-8"
    )
smtp_settings = smtpSettings()