from sqlalchemy import Column, Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from uuid import uuid4


class RefreshToken(Base):
    """리프래시 토큰 로깅 및 검증용 모델"""

    __tablename__ = 'refresh_tokens'

    refresh_token = Column(String, nullable=False, primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), default=uuid4, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(String)
    ip_address = Column(String)
    is_active = Column(Boolean, default=True)  # 토큰 활성화 여부


class OAuthAccount(Base):
    """OAuth 계정 모델"""

    __tablename__ = 'oauth_accounts'

    oauth_id = Column(String, nullable=False, primary_key=True)
    user_uuid = Column(UUID(as_uuid=True), default=uuid4, nullable=False)
    provider = Column(String, nullable=False)  # 예: 'google', 'facebook' 등
    provider_id = Column(String, nullable=False)  # OAuth 제공자에서의 사용자 ID
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmailVerificationCode(Base):
    """이메일 인증 코드 모델"""

    __tablename__ = 'email_verification_codes'

    token = Column(String, nullable=False, primary_key=True)
    code = Column(String, nullable=False)
    email = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_used = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)