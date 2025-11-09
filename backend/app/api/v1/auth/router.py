# Standard library imports
from loguru import logger

# FastAPI imports
from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

# SQLAlchemy imports
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.core.database import get_db

# App imports
from app.api.v1.auth import service, schemas
from app.api.v1.auth.tools.cookie_manager import TokenCookieManager
from app.api.v1.auth.service import IssueTokenResponse
from app.api.v1.core.redis import Redis, get_redis
from app.api.v1.core.smtp import get_smtp_client, AsyncEmailSender


# ------------------------- Functional Logic -------------------------

def token_response(
    tokens: IssueTokenResponse
) -> JSONResponse:
    resp = JSONResponse({"access_token": tokens.access_token.token, "token_type": "bearer"})
    resp = TokenCookieManager.set_token_cookies(
        response=resp,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token
    )
    return resp

# ------------------------- Token Router -------------------------

token_router = APIRouter(tags=["Token"])

@token_router.post('/', description="로그인 하여 액세스 토큰 및 리프래시 토큰 발급")
async def issue_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    로그인 하여 액세스 토큰 및 리프래시 토큰 발급
    """
    tokens: service.IssueTokenResponse = await service.issue_token(request, db, form_data)
    logger.info(f"User '{form_data.username}' logged in and tokens issued.")

    return token_response(tokens)


@token_router.post('/refresh', description="리프래시 토큰으로 액세스 토큰 재발급")
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """리프래시 토큰으로 액세스 토큰 재발급"""
    tokens: service.IssueTokenResponse = await service.rotate_tokens(request, db)
    logger.info(f"Refresh token used to issue new access token.")

    return token_response(tokens)


@token_router.delete("/", description="로그아웃 처리 및 토큰 무효화")
async def revoke_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    await service.revoke_token(request, db)
    return TokenCookieManager.delete_token_cookies(JSONResponse({"detail": "Tokens revoked."}))

# ------------------------- Email Router -------------------------

email_router = APIRouter(tags=["Email"])

@email_router.post("/")
async def send_email_verification(
    form: schemas.SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    smtp: AsyncEmailSender = Depends(get_smtp_client)
):
    """이메일 인증 토큰 및 코드 발급"""
    result = await service.send_email_verification(db, redis, smtp, form.email)
    logger.info(f"Email verification sent to '{form.email}'.")
    return result


@email_router.post("/verify")
async def verify_email_code(
    form: schemas.VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """이메일 인증 코드 검증"""
    result = await service.verify_email_token(db, redis, form.token, form.code)
    logger.info(f"Email verification token checked for token '{form.token}'.")
    return result

# ------------------------- Google Router -------------------------

google_router = APIRouter(tags=["Google"])

@google_router.post("/google/login")
async def google_login(
    request: Request,
    form: schemas.GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """구글 OAuth2 로그인 콜백 처리"""
    result = await service.google_login(request, db, form.code)
    # logger.info(f"Google OAuth2 login processed.")
    return result


@google_router.post("/google/link")
async def link_google_account(
    request: Request,
    form: schemas.GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """구글 OAuth2 계정 연결 처리"""
    result = await service.link_oauth_account(request, db, form.code, "google")
    return result