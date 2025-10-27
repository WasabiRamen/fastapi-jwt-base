from sqlalchemy import Column, Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
from uuid import uuid4


class User(Base):
    """사용자 모델"""
    __tablename__ = 'users'

    user_uuid = Column(UUID(as_uuid=True), default=uuid4)
    user_id = Column(String, primary_key=True)          # 사용자 아이디
    password = Column(String, nullable=False)
    user_name = Column(String)                          # 닉네임
    phone_number = Column(String)                       # 휴대폰 번호 (인증 필요)
    email = Column(String)                              # 이메일 주소 (인증 필요)
    super_user = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)           # 휴먼 및 탈퇴 여부