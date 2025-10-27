from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.requests import Request

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.auth import service

router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


@router.post('/token')
async def create_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    로그인 하여 액세스 토큰 및 리프래시 토큰 발급
    """

    return await service.create_token(request, db, form_data)


@router.post('/token/refresh')
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """리프래시 토큰으로 액세스 토큰 재발급"""
    return await service.rotate_refresh_token(request, db)


@router.delete("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await service.logout(request, db)