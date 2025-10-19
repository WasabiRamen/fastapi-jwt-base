import dotenv
import os
from typing import AsyncGenerator, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


dotenv.load_dotenv()

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = 'localhost' if os.getenv("LOCAL") else os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT", "5432")
db = os.getenv("POSTGRES_DB")

# 비동기용 데이터베이스 URL로 변경
database_url = (
    f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
)

# 비동기 엔진 생성
engine = create_async_engine(
    database_url,
    pool_recycle=1800,    # 30분
    pool_pre_ping=True,  
    pool_size=10,         
    max_overflow=20
)

# 비동기 세션 생성
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=True,
    bind=engine,
    class_=AsyncSession
)
Base = declarative_base()

# 비동기 DB 세션 의존성
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db(app) -> None:
    """
    Lifespan에서 호출: 엔진/세션메이커를 1회 생성하여 app.state에 저장
    """
    engine: AsyncEngine = create_async_engine(
        database_url,
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

    # 필요 시 여기서 스키마 생성 등 초기화
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db(app) -> None:
    """
    Lifespan 종료 시 호출: 엔진 정리
    """
    engine: Optional[AsyncEngine] = getattr(app.state, "db_engine", None)
    if engine is not None:
        await engine.dispose()

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    요청 단위 의존성: 세션을 열고, 요청 처리 후 자동 닫기
    """
    SessionLocal = request.app.state.async_session_maker
    async with SessionLocal() as session:
        yield session

# 간단한 DB 헬스체크 쿼리 예시 유틸
async def db_healthcheck(session: AsyncSession) -> bool:
    result = await session.execute(text("SELECT 1"))
    return (result.scalar() == 1)
