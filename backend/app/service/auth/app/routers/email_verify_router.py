# auth/routers/email_verify_router.py
# FastAPI imports
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

# SQLAlchemy & Third Party imports
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# App imports
from .. import service, schemas

# Shared imports
from app.shared.core.redis import Redis, get_redis
from app.shared.core.async_mail_client import get_smtp_client, AsyncEmailClient
from app.shared.core.database import get_db

# ------------------------- Email Router -------------------------

email_verify_router = APIRouter(prefix="/email")

@email_verify_router.post("")
async def send_email_verification(
    form: schemas.SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    smtp: AsyncEmailClient = Depends(get_smtp_client)
):
    """이메일 인증 토큰 및 코드 발급"""
    result = await service.send_email_verification(db, redis, smtp, form.email)
    logger.info(f"Email verification sent to '{form.email}'.")
    return result


@email_verify_router.post("/verify")
async def verify_email_code(
    form: schemas.VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """이메일 인증 코드 검증"""
    result = await service.verify_email_token(db, redis, form.token, form.code)
    logger.info(f"Email verification token checked for token '{form.token}'.")
    return result