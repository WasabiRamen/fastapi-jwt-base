from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class DatabaseSettings(BaseSettings):
    """데이터베이스 설정"""

    DB_HOST: str = Field("localhost", description="데이터베이스 호스트")
    DB_PORT: int = Field(5432, description="데이터베이스 포트")
    DB_USER: str = Field("postgres", description="데이터베이스 사용자 이름")
    DB_PASSWORD: str = Field("postgres", description="데이터베이스 비밀번호")
    DB_NAME: str = Field("app_db", description="데이터베이스 이름")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[5] / "config" / ".env.database",
        env_file_encoding="utf-8"
    )

database_settings = DatabaseSettings()