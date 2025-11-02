from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.accounts.models import User

from app.auth.core import security

async def create_user(db: AsyncSession, user_id, password):
    hash_password = security.PasswordManager.encrypt_password(password)
    db_user = User(user_id=user_id, password=hash_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_user_id(db: AsyncSession, user_id: str):
    """ID로 사용자 조회"""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalars().first()

async def get_user_by_user_uuid(db: AsyncSession, user_uuid: str):
    """UUID로 사용자 조회"""
    result = await db.execute(select(User).where(User.user_uuid == user_uuid))
    return result.scalars().first()