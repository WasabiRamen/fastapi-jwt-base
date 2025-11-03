from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.settings import app_settings
from app.core.settings import smtp_settings
from app.auth.tools.async_mailer import AsyncEmailSender
from app.api.v1 import router as v1_router
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis

from app.auth.tools.key_manager import JWTSecretKeyManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # JWT Key Manager
    manager = JWTSecretKeyManager()
    await manager.init()
    app.state.jwt_manager = manager

    # DB
    await init_db(app)

    # Redis
    await init_redis(app)

    # SMTP
    app.state.smtp = AsyncEmailSender(
        smtp_host=smtp_settings.SMTP_HOST,
        smtp_port=smtp_settings.SMTP_PORT,
        username=smtp_settings.SMTP_USER,
        password=smtp_settings.SMTP_PASSWORD,
        from_email=smtp_settings.SMTP_USER,
        use_tls=True
    )
    await app.state.smtp.connect()

    try:
        yield
    finally:
        manager.scheduler.shutdown(wait=False)
        # Shutdown: 전역 리소스 정리
        await close_db(app)
        await close_redis(app)
        await app.state.smtp.disconnect()


app = FastAPI(
    title=app_settings.APP_NAME,
    version=app_settings.APP_VERSION,
    lifespan=lifespan
    )
app.include_router(v1_router, prefix="/api/v1")

# CORS 설정 - HTTP 테스트 가능하도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ORIGINS.split(",") if app_settings.CORS_ORIGINS else [],
    allow_credentials=app_settings.CORS_ALLOW_CREDENTIALS,  # 쿠키 포함 요청 허용
    allow_methods=["*"],     # 모든 HTTP 메서드 허용
    allow_headers=["*"],     # 모든 헤더 허용
)


@app.get("/")
def read_root():
    """헬스체크 엔드포인트"""
    return {"Health": "OK"}
