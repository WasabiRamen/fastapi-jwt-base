from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class RedisSettings(BaseSettings):
    """Redis 설정"""

    REDIS_HOST: str = Field("localhost", description="Redis 호스트")
    REDIS_PORT: int = Field(6379, description="Redis 포트")
    REDIS_DB: int = Field(0, description="Redis 데이터베이스 번호")
    REDIS_USER: str = Field("", description="Redis 사용자 이름 (없으면 빈 문자열)")
    REDIS_PASSWORD: str = Field("", description="Redis 비밀번호 (없으면 빈 문자열)")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[5] / "config" / ".env.redis",
        env_file_encoding="utf-8"
    )
redis_settings = RedisSettings()
