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


# class appSettings(BaseSettings):
#     """애플리케이션 전반 설정"""

#     APP_NAME: str = Field("FastAPI JWT Example", description="애플리케이션 이름")
#     APP_VERSION: str = Field("0.0.0", description="애플리케이션 버전")
#     DEBUG: bool = Field(False, description="디버그 모드 활성화 여부")
#     CORS_ORIGINS: list[str] = Field([], description="허용된 CORS 출처 목록")


# class RedisSettings(BaseSettings):
#     """Redis 설정"""

#     REDIS_HOST: str = Field("localhost", description="Redis 호스트")
#     REDIS_PORT: int = Field(6379, description="Redis 포트")
#     REDIS_DB: int = Field(0, description="Redis 데이터베이스 번호")


# # --------------------------------------------------------------
# class AccessTokenSecretSettings(BaseSettings):
#     SECRET_KEY_PATH: str = Field(
#         os.path.join(os.path.dirname(os.path.dirname(__file__)), "secrets", "secret.key"),
#         description='액세스 토큰 비밀 키 파일 경로'
#     )
#     SECRET_KEY_ROTATION_DAYS: int = Field(30, description="액세스 토큰 비밀 키 교체 주기 (일)")


# class AccessTokenSettings(BaseSettings):
#     """Access Token Settings (Json Web Token)"""
#     EXPIRES_IN_SECONDS: int = Field(60 * 15, description="액세스 토큰 만료 시간 (초)")

# class RefreshTokenSettings(BaseSettings):
#     """Refresh Token Settings (Json Web Token)"""

#     EXPIRES_IN_SECONDS: int = Field(60 * 60 * 24 * 7, description="리프레시 토큰 만료 시간 (초)")

# # --------------------------------------------------------------

# class CookieSettings(BaseSettings):
#     """쿠키 설정"""

#     SECURE: bool = Field(True, description="보안 쿠키 사용 여부")
#     HTTP_ONLY: bool = Field(True, description="HTTP 전용 쿠키 사용 여부")
#     SAME_SITE: str = Field("Lax", description="SameSite 속성 설정")