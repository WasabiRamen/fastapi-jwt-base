from fastapi import Response

class AuthCookieHandler:
    def __init__(self, secure: bool, path: str, samesite: str):
        self.secure = secure
        self.path = path
        self.samesite = samesite

    def set_token_cookies(
        self,
        response: Response,
        access_token,
        refresh_token,
        ) -> Response:
        
        response.set_cookie(
            key="access_token",
            value=access_token.token,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=access_token.expires_at - access_token.created_at,
            path=self.path
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token.token,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=refresh_token.expires_in,
            path=self.path
        )

        response.set_cookie(
            key="session_id",
            value=refresh_token.session_id,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=refresh_token.expires_in,
            path=self.path
        )
        return response

    @staticmethod
    def delete_token_cookies(response: Response) -> Response:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        response.delete_cookie("session_id", path="/")
        return response
    
    
class EmailVerifyCookieHandler:
    def __init__(self, secure: bool, path: str, samesite: str):
        self.secure = secure
        self.path = path
        self.samesite = samesite

    def set_email_verify_cookie(
        self,
        response: Response,
        verify_token,
        expires_in: int,
        ) -> Response:
        
        response.set_cookie(
            key="email_verify_token",
            value=verify_token,
            httponly=True,
            secure=self.secure,
            samesite=self.samesite,
            max_age=expires_in,
            path=self.path
        )
        return response

    @staticmethod
    def delete_email_verify_cookie(response: Response) -> Response:
        response.delete_cookie("email_verify_token", path="/")
        return response