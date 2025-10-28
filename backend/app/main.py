from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import router as v1_router
from app.core.database import init_db, close_db
# from app.core.redis import init_redis, close_redis

from app.auth.tools.key_manager import JWTSecretKeyManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 전역 리소스 준비
    await init_db(app)
    # await init_redis(app)
    manager = JWTSecretKeyManager()
    await manager.init()
    app.state.jwt_manager = manager

    try:
        yield
    finally:
        manager.scheduler.shutdown(wait=False)
        # Shutdown: 전역 리소스 정리
        await close_db(app)
        # await close_redis(app)


app = FastAPI(lifespan=lifespan)
app.include_router(v1_router, prefix="/api/v1")

# CORS 설정 - HTTP 테스트 가능하도록 설정
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",  # React 개발 서버
#         "http://127.0.0.1:3000",
#         "http://localhost:8000",  # 백엔드 자체 테스트
#         "http://127.0.0.1:8000",
#     ],
#     allow_credentials=True,  # 쿠키 포함 요청 허용
#     allow_methods=["*"],     # 모든 HTTP 메서드 허용
#     allow_headers=["*"],     # 모든 헤더 허용
# )



@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
