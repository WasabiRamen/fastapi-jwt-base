from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
import app.schemas.user as user_schema
import app.crud.user as user_crud


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/")
async def read_users(
    params: user_schema.UserRead = Depends(), 
    db: AsyncSession = Depends(get_db)
    ):
    return await user_crud.get_users(db, skip=params.skip, limit=params.limit)


@router.post("/")
async def create_user(
    user: user_schema.UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """사용자 생성"""
    exist_user = await user_crud.exist_user_by_id(db, user.user_id)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자 아이디입니다."
        )
    await user_crud.create_user(db, user.user_id, user.password)
    return {"message": "사용자가 생성되었습니다."}


async def exist_user_id(
    user_id: str, 
    db: AsyncSession = Depends(get_db)
):
    user = await user_crud.exist_user_by_id(db, user_id)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자 아이디입니다."
        )
    return True


@router.post("/token")
async def create_token(
    user: user_schema.CreateToken, 
    db: AsyncSession = Depends(get_db)
):
    """토큰 생성"""
    # 각종 정보 확인 (아이디, 비밀번호 등)
    user_query = await user_crud.exist_user_by_id(db, user.user_id)
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자 아이디입니다."
        )
    if user_crud.verify_password(db, user.user_id, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다."
        )

    # 토큰 생성 로직 추가 예정
    return True
