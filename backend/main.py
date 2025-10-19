from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1.user import router as user_router
from app.models import user as user_models
from app.core.database import init_db, close_db, get_db, db_healthcheck
from app.core.redis import init_redis, close_redis, get_redis


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
