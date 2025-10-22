from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.account import router as user_router
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 전역 리소스 준비
    await init_db(app)
    await init_redis(app)
    try:
        yield
    finally:
        # Shutdown: 전역 리소스 정리
        await close_redis(app)
        await close_db(app)


app = FastAPI(lifespan=lifespan)

# CORS 설정 - HTTP 테스트 가능하도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 개발 서버
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # 백엔드 자체 테스트
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,  # 쿠키 포함 요청 허용
    allow_methods=["*"],     # 모든 HTTP 메서드 허용
    allow_headers=["*"],     # 모든 헤더 허용
)

# Route bindings
app.include_router(user_router)


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.get("/health")
async def health_check():
    try:
        pong = await app.state.redis.ping()
        if pong:
            return {"status": "ok"}
        else:
            return {"status": "error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
