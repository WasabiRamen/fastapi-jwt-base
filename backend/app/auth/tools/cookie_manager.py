from fastapi import Response

from app.auth.schemas import AccessTokenResponse, RefreshTokenResponse
from app.auth.setting import setting


class TokenCookieManager:
    TOKEN_COOKIE_SECURE = setting.TOKEN_COOKIE_SECURE  # 배포 시 True로 변경 (HTTPS 필요)
    TOKEN_COOKIE_PATH = setting.TOKEN_COOKIE_PATH
    SAMESITE = setting.TOKEN_COOKIE_SAMESITE

    @classmethod
    def set_token_cookies(
        cls,
        response: Response,
        access_token: AccessTokenResponse,
        refresh_token: RefreshTokenResponse
        ) -> Response:
        
        response.set_cookie(
            key="access_token",
            value=access_token.token,
            httponly=True,
            secure=cls.TOKEN_COOKIE_SECURE,
            samesite=cls.SAMESITE,
            expires=access_token.expires_at,
            max_age=access_token.expires_in,
            path=cls.TOKEN_COOKIE_PATH
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token.token,
            httponly=True,
            secure=cls.TOKEN_COOKIE_SECURE,
            samesite=cls.SAMESITE,
            expires=refresh_token.expires_at,
            max_age=refresh_token.expires_in,
            path=cls.TOKEN_COOKIE_PATH
        )
        return response

    @staticmethod
    def delete_token_cookies(response: Response) -> Response:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response
