from datetime import datetime, timezone

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Member, RefreshToken

import app.core.security as security


def ts_to_dt(timestamp: int):
    """타임스탬프를 datetime 객체로 변환"""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

async def get_users(db: AsyncSession, 
                    skip: int = 0, limit: int = 10):
    """사용자 목록 조회"""
    result = await db.execute(select(Member).offset(skip).limit(limit))
    return result.scalars().all()


async def get_user_by_uuid(db: AsyncSession, uuid: str):
    """UUID로 사용자 조회"""
    result = await db.execute(select(Member).where(Member.uuid == uuid))
    return result.scalars().first()


async def exist_user_by_id(db: AsyncSession, user_id: str):
    """ID 중복사용 확인"""
    result = await db.execute(select(Member).where(Member.user_id == user_id))

    return True if result.scalars().first() else False


async def create_user(db: AsyncSession, user_id, password):
    hash_password = security.PasswordManager.encrypt_password(password)
    db_user = Member(user_id=user_id, password=hash_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def verify_password(db: AsyncSession, user_id: str, plain_password: str):
    """사용자 인증"""
    result = await db.execute(select(Member).where(Member.user_id == user_id))
    user = result.scalars().first()
    if not security.PasswordManager.verify_password(plain_password, user.password):
        return False
    return user


async def create_refresh_token(
        db: AsyncSession, 
        uuid: str, 
        ip_address: str = None, 
        user_agent: str = None
        ) -> tuple[str, int, int]:
    """리프래시 토큰 생성 및 저장"""
    # 기존 활성화된 토큰 비활성화
    db_query = await db.execute(
        select(RefreshToken).where(
            RefreshToken.uuid == uuid,
            RefreshToken.is_active == True
        )
    )

    for token in db_query.scalars().all():
        token.is_active = False
        db.add(token)
    await db.commit()

    # 새로운 리프래시 토큰 생성
    refresh_token, created_at, expires_at, max_age = await security.RefreshTokenManager.create_token()
    db_refresh_token = RefreshToken(
        refresh_token=refresh_token,
        uuid=uuid,
        expires_at=ts_to_dt(expires_at),
        created_at=ts_to_dt(created_at),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_refresh_token)
    await db.commit()
    await db.refresh(db_refresh_token)
    return db_refresh_token.refresh_token, expires_at, max_age