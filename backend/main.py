from fastapi import FastAPI
from redis import asyncio as aioredis
from contextlib import asynccontextmanager

from app.api.v1.user import router as user_router
from app.models import user as user_models
from app.core.database import engine, get_db

def get_redis_url():
    return "redis://localhost"

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(get_redis_url(), decode_responses=True)
    async with engine.begin() as conn:
        await conn.run_sync(user_models.Base.metadata.create_all)

    yield
    await app.state.redis.close()

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
