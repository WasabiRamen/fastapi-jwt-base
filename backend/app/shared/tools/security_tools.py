import jwt
from pydantic import BaseModel, Field
from fastapi import Depends
from fastapi.requests import Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.settings import get_cookie_settings
from ..core.cookie_handler import AuthCookieHandler
from ..core.database import get_db
# Auth Service (차후 gRPC로 분리 예정)
from app.service.auth.app.service import rotate_tokens, IssueTokenResponse

cookie_settings = get_cookie_settings()
auth_cookie_handler = AuthCookieHandler(
    secure=cookie_settings.SECURE,
    path=cookie_settings.PATH,
    samesite=cookie_settings.SAMESITE,
)

class ExpiredTokenError(Exception):
    """토큰 만료 예외"""
    pass


class InvalidTokenError(Exception):
    """토큰 검증 예외"""
    pass


class SecretKeyNotFoundError(Exception):
    """비밀 키 미설정 예외"""
    pass


class AccessTokenPayload(BaseModel):
    sub: str = Field(..., description="사용자 UUID")
    iat: int = Field(..., description="발급 시간 (timestamp)")
    exp: int = Field(..., description="만료 시간 (timestamp)")

def get_secret_key(request: Request) -> str:
    return request.app.state.jwt_manager.current_secret.secret_key

def decode_token(request: Request, token: str, options: dict = None) -> dict:
    """
    JWT 디코딩. options에 verify_signature=False 가 명시되면 secret_key는 필수가 아님.
    """
    opts = options or {}
    verify_signature = opts.get("verify_signature", True)
    secret_key = get_secret_key(request)

    if verify_signature and not secret_key:
        raise SecretKeyNotFoundError("비밀 키가 제공되지 않았습니다.")

    try:
        payload = jwt.decode(
            token,
            key=(secret_key if verify_signature else None),
            algorithms=["HS256"],
            options=opts
        )
        return payload

    except Exception as e:
        # PyJWT의 ExpiredSignatureError가 있으면 별도 처리
        ExpiredErr = getattr(jwt, "ExpiredSignatureError", None)
        if ExpiredErr and isinstance(e, ExpiredErr):
            raise ExpiredTokenError("토큰이 만료되었습니다.") from e

        # 그 외 예외는 검증 실패로 래핑
        raise InvalidTokenError("토큰 검증에 실패하였습니다.") from e

def decode_token_without_expiration(request: Request,token: str) -> dict:
    """만료 검증 없이 JWT 토큰 디코딩 및 payload 반환"""
    option = {
        "verify_exp": False
    }
    return decode_token(request, token, option)
    
def decode_token_without_validation(request: Request, token: str) -> dict:
    """검증 없이 JWT 토큰 디코딩 및 payload 반환"""
    options = {
        "verify_signature": False,
        "verify_exp": False
        }
    return decode_token(request, token, options)


# ------------------------- Depends ------------------------
async def get_token(
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
        ) -> str:
    access_token = request.cookies.get("access_token")
    try:
        decoded_token = decode_token(request, access_token)
    except ExpiredTokenError as e:
        new_tokens: IssueTokenResponse = await rotate_tokens(request, db)
        auth_cookie_handler.set_token_cookies(
            response=response,
            access_token=new_tokens.access_token,
            refresh_token=new_tokens.refresh_token
        )
        decoded_token = decode_token(request, new_tokens.access_token.token)

    token_payload: AccessTokenPayload = AccessTokenPayload(**decoded_token)
    
    return token_payload