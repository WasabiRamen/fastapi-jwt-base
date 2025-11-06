from fastapi import HTTPException, status

#리팩토링 예정


# Authentication Exceptions
# -------------------------

class UserNotFoundException(HTTPException):
    """사용자를 찾을 수 없는 경우"""
    def __init__(self, user_id: str = None):
        detail = f"사용자 '{user_id}'를 찾을 수 없습니다." if user_id else "존재하지 않는 사용자 아이디입니다."
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class InvalidPasswordException(HTTPException):
    """비밀번호가 일치하지 않는 경우"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다."
        )


# Token Exceptions
# ----------------

class TokenNotFoundException(HTTPException):
    """토큰이 존재하지 않는 경우"""
    def __init__(self, token_type: str = "토큰"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{token_type}이 존재하지 않습니다."
        )


class InvalidTokenException(HTTPException):
    """유효하지 않은 토큰인 경우"""
    def __init__(self, message: str = "토큰"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )


class ExpiredTokenException(HTTPException):
    """만료된 토큰인 경우"""
    def __init__(self, token_type: str = "토큰"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"만료된 {token_type}입니다."
        )


# Password Validation Exceptions
# ------------------------------

class WeakPasswordException(HTTPException):
    """약한 비밀번호인 경우"""
    def __init__(self, errors: list[str] = None):
        if errors:
            detail = f"비밀번호 요구사항을 만족하지 않습니다: {', '.join(errors)}"
        else:
            detail = "비밀번호는 8~16자, 최소 한 개의 대문자, 숫자, 특수문자를 포함해야 합니다."
        
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class SamePasswordException(HTTPException):
    """기존 비밀번호와 동일한 경우"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 기존 비밀번호와 달라야 합니다."
        )


# Permission Exceptions
# ---------------------

class InsufficientPermissionException(HTTPException):
    """권한이 부족한 경우"""
    def __init__(self, action: str = None):
        detail = f"'{action}' 작업을 수행할 권한이 없습니다." if action else "권한이 부족합니다."
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class Unauthorizedv(HTTPException):
    """인증되지 않은 사용자인 경우"""
    def __init__(self, message: str = "로그인이 필요합니다."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )


# OAuth Exceptions
# -----------------
class OAuthAccountNotFoundException(HTTPException):
    """OAuth 계정이 연결되지 않은 경우"""
    def __init__(self, provider: str = "OAuth"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{provider} 계정과 연결된 사용자를 찾을 수 없습니다.",
            code="oauth_account_not_found"
        )

