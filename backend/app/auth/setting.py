from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

class AuthSettings(BaseSettings):
    # PassWord Manager Settings
    BCRYPT_ROUNDS: int = Field(12, description="Bcrypt 해싱 라운드 수")

    # Key Manager Settings
    SECRET_KEY_PATH: str = Field("./app/auth/tools/jwt_secret.key", description="JWT 비밀 키 파일 경로")
    SECRET_KEY_ROTATION_DAYS: int = Field(30, description="JWT 비밀 키 교체 주기 (일)")

    # JWT Manager Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(15, description="액세스 토큰 만료 시간 (분)")
    
    # Refresh Token Settings
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, description="리프레시 토큰 만료 시간 (일)")
    REFRESH_TOKEN_STORE_HASHED: bool = Field(False, description="리프레시 토큰 해시 저장 여부")
    REFRESH_TOKEN_BYTE_LENGTH: int = Field(32, description="리프레시 토큰 바이트 길이")

    # Token Cookie Settings
    TOKEN_COOKIE_SECURE: bool = Field(False, description="토큰 쿠키의 Secure 속성 설정 (배포 시 True로 변경)")
    TOKEN_COOKIE_SAMESITE: str = Field("lax", description="토큰 쿠키의 SameSite 속성 설정")
    TOKEN_COOKIE_PATH: str = Field("/", description="토큰 쿠키의 경로 설정")

    # Email Verification Settings
    EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES: int = Field(10, description="이메일 인증 토큰 만료 시간 (분)")
    EMAIL_VERIFY_CODE_LENGTH: int = Field(16, description="이메일 인증 코드 길이")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / "config" / ".env.auth",
        env_file_encoding="utf-8"
    )

setting = AuthSettings()