from fastapi import Response
from typing import Optional


class CookieManager:
    TOKEN_COOKIE_SECURE = False  # 배포 시 True로 변경 (HTTPS 필요)
    SAMESITE = "lax"

    @classmethod
    def set_token_cookies(
        cls,
        response: Response,
        access_token: str,
        access_expires: int,
        access_max_age: int,
        refresh_token: str,
        refresh_expires: int,
        refresh_max_age: int,
        ) -> Response:
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=cls.TOKEN_COOKIE_SECURE,
            samesite=cls.SAMESITE,
            expires=access_expires,
            max_age=access_max_age,
            path="/"
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=cls.TOKEN_COOKIE_SECURE,
            samesite=cls.SAMESITE,
            expires=refresh_expires,
            max_age=refresh_max_age,
            path="/"
        )
        return response

    @staticmethod
    def delete_token_cookies(response: Response) -> Response:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response
