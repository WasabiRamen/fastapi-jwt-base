from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.cookie import CookieManager
import app.core.security as security
import app.crud.account_crud as account_crud
import app.schemas.account_schemas as account_schema
from app.exceptions.account_exceptions import (
    UserNotFoundException,
    InvalidPasswordException,
    UserAlreadyExistsException,
    TokenNotFoundException,
    InvalidTokenException,
    SamePasswordException
)


router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/accounts/token")

"""
@Todo: IP 주소 가져오는 모듈 -> SecurityManager 등으로 이동 고려
@Todo: /refresh 엔드포인트 리팩토링 고려 (중복 코드 제거)


refresh token 흐름이 잘못됨

_get_client_ip -> 어차피 refresh token 시점에만 필요해서 다른 곳으로 이동
refresh token은 자체적으로 검증이 가능함.
"""



def _get_client_ip(request: Request) -> str:
    """
    클라이언트 IP 주소 가져오기

    우선순위: X-Forwarded-For > X-Real-IP > request.client.host
    """
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
    """
    액세스 토큰 및 리프래시 토큰 발급
    
    OAuth2 폼 사용
    아이디 비밀번호 검증 후 토큰 발급
    """
    user_exist = await account_crud.exist_user_by_id(db, form_data.username)
    if not user_exist:
        raise UserNotFoundException(form_data.username)

    user_query = await account_crud.verify_password(db, form_data.username, form_data.password)
    if not user_query:
        raise InvalidPasswordException()

    access = security.JWTManager.create_token(user_query.uuid)
    refresh = await account_crud.create_refresh_token(db, user_query.uuid, ip_address=_get_client_ip(request), user_agent=request.headers.get("user-agent"))
    resp = JSONResponse({"access_token": access.token, "token_type": "bearer"})
    resp = CookieManager.set_token_cookies(
        resp,
        access.token, access.expires_at, access.expires_in,
        refresh.token, refresh.expires_at, refresh.expires_in
    )
    return resp


@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """리프래시 토큰으로 액세스 토큰 재발급"""
    old_refresh_token = request.cookies.get("refresh_token")
    refresh_token = await account_crud.rotate_refresh_token(db, old_refresh_token, ip_address=_get_client_ip(request), user_agent=request.headers.get("user-agent"))

    if type(refresh_token) == str:
        raise InvalidTokenException(refresh_token)

    access = security.JWTManager.create_token(refresh_token.uuid)
    resp = JSONResponse({"access_token": access.token, "token_type": "bearer"})
    resp = CookieManager.set_token_cookies(
        resp,
        access.token, access.expires_at, access.expires_in,
        refresh_token.token, refresh_token.expires_at, refresh_token.expires_in
    )
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
    resp = CookieManager.delete_token_cookies(resp)
    return resp


@router.post("/verify_password")
async def verify_password(
    user: account_schema.VerifyPassword,
    db: AsyncSession = Depends(get_db)
):
    """사용자 인증"""
    user_query = await account_crud.verify_password(db, user.user_id, user.password)
    if not user_query:
        raise InvalidPasswordException()
    return {"message": "비밀번호가 일치합니다."}


@router.put("/password")
async def change_password(
    user: account_schema.ChangePassword,
    db: AsyncSession = Depends(get_db)
):
    user_query = await account_crud.verify_password(db, user.user_id, user.old_password)
    if not user_query:
        raise InvalidPasswordException()

    if user.old_password == user.new_password:
        raise SamePasswordException()
    
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
        raise UserAlreadyExistsException(user.user_id)
    
    await account_crud.create_user(db, user.user_id, user.password)
    return {"message": "사용자가 생성되었습니다."}


@router.get("/exist/{user_id}")
async def exist_user_id(
    user_id: str, 
    db: AsyncSession = Depends(get_db)
):
    user = await account_crud.exist_user_by_id(db, user_id)
    if user:
        raise UserAlreadyExistsException(user_id)
    return True


@router.get("/me")
async def get_user_info(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """토큰으로 사용자 정보 조회"""
    try:
        payload = security.JWTManager.verify_token(token)
    except ValueError:
        raise InvalidTokenException("액세스 토큰")
        
    user_uuid = payload.get("sub")
    if user_uuid is None:
        raise InvalidTokenException("액세스 토큰")
        
    user = await account_crud.get_user_by_uuid(db, user_uuid)
    if user is None:
        raise UserNotFoundException()
        
    return {"user_id": user.user_id, "uuid": str(user.uuid)}
