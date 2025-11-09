# Standard library imports
import json
from datetime import datetime, timezone

# Third-party imports
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# FastAPI imports
from fastapi.requests import Request

# App imports
from app.api.v1.accounts import crud
from app.api.v1.auth.service import create_auth_user


async def create_account(
    request: Request,
    db: AsyncSession,
    user_id: str,
    password: str,
    user_name: str,
    email: str,
    email_token: str,
    phone_number: str
):
    """
    계정 생성 서비스

    프로필 생성 -> 인증생성
    """
    logger.info(f"Creating account for user_id: {user_id}")
    auth_user = await create_auth_user(
        db=db,
        user_id=user_id,
        password=password,
        email=email,
        email_token=email_token,
    )

    new_account = await crud.create_account(
        db=db,
        user_name=user_name,
        email=email,
        user_uuid=user_uuid,
        phone_number=phone_number
    )
    logger.info(f"Account created successfully for user_id: {user_id}")
    return new_account