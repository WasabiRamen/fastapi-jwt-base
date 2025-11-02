from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.requests import Request

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.core import security
from app.accounts import crud, schemas
from app.core.database import get_db
from app.accounts import service

from app.auth.exceptions import (
    InvalidTokenException
)

router = APIRouter(tags=["accounts"])


@router.post("/")
async def create_user(
    user: schemas.CreateUser, 
    db: AsyncSession = Depends(get_db)
):
    """사용자 생성"""
    return service.create_user(db, user.user_id, user.password)


@router.get("/me")
async def read_users_me(
    request: Request,
):
    """현재 사용자 정보 조회"""
    return await service.me(request)
