from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class smtpSettings(BaseSettings):
    """SMTP 설정"""

    SMTP_HOST: str = Field("smtp.gmail.com", description="SMTP 호스트")
    SMTP_PORT: int = Field(587, description="SMTP 포트")
    SMTP_USER: str = Field(..., description="SMTP 사용자 이름")
    SMTP_PASSWORD: str = Field(..., description="SMTP 비밀번호")

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[5] / "config" / ".env.smtp",
        env_file_encoding="utf-8"
    )
smtp_settings = smtpSettings()