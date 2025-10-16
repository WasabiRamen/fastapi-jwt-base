from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Member

import app.core.security as security

async def get_users(db: AsyncSession, 
                    skip: int = 0, limit: int = 10):
    """사용자 목록 조회"""
    result = await db.execute(select(Member).offset(skip).limit(limit))
    return result.scalars().all()


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