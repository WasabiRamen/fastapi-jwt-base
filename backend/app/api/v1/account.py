from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.cookie import CookieManager
import app.schemas.account as account_schema
import app.crud.account as account_crud
import app.core.security as security


router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/token")


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
    user_exist = await account_crud.exist_user_by_id(db, form_data.username)
    if not user_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자 아이디입니다."
        )

    user_query = await account_crud.verify_password(db, form_data.username, form_data.password)
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다."
        )

    access_token, expires, max_age = await security.JWTManager.create_token(user_query.uuid)
    resp = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    resp = CookieManager.set_access_token_cookie(resp, access_token, expires, max_age)

    refresh_token, expires, max_age = await account_crud.create_refresh_token(
        db,
        user_query.uuid,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
        )
    resp = CookieManager.set_refresh_token_cookie(resp, refresh_token, expires, max_age)
    return resp


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """리프래시 토큰으로 액세스 토큰 재발급"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프래시 토큰이 존재하지 않습니다."
        )

    payload = await security.JWTManager.verify_token(refresh_token)
    user_uuid = payload.get("sub")
    if user_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프래시 토큰입니다."
        )

    is_valid = await account_crud.validate_refresh_token(db, user_uuid, refresh_token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프래시 토큰입니다."
        )

    await account_crud.deactivate_refresh_token(db, user_uuid, refresh_token)

    access_token, expires, max_age = await security.JWTManager.create_token(user_uuid)
    resp = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    resp = CookieManager.set_access_token_cookie(resp, access_token, expires, max_age)
    refresh_token, expires, max_age = await account_crud.create_refresh_token(
        db,
        user_uuid,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
        )
    resp = CookieManager.set_refresh_token_cookie(resp, refresh_token, expires, max_age)
    return resp



@router.delete("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    user_uuid = None
    if access_token:
        try:
            payload = await security.JWTManager.verify_token(access_token)
            user_uuid = payload.get("sub")
        except HTTPException:
            pass
    
    if user_uuid and refresh_token:
        await account_crud.deactivate_refresh_token(db, user_uuid, refresh_token)

    resp = JSONResponse({"message": "로그아웃 되었습니다."})
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")
    return resp


@router.post("/verify_password")
async def verify_password(
    user: account_schema.VerifyPassword,
    db: AsyncSession = Depends(get_db)
):
    """사용자 인증"""
    user_query = await account_crud.verify_password(db, user.user_비id, user.password)
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다."
        )
    return {"message": "비밀번호가 일치합니다."}


@router.put("/password")
async def change_password(
    user: account_schema.ChangePassword,
    db: AsyncSession = Depends(get_db)
):
    user_query = await account_crud.verify_password(db, user.user_id, user.old_password)
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="기존 비밀번호가 일치하지 않습니다."
        )

    if user.old_password == user.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="기존 비밀번호와 동일한 비밀번호로 변경할 수 없습니다."
        )
    await account_crud.change_password(db, user.user_id, user.new_password)
    return {"message": "비밀번호가 변경되었습니다."}


@router.post("/")
async def create_user(
    user: account_schema.UserCreate, 
    db: AsyncSession = Depends(get_db)
):
    """사용자 생성"""
    exist_user = await account_crud.exist_user_by_id(db, user.user_id)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 사용자 아이디입니다."
        )
    await account_crud.create_user(db, user.user_id, user.password)
    return {"message": "사용자가 생성되었습니다."}


@router.get("/exist/{user_id}")
async def exist_user_id(
    user_id: str, 
    db: AsyncSession = Depends(get_db)
):
    user = await account_crud.exist_user_by_id(db, user_id)
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
    user = await account_crud.get_user_by_uuid(db, user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return {"user_id": user.user_id, "uuid": str(user.uuid)}
