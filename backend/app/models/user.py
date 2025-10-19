from sqlalchemy import Column, Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from uuid import uuid4


class Member(Base):
    __tablename__ = 'member'

    uuid = Column(UUID(as_uuid=True), default=uuid4)
    user_id = Column(String, primary_key=True)       # 사용자 아이디
    password = Column(String, nullable=False)
    user_name = Column(String)  # 닉네임
    phone_number = Column(String)               # 휴대폰 번호 (인증 필요)
    email = Column(String)      # 이메일 주소 (인증 필요)
    super_user = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)   # 휴먼 및 탈퇴 여부


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    refresh_token = Column(String, nullable=False, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_agent = Column(String)
    ip_address = Column(String)
    is_active = Column(Boolean, default=True)  # 토큰 활성화 여부