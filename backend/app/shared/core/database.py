# backend/auth/app/database.py
import os
from typing import AsyncGenerator, Optional
from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
from pydantic import BaseModel, Field
from loguru import logger
from urllib.parse import quote_plus


# 데이터베이스 init 할 때 필요 config
class DatabaseSettings(BaseModel):
    host: str = Field(..., description="데이터베이스 호스트")
    port: int = Field(..., description="데이터베이스 포트")
    user: str = Field(..., description="데이터베이스 사용자 이름")
    password: str = Field(..., description="데이터베이스 비밀번호")
    name: str = Field(..., description="데이터베이스 이름")


def get_database_url(setting: DatabaseSettings) -> str:
    # 사용자/비밀번호에 특수문자가 포함될 수 있으므로 인코딩
    user = quote_plus(setting.user)
    password = quote_plus(setting.password)
    return f"postgresql+asyncpg://{user}:{password}@{setting.host}:{setting.port}/{setting.name}"

Base = declarative_base()


async def init_db(app: FastAPI, setting: DatabaseSettings) -> None:
    """
    Lifespan에서 호출: 엔진/세션메이커를 1회 생성하여 app.state에 저장
    """
    engine: AsyncEngine = create_async_engine(
        get_database_url(setting),
        pool_pre_ping=True,  # 끊어진 커넥션 자동 감지
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    app.state.db_engine = engine
    app.state.async_session_maker = SessionLocal

    # 스키마 자동 생성(개발 환경에서만 사용 권장)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        logger.exception("DB schema create_all 실패")

    logger.info(f"DB Successfully connected : {setting.host}")


async def close_db(app: FastAPI) -> None:
    """
    Lifespan 종료 시 호출: 엔진 정리
    """
    engine: Optional[AsyncEngine] = getattr(app.state, "db_engine", None)
    if engine is not None:
        logger.info(f"DB Successfully disconnected")
        await engine.dispose()

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    요청 단위 의존성: 세션을 열고, 요청 처리 후 자동 닫기
    """
    SessionLocal = getattr(request.app.state, "async_session_maker", None)
    if SessionLocal is None:
        raise RuntimeError("Async session maker is not initialized on app.state")
    async with SessionLocal() as session:
        yield session


# 간단한 DB 헬스체크 쿼리 예시 유틸
async def db_healthcheck(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT 1"))
    return (result.scalar() == 1)
