from datetime import datetime, timezone

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.account import User, RefreshToken

import app.core.security as security


def ts_to_dt(timestamp: int):
    """타임스탬프를 datetime 객체로 변환"""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

async def get_users(db: AsyncSession, 
                    skip: int = 0, limit: int = 10):
    """사용자 목록 조회"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def get_user_by_uuid(db: AsyncSession, uuid: str):
    """UUID로 사용자 조회"""
    result = await db.execute(select(User).where(User.uuid == uuid))
    return result.scalars().first()


async def exist_user_by_id(db: AsyncSession, user_id: str):
    """ID 중복사용 확인"""
    result = await db.execute(select(User).where(User.user_id == user_id))

    return True if result.scalars().first() else False


async def create_user(db: AsyncSession, user_id, password):
    hash_password = security.PasswordManager.encrypt_password(password)
    db_user = User(user_id=user_id, password=hash_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def verify_password(db: AsyncSession, user_id: str, plain_password: str):
    """사용자 인증"""
    result = await db.execute(select(User).where(User.user_id == user_id))
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


async def deactivate_refresh_token(db: AsyncSession, uuid: str, refresh_token: str) -> None:
    """리프래시 토큰 비활성화"""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.refresh_token == refresh_token,
            RefreshToken.is_active == True
        )
    )
    db_token = result.scalars().first()
    if not db_token:
        return

    # 동일한 uuid이면 해당 토큰만 비활성화
    if db_token.uuid == uuid:
        db_token.is_active = False
        db.add(db_token)
        await db.commit()
        return

    # uuid 불일치: 해당 토큰의 uuid와 연관된 모든 활성 토큰 비활성화
    result_all = await db.execute(
        select(RefreshToken).where(
            RefreshToken.uuid == db_token.uuid,
            RefreshToken.is_active == True
        )
    )
    for token in result_all.scalars().all():
        token.is_active = False
        db.add(token)
    await db.commit()


async def validate_refresh_token(db: AsyncSession, uuid: str, refresh_token: str) -> bool:
    """리프래시 토큰 유효성 검사"""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.uuid == uuid,
            RefreshToken.is_active == True,
            RefreshToken.expires_at > datetime.now(timezone.utc)
        )
    )
    db_tokens = result.scalars().all()

    validate = False
    for token in db_tokens:
        if security.RefreshTokenManager.verify_token(refresh_token, token.refresh_token):
            validate = True
            break

    return validate


async def change_password(db: AsyncSession, user_id: str, new_password: str) -> None:
    """비밀번호 변경"""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalars().first()
    hash_password = security.PasswordManager.encrypt_password(new_password)
    user.password = hash_password
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user