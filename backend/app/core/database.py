import dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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