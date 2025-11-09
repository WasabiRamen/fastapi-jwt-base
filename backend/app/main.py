# Standard Library
from contextlib import asynccontextmanager

# FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Settings
from app.api.v1.core.settings.app_setting import app_settings
from app.api.v1.core.settings.smtp_setting import smtp_settings
from app.api.v1.core.settings.database_setting import database_settings
from app.api.v1.core.settings.auth_setting import auth_settings

# Core
from app.api.v1.core.database import init_db, close_db, databaseSettings
from app.api.v1.core.redis import init_redis, close_redis
from app.api.v1.core.smtp import AsyncEmailSender

# Tools
from app.api.v1.auth.tools.key_manager import JWTSecretKeyManager

#routers
from app.api.v1 import router as v1_router


database = databaseSettings(
    host=database_settings.DB_HOST,
    port=database_settings.DB_PORT,
    user=database_settings.DB_USER,
    password=database_settings.DB_PASSWORD,
    name=database_settings.DB_NAME,
)

smtp = AsyncEmailSender.AsyncEmailSenderSettings(
    smtp_host=smtp_settings.SMTP_HOST,
    smtp_port=smtp_settings.SMTP_PORT,
    username=smtp_settings.SMTP_USER,
    password=smtp_settings.SMTP_PASSWORD,
    from_email=smtp_settings.SMTP_USER,
    use_tls=True
)

key_manager_settings = JWTSecretKeyManager.setting(
    SECRET_KEY_PATH=auth_settings.SECRET_KEY_PATH,
    SECRET_KEY_ROTATION_DAYS=auth_settings.SECRET_KEY_ROTATION_DAYS
)


from contextlib import asynccontextmanager
import asyncio
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # JWT Key Manager
    manager = JWTSecretKeyManager(
        auth_settings.SECRET_KEY_PATH,
        auth_settings.SECRET_KEY_ROTATION_DAYS
    )
    await manager.init()
    app.state.jwt_manager = manager

    # DB
    await init_db(app, database)

    # Redis
    await init_redis(app)

    # SMTP
    app.state.smtp = AsyncEmailSender(smtp)
    await app.state.smtp.connect()

    try:
        yield
    finally:
        # Shutdown: 전역 리소스 정리 (순서 및 예외 안전성 강화)
        cleanup_tasks = [
            ("SMTP", app.state.smtp.disconnect),
            ("Redis", lambda: close_redis(app)),
            ("DB", lambda: close_db(app)),
            ("Scheduler", lambda: asyncio.to_thread(manager.scheduler.shutdown, wait=True)),
        ]
        for name, task in cleanup_tasks:
            try:
                await task()
            except Exception as e:
                logging.exception(f"[Shutdown] Failed to close {name}: {e}")


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


@app.get("/health", description="Health Check")
def read_root():
    """헬스체크 엔드포인트"""
    return {"Health": "OK"}
