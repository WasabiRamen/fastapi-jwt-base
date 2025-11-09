import os
from typing import Optional

from fastapi import Request
from redis.asyncio import Redis
from loguru import logger

from app.api.v1.core.settings.redis_setting import redis_settings

DEFAULT_REDIS_URL = f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}/{redis_settings.REDIS_DB}"

if redis_settings.REDIS_PASSWORD:
    if redis_settings.REDIS_USER:
        DEFAULT_REDIS_URL = f"redis://{redis_settings.REDIS_USER}:{redis_settings.REDIS_PASSWORD}@{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}/{redis_settings.REDIS_DB}"
    else:
        DEFAULT_REDIS_URL = f"redis://:{redis_settings.REDIS_PASSWORD}@{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}/{redis_settings.REDIS_DB}"

async def init_redis(app) -> None:
    """
    Lifespan에서 호출: Redis 클라이언트를 1회 생성하여 app.state에 저장
    """
    url = DEFAULT_REDIS_URL
    redis = Redis.from_url(
        url,
        encoding="utf-8",
        decode_responses=True,  # 문자열 편의
        health_check_interval=30,
    )
    # 연결 확인(옵션)
    await redis.ping()

    logger.info(f"Redis Successfully connected : {redis_settings.REDIS_HOST}")
    app.state.redis = redis

async def close_redis(app) -> None:
    """
    Lifespan 종료 시 호출: Redis 클라이언트/풀 정리
    """
    redis: Optional[Redis] = getattr(app.state, "redis", None)
    if redis is not None:
        # redis-py 5.x: close() + connection_pool.disconnect() 권장
        logger.info(f"Redis Successfully disconnected : {redis_settings.REDIS_HOST}")
        await redis.close()
        await redis.connection_pool.disconnect()

async def get_redis(request: Request) -> Redis:
    """
    요청 단위 의존성: 전역 클라이언트를 그대로 참조(풀은 내부에서 관리)
    """
    return request.app.state.redis