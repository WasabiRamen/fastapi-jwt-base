import json

from fastapi import Request, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

import ipaddress

from app.auth.core import security
from app.auth.tools.cookie_manager import TokenCookieManager
from app.auth.exceptions import (
    UserNotFoundException, 
    InvalidPasswordException,
    InvalidTokenException
    )
from app.auth import crud
from app.accounts import crud as account_crud
from app.auth.tools import async_mailer


def _get_client_ip(request: Request) -> str:
    """
    클라이언트 IP 주소 추출

    x-forwarded-for, x-real-ip 헤더 우선, 없으면 request.client.host 사용
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        ip = xff.split(",")[0].strip()
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            pass  # 유효하지 않은 IP는 무시
    xrip = request.headers.get("x-real-ip")
    if xrip:
        try:
            ipaddress.ip_address(xrip)
            return xrip
        except ValueError:
            pass
    if request.client:
        return request.client.host or ""
    return ""


async def create_token(
    request: Request,
    db: AsyncSession,
    form_data: OAuth2PasswordRequestForm,
):
    """
    액세스 토큰 발급
    
    아이디 > 비밀번호 순으로 검증하고 발급
    """
    user = await account_crud.get_user_by_user_id(db, form_data.username)
    if not user:
        raise UserNotFoundException(form_data.username)

    if not security.PasswordManager.verify_password(form_data.password, user.password):
        raise InvalidPasswordException()

    user_ip = _get_client_ip(request)

    access_token = security.JWTManager.create_token(user.user_uuid, request.app)
    refresh_token = await crud.create_refresh_token(
        db,
        user_uuid=user.user_uuid,
        ip_address=user_ip,
        user_agent=request.headers.get("user-agent")
    )

    resp = JSONResponse({"access_token": access_token.token, "token_type": "bearer"})
    resp = TokenCookieManager.set_token_cookies(
        response=resp,
        access_token=access_token,
        refresh_token=refresh_token
    )
    return resp


async def rotate_refresh_token(
    request: Request,
    db: AsyncSession,
):
    """
    TODO:
    - 재사용 감지 (재사용 감지시, 모든 토큰 비활성화 X 혹은 옵션으로 만들 계획)
    - 해당 기기의 토큰만 비활성화
    """
    old_access_token = request.cookies.get("access_token")
    try:
        decode_access_token = security.JWTManager.decode_token_without_expiration(old_access_token, request.app)
    except ValueError:
        raise InvalidTokenException("액세스 토큰이 유효하지 않습니다.")
    
    user_uuid = decode_access_token.get("sub")
    old_refresh_token = request.cookies.get("refresh_token")

    refresh_token = await crud.rotate_refresh_token(
        db,
        old_refresh_token,
        user_uuid=user_uuid,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    access_token = security.JWTManager.create_token(user_uuid, request.app)

    resp = JSONResponse({"access_token": access_token.token, "token_type": "bearer"})
    resp = TokenCookieManager.set_token_cookies(
        response=resp,
        access_token=access_token,
        refresh_token=refresh_token
    )
    return resp


async def logout(
    request: Request,
    db: AsyncSession,
):
    """
    로그아웃 처리

    액세스 토큰과 리프래시 토큰을 비활성화하고 쿠키 삭제
    """
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    access_token_user_uuid = security.JWTManager.decode_token_without_validation(access_token, request.app).get("sub")
    refresh_token_user_uuid = await crud.get_refresh_token_user_uuid(db, refresh_token)

    if str(access_token_user_uuid) != str(refresh_token_user_uuid):
        return "로그 생성 / 이상 징후 감지 필요 / 로그아웃 처리 X"

    await crud.deactivate_refresh_token(db, refresh_token)
    resp = JSONResponse({"message": "로그아웃 되었습니다."})
    resp = TokenCookieManager.delete_token_cookies(response=resp)
    return resp


async def send_email_verification(
    request: Request,
    email: str,
):
    """
    이메일 인증 토큰 및 코드 발급
    """
    verify = security.EmailTokenManager.create_token(email)
    
    body = async_mailer.varification_email_form(
        code=verify.code,
        expiry=verify.expires_in // 60
    )

    await request.app.state.smtp.send_email(
        to=email,
        subject="이메일 인증 안내 — Hilighting",
        body=body,
        subtype="html"
    )

    redis_value = {
            "email": email,
            "code": verify.code,
            "expires_at": verify.expires_at,
            "created_at": verify.created_at
        }

    await request.app.state.redis.set(
        verify.token, 
        json.dumps(redis_value), 
        ex=verify.expires_in
        )

    response_data = {
        "email": email,
        "token": verify.token,
        "expires_at": verify.expires_at,
        "created_at": verify.created_at
    }

    return JSONResponse(response_data)


async def verify_email_token(
    request: Request,
    token: str,
    code: str,
):
    """
    이메일 인증 토큰 및 코드 검증
    """
    redis_data = await request.app.state.redis.get(token)
    if not redis_data:
        raise InvalidTokenException("이메일 인증 토큰이 유효하지 않거나 만료되었습니다.")

    data = json.loads(redis_data)

    if data.get("code") != code:
        raise InvalidTokenException("이메일 인증 코드가 일치하지 않습니다.")

    # 검증 성공 시, Redis에서 해당 토큰 삭제
    await request.app.state.redis.delete(token)

    return JSONResponse({"message": "이메일 인증이 완료되었습니다."})