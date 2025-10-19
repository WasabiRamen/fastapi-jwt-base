from fastapi import Response


class CookieManager:
    TOKEN_COOKIE_SECURE = False  # 배포 시 True로 변경 (HTTPS 필요)

    @classmethod
    def set_access_token_cookie(
        cls,
        response: Response,
        token: str,
        expires: int,
        max_age: int,
    ) -> Response:
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=cls.TOKEN_COOKIE_SECURE,
            samesite="lax",
            expires=expires,
            max_age=max_age,
            path="/"
        )
        return response

    @classmethod
    def set_refresh_token_cookie(
        cls,
        response: Response,
        token: str,
        expires: int,
        max_age: int,
    ) -> Response:
        response.set_cookie(
            key="refresh_token",
            value=token,
            httponly=True,
            secure=cls.TOKEN_COOKIE_SECURE,
            samesite="lax",
            expires=expires,
            max_age=max_age,
            path="/"
        )
        return response


