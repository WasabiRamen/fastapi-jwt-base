from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
import app.schemas.user as user_schema
import app.crud.user as user_crud
import app.core.security as security



router = APIRouter(prefix="/api/v1/users", tags=["users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")

def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xrip = request.headers.get("x-real-ip")
    if xrip:
        return xrip
    if request.client:
        return request.client.host
    return ""


@router.post("/token")
async def create_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:

    # 각종 정보 확인 (아이디, 비밀번호 등)
    user_exist = await user_crud.exist_user_by_id(db, form_data.username)
    if not user_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자 아이디입니다."
        )

    user_query = await user_crud.verify_password(db, form_data.username, form_data.password)
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다."
        )

    resp = JSONResponse({"access_token": access_token, "token_type": "bearer"})

    access_token, expires, max_age = await security.JWTManager.create_token(user_query.uuid)

    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,        # 배포 시 True로 변경 (HTTPS 필요)
        samesite="lax",
        expires=expires,
        max_age=max_age,
        path="/"
    )

    refresh_token, expires, max_age = await user_crud.create_refresh_token(
        db,
        user_query.uuid,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
        )

    resp.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,        # 배포 시 True로 변경 (HTTPS 필요)
        samesite="lax",
        expires=expires,
        max_age=max_age,
        path="/"
    )
    return resp


# @router.post("/refresh")
# async def refresh_token():
#     """리프래시 토큰으로 액세스 토큰 재발급"""
#     pass


# @router.delete("/logout")
# async def logout(
#     db: AsyncSession = Depends(get_db),
#     token: str = Depends(oauth2_scheme)
# ):
#     """로그아웃 처리 (리프래시 토큰 비활성화)"""
#     pass

# @router.put("/password")
# async def change_password():
#     # Access Token 확인 및 비밀번호 변경
#     pass


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


@router.get("/exist/{user_id}")
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


@router.get("/me")
async def get_user_info(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """토큰으로 사용자 정보 조회"""
    payload = await security.JWTManager.verify_token(token)
    user_uuid = payload.get("sub")
    if user_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )
    user = await user_crud.get_user_by_uuid(db, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return {"user_id": user.user_id, "uuid": str(user.uuid)}
