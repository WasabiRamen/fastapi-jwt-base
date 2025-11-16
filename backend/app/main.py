# Standard Library
import asyncio
from contextlib import asynccontextmanager

# Third Party
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# FastAPI
from fastapi import FastAPI, Depends
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware

# Settings
from app.shared.core.settings import (
    get_database_runtime,
    get_redis_runtime,
    get_smtp_runtime,
    get_auth_settings,
    get_app_settings,
    get_cors_settings
)

# Core
from app.shared.core.database import (
    init_db,
    close_db,
    get_db,
    db_healthcheck
)
from app.shared.core.redis import (
    init_redis,
    close_redis
)
from app.shared.core.async_mail_client import AsyncEmailClient

# Services
from app.service.auth.core.security import JWTSecretService
from app.service.auth import router as auth_router
from app.service.accounts import router as accounts_router


auth_settings = get_auth_settings()
smtp_runtime = get_smtp_runtime()
app_settings = get_app_settings()
cors_settings = get_cors_settings()
database_runtime = get_database_runtime()
redis_runtime = get_redis_runtime()
smtp_runtime = get_smtp_runtime()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # JWT Key Manager
    manager = JWTSecretService(
        auth_settings.SECRET_KEY_PATH,
        auth_settings.SECRET_KEY_ROTATION_DAYS
    )
    await manager.init()
    app.state.jwt_manager = manager

    # DB
    await init_db(app, database_runtime)

    # Redis
    await init_redis(app, redis_runtime)

    # SMTP
    app.state.smtp = AsyncEmailClient(smtp_runtime)
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
                logger.error(f"[Shutdown] Failed to close {name}: {e}")


# app Instance
app = FastAPI(
    title=app_settings.NAME,
    version=app_settings.VERSION,
    lifespan=lifespan,
    prefix="/api"
    )

# Bind Routers
app.include_router(auth_router)
app.include_router(accounts_router)

# CORS 설정 - HTTP 테스트 가능하도록 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.origins_list,  # 허용할 출처 목록
    allow_credentials=cors_settings.ALLOW_CREDENTIALS,  # 쿠키 포함 요청 허용
    allow_methods=["*"],     # 모든 HTTP 메서드 허용
    allow_headers=["*"],     # 모든 헤더 허용
)


@app.get("/health", description="Health Check")
async def read_root(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """헬스체크 엔드포인트"""
    db_health = await db_healthcheck(db)
    react_health = request.app.state.redis.ping()

    return {
        "status": "ok",
        "database": "ok" if db_health else "error",
        "redis": "ok" if react_health else "error"
    }
