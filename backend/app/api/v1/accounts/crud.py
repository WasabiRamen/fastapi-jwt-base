from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.accounts.models import Account
from app.api.v1.auth.service import create_auth_user

async def create_account(
        db: AsyncSession,
        user_name: str,
        email: str,
        user_uuid: str,
        phone_number: str | None = None,
    ) -> Account:
    """새로운 계정 생성"""
    new_account = Account(
        user_uuid=user_uuid,
        user_name=user_name,
        email=email,
        phone_number=phone_number,
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account


async def get_account_by_uuid(
        db: AsyncSession,
        user_uuid: str,
    ) -> Account | None:
    """user_uuid로 계정 조회"""
    result = await db.execute(
        select(Account).where(Account.user_uuid == user_uuid)
    )
    account = result.scalars().first()
    return account