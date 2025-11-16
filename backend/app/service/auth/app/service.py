# Standard library imports
import json
from datetime import datetime, timezone

# Third-party imports
import ipaddress
from loguru import logger
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

# FastAPI imports
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

# App imports
from . import crud
from ..core.security.password_hasher import PasswordHasher
from ..core.security.access_token import AccessTokenService
from ..core.security.refresh_token import RefreshTokenService
from ..core.security.email_token import EmailTokenManager
from ..core.security.google_oauth2 import GoogleOAuth2Client
from ..core.form.verify_email_form import verify_email_form


# Shared Core imports
from app.shared.core.async_mail_client import AsyncEmailClient
from app.shared.core.settings import (
    get_auth_settings, 
    get_email_verify_settings, 
    get_google_oauth_settings
    )

auth_settings = get_auth_settings()
email_verify_settings = get_email_verify_settings()
google_oauth_settings = get_google_oauth_settings()

# ------------------------------ Functional Business Logic -------------------------

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

# -------------------------------- Token Business Logic ---------------------------

password_hasher = PasswordHasher(auth_settings.BCRYPT_ROUNDS)
access_token_service = AccessTokenService("HS256", auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_token_service = RefreshTokenService(
    expire_days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS,
    store_hashed=auth_settings.REFRESH_TOKEN_STORE_HASHED,
    byte_length=auth_settings.REFRESH_TOKEN_BYTE_LENGTH
)

# ----------------------------- Exception Handling -----------------------

class UserNotFoundException(Exception):
    """사용자 미발견 예외"""
    pass


class InvalidPasswordException(Exception):
    """잘못된 비밀번호 예외"""
    pass

class RefreshTokenNotFound(Exception):
    """리프래시 토큰 미발견 예외"""
    pass

class InvalidRefreshTokenException(Exception):
    """잘못된 리프래시 토큰 예외"""
    pass

class InvalidEmailTokenException(Exception):
    """잘못된 이메일 인증 토큰 예외"""
    pass

# ------------------------------------------------------------------------


class IssueTokenResponse(BaseModel):
    """
    토큰 발급 응답 커스텀 클래스
    """
    access_token: AccessTokenService.TokenResponse
    refresh_token: RefreshTokenService.TokenResponse

def get_secret_key(app) -> str:
    """
    애플리케이션의 비밀 키 반환
    """
    return app.state.jwt_manager.current_secret.secret_key


async def create_auth_user(
    db: AsyncSession,
    user_id: str,
    password: str,
    email: str,
    email_token: str
):
    """
    새로운 인증 사용자 생성

    Description:
        가입 순서:
            Email 인증 완료 -> 사용자 생성
        비밀번호는 해시저장
    """
    existing_email_token = await crud.existing_email_token(
        db,
        token=email_token
    )
    if not existing_email_token:
        raise InvalidEmailTokenException("이메일 인증 토큰이 유효하지 않습니다.")

    verify_email = await crud.is_email_verified(
        db,
        token=email_token
    )

    if not verify_email:
        raise InvalidEmailTokenException("이메일 인증이 완료되지 않았습니다.")
    
    await crud.update_email_verification_code_as_used(
        db,
        token=email_token
    )

    hashed_password = password_hasher.hash_password(password)

    new_user = crud.AuthUser(
        user_id=user_id,
        password=hashed_password,
        email=email,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def _issue_token(
    request: Request,
    db: AsyncSession,
    user_uuid: str = None,
) -> IssueTokenResponse:
    """
    액세스 토큰 및 리프래시 토큰 발급

    Description:
        내부 함수로, 토큰 발급 로직을 캡슐화
    """
    access_token = access_token_service.issue_token(user_uuid, get_secret_key(request.app))

    await crud.deactivate_refresh_token(db)
    refresh_token = refresh_token_service.create_token(user_uuid=str(user_uuid))
    await crud.issue_refresh_token(
        db,
        user_uuid=user_uuid,
        token=refresh_token,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )  

    return IssueTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def issue_token_by_login_form(
    request: Request,
    db: AsyncSession,
    form_data: OAuth2PasswordRequestForm
) -> IssueTokenResponse:
    """
    액세스 토큰 발급
    
    아이디 > 비밀번호 순으로 검증하고 발급

    social_mode가 True면 form_data 무시하고 user_uuid로 바로 발급

    @TODO 소셜 로그인 처리 로직 분리
    """
    user = await crud.get_user_by_user_id(db, form_data.username)
    if not user:
        raise UserNotFoundException()
    
    password_hasher.verify_password(form_data.password, user.password)

    user_uuid = user.user_uuid

    tokens =  await _issue_token(
        request,
        db,
        user_uuid=user_uuid
    )

    return tokens


async def verify_access_token(
    request: Request,
    access_token: str
) -> str:
    """
    액세스 토큰 검증

    Description:
        - 액세스 토큰의 유효성을 검사하고, 필요한 경우 사용자 정보를 반환
    """
    secret_key = get_secret_key(request.app)
    try:
        payload = access_token_service.decode_token(access_token, secret_key)
        user_uuid = payload.get("sub")
        return user_uuid
    except Exception as e:
        logger.error(f"Failed to verify access token: {e}")
        return "Invalid access token"


async def rotate_tokens(request: Request, db: AsyncSession) -> IssueTokenResponse:
    """
    리프래시 토큰으로 액세스 토큰 재발급

    description:
        발급 예외처리 과정
        1. 토큰이 DB에 존재하지 않음 -> RefreshTokenNotFound 예외 발생
        2. 토큰이 만료됨 -> InvalidTokenException 예외 발생, 비활성화 처리
        3. 토큰 소유자 불일치 -> InvalidTokenException 예외 발생
    """
    secret_key = get_secret_key(request.app)

    old_access_token = request.cookies.get("access_token")
    decode_access_token = access_token_service.decode_token_without_expiration(old_access_token, secret_key)
    user_uuid = decode_access_token.get("sub")
    old_refresh_token = request.cookies.get("refresh_token")

    old_refresh_token_data = await crud.get_refresh_token(db, old_refresh_token)
    if not old_refresh_token_data:
        raise RefreshTokenNotFound("리프래시 토큰이 유효하지 않습니다.")
    
    now_utc = datetime.now(timezone.utc).timestamp()
    if old_refresh_token_data.expires_at.timestamp() < now_utc:
        await crud.deactivate_refresh_token(db, old_refresh_token)
        raise InvalidRefreshTokenException("리프래시 토큰이 만료되었습니다.")

    if str(old_refresh_token_data.user_uuid) != str(user_uuid):
        logger.warning("리프래시 토큰의 소유자 정보가 일치하지 않습니다.")
        raise InvalidRefreshTokenException("리프래시 토큰의 소유자 정보가 일치하지 않습니다.")

    refresh_token = refresh_token_service.create_token(user_uuid=str(user_uuid))
    await crud.issue_refresh_token(
        db,
        user_uuid=user_uuid,
        token=refresh_token,
        ip_address=_get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )
    access_token = access_token_service.issue_token(user_uuid, secret_key)

    return IssueTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


async def revoke_token(
    request: Request,
    db: AsyncSession,
) -> None:
    """
    토큰 무효화 처리
    """
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    access_token_user_uuid = access_token_service.decode_token_without_validation(access_token).get("sub")
    refresh_token = await crud.get_refresh_token(db, refresh_token)
    refresh_token_user_uuid = refresh_token.user_uuid

    if str(access_token_user_uuid) != str(refresh_token_user_uuid):
        logger.warning("액세스 토큰과 리프래시 토큰의 소유자 정보가 일치하지 않습니다.")
        raise InvalidRefreshTokenException("토큰의 소유자 정보가 일치하지 않습니다.")

    await crud.deactivate_refresh_token(db, refresh_token.refresh_token)

# -------------------------- Email Verification Business Logic --------------------

email_token_manager = EmailTokenManager(
    email_verify_settings.VERIFY_TOKEN_EXPIRE_MINUTES,
    email_verify_settings.VERIFY_CODE_LENGTH
)

# ----------------------------- Exception Handling -----------------------

class InvalidEmailTokenException(Exception):
    """잘못된 이메일 인증 토큰 예외"""
    pass

# ------------------------------------------------------------------------

async def send_email_verification(
    db: AsyncSession,
    redis: Redis,
    smtp: AsyncEmailClient,
    email: str
):
    """
    이메일 인증 토큰 및 코드 발급
    """
    verify: EmailTokenManager.EmailVerifyResponse = email_token_manager.create_token(email)

    body = verify_email_form(
        code=verify.code,
        expiry=verify.expires_in // 60
    )

    await smtp.send_email(
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

    await redis.set(
        verify.token, 
        json.dumps(redis_value), 
        ex=verify.expires_in
        )

    await crud.save_email_verification_code(
        db=db,
        email=email,
        token=verify.token,
        code=verify.code,
        expires_at=verify.expires_at
    )

    response_data = {
        "email": email,
        "token": verify.token,
        "expires_at": verify.expires_at,
        "created_at": verify.created_at
    }

    return JSONResponse(response_data)


async def verify_email_token(
    db: AsyncSession,
    redis: Redis,
    token: str,
    code: str,
) -> JSONResponse:
    """
    이메일 인증 토큰 및 코드 검증
    """
    redis_data = await redis.get(token)
    if not redis_data:
        raise InvalidEmailTokenException("이메일 인증 토큰이 유효하지 않거나 만료되었습니다.")

    data = json.loads(redis_data)

    if data.get("code") != code:
        raise InvalidEmailTokenException("이메일 인증 코드가 일치하지 않습니다.")

    # 검증 성공 시, Redis에서 해당 토큰 삭제
    await redis.delete(token)
    await crud.update_email_verification_code_as_verified(db, token)

    return JSONResponse({"message": "이메일 인증이 완료되었습니다."})

# -------------------------------- Google Business Logic --------------------------

google_oauth2_client = GoogleOAuth2Client(
    "popup",
    google_oauth_settings.OAUTH_CLIENT_ID,
    google_oauth_settings.OAUTH_CLIENT_SECRET,
)

# ----------------------------- Exception Handling -----------------------

class InvalidGoogleTokenException(Exception):
    """잘못된 구글 인증 토큰 예외"""
    pass

class ProviderAccountAlreadyLinkedException(Exception):
    """OAuth 제공자 계정이 이미 연결된 예외"""
    pass

# ------------------------------------------------------------------------

async def google_login(
       request: Request,
       db: AsyncSession,
       code: str
):
    """
    구글 OAuth2 로그인 처리

    Description:
        구글에서 제공한 code로 사용자 정보 조회
        기존 사용자면 토큰 발급
        신규 사용자면 예외 발생 (추후 회원가입 로직 필요)
    """
    google_user_info = await google_oauth2_client.code_to_token(code)
    if not google_user_info:
       raise InvalidGoogleTokenException("구글 인증에 실패했습니다.")
    
    user = await crud.get_user_by_provider_id(
        db,
        provider="google",
        provider_id=google_user_info.get("id")
    )
    if not user:
        # 신규 사용자 생성 로직 필요
        raise UserNotFoundException("구글 계정과 연동된 사용자를 찾을 수 없습니다.")

    tokens =  await _issue_token(
        request,
        db,
        user_uuid=user.user_uuid
    )

    return tokens


async def google_code_to_token(
       code: str
):
    """
    구글 OAuth2 코드로 토큰 및 사용자 정보 조회
    """
    google_user_info = await google_oauth2_client.code_to_token(code)
    if not google_user_info:
       raise InvalidGoogleTokenException("구글 인증에 실패했습니다.")
    
    return google_user_info


async def link_oauth_account(
         db: AsyncSession,
         provider: str,
         provider_id: str,
         user_uuid: str,
):
    """
    APP TOKEN으로 OAuth 계정 연결 처리

    Description:
        access token이 유효한 상태여야함.
    """
    # 연동 가능한 계정인지 파악
    if not crud.validate_provider_id(
        db,
        user_uuid=user_uuid,
        provider=provider,
        provider_id=provider_id
    ):
        raise InvalidGoogleTokenException("해당 OAuth 계정은 이미 연결되어 있거나 연동할 수 없습니다.")

    # 4. OAuth 계정 연결
    await crud.link_oauth_account(
        db=db,
        user_uuid=user_uuid,
        provider=provider,
        provider_id=provider_id,
    )

    return {
        'status': True
    }
