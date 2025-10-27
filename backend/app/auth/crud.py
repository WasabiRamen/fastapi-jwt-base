from datetime import datetime, timezone

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.models import User
from app.auth.models import RefreshToken

from app.auth.core import security
from app.auth.schemas import RefreshTokenResponse
from app.auth.exceptions import InvalidTokenException

def ts_to_dt(timestamp: int):
    """타임스탬프를 datetime 객체로 변환"""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)

async def create_refresh_token(
        db: AsyncSession, 
        user_uuid: str, 
        ip_address: str = None, 
        user_agent: str = None
        ) -> RefreshTokenResponse:
    """리프래시 토큰 생성 및 저장"""
    # 기존 활성화된 토큰 비활성화
    db_query = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_uuid == user_uuid,
            RefreshToken.is_active == True
        )
    )

    for token in db_query.scalars().all():
        token.is_active = False
        db.add(token)
    await db.commit()

    # 새로운 리프래시 토큰 생성
    refresh = security.RefreshTokenManager.create_token(user_uuid=str(user_uuid))

    db_refresh_token = RefreshToken(
        refresh_token=refresh.token,
        user_uuid=user_uuid,
        expires_at=ts_to_dt(refresh.expires_at),
        created_at=ts_to_dt(refresh.created_at),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_refresh_token)
    await db.commit()
    await db.refresh(db_refresh_token)
    return refresh


async def rotate_refresh_token(
        db: AsyncSession,
        refresh_token: str,
        user_uuid: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> RefreshTokenResponse:
    """리프래시 토큰 재발급(로테이션)"""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.refresh_token == refresh_token,
            RefreshToken.is_active == True
        )
    )
    db_token = result.scalars().first()

    # 토큰이 DB상 존재하지 않음
    if not db_token:
        raise InvalidTokenException("리프래시 토큰이 유효하지 않습니다.")

    # 만료된 토큰일 경우
    now_utc = datetime.now(timezone.utc).timestamp()

    db_token.is_active = False

    if db_token.expires_at.timestamp() < now_utc:
        raise InvalidTokenException("리프래시 토큰이 만료되었습니다.")
    
    # access_token에서 user_uuid와 비교
    if str(db_token.user_uuid) != str(user_uuid):
        raise InvalidTokenException("리프래시 토큰의 소유자 정보가 일치하지 않습니다.")

    # 검증 완료
    refresh = security.RefreshTokenManager.create_token(user_uuid=str(db_token.user_uuid))

    db_refresh_token = RefreshToken(
        refresh_token=refresh.token,
        user_uuid=db_token.user_uuid,
        expires_at=ts_to_dt(refresh.expires_at),
        created_at=ts_to_dt(refresh.created_at),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_refresh_token)
    db.add(db_token)
    await db.commit()
    await db.refresh(db_refresh_token)

    return refresh

async def get_refresh_token_user_uuid(db: AsyncSession, refresh_token: str):
    """리프래시 토큰 조회"""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.refresh_token == refresh_token,
            RefreshToken.is_active == True
        )
    )
    db_token = result.scalars().first()
    return db_token.user_uuid if db_token else None


async def deactivate_refresh_token(db: AsyncSession, refresh_token: str) -> None:
    """리프래시 토큰 비활성화"""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.refresh_token == refresh_token,
            RefreshToken.is_active == True
        )
    )
    db_token = result.scalars().first()
    if not db_token:
        return ''

    db_token.is_active = False
    db.add(db_token)
    await db.commit()
