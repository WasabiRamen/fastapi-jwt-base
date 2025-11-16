# Http Exceptions for accounts module

from fastapi import HTTPException, status
from enum import Enum


class ErrorCode(str, Enum):
    # 이메일 인증 관련
    # 이메일 인증 실패
    EmailTokenNotValid = "EMAIL_TOKEN_NOT_VALID"

    # 사용자 관련
    # 이미 존재하는 사용자
    UserAlreadyExists = "USER_ALREADY_EXISTS"
    # 계정이 존재하지 않음
    AccountNotFound = "ACCOUNT_NOT_FOUND"
    # 잘못된 비밀번호
    IncorrectPassword = "INCORRECT_PASSWORD"

    # 구글 인증 관련
    # 구글 인증 코드 유효성 실패 (코드 -> 토큰 변환 실패 시)
    GoogleCodeNotValid = "GOOGLE_CODE_NOT_VALID"


class BaseHTTPException(HTTPException):
    """모든 커스텀 예외의 공통 부모"""
    def __init__(self, code: ErrorCode, message: str, status_code: int):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code.value,
                "message": message
            }
        )


# class ExampleException(BaseHTTPException):
#     def __init__(self):
#         super().__init__(
#             code=ErrorCode.USER_NOT_FOUND,
#             message="User not found.",
#             status_code=status.HTTP_404_NOT_FOUND
#         )


class EmailTokenNotValidException(BaseHTTPException):
    def __init__(self, message: str = "Invalid email token."):
        super().__init__(
            code=ErrorCode.EmailTokenNotValid,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UserAlreadyExistsException(BaseHTTPException):
    def __init__(self, message: str = "User already exists."):
        super().__init__(
            code=ErrorCode.UserAlreadyExists,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class AccountNotFoundException(BaseHTTPException):
    def __init__(self, message: str = "Account not found."):
        super().__init__(
            code=ErrorCode.AccountNotFound,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class IncorrectPasswordException(BaseHTTPException):
    def __init__(self, message: str = "Incorrect password."):
        super().__init__(
            code=ErrorCode.IncorrectPassword,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidGoogleTokenException(BaseHTTPException):
    def __init__(self, message: str = "Invalid Google token."):
        super().__init__(
            code=ErrorCode.GoogleCodeNotValid,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )