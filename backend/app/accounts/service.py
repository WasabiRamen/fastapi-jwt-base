from fastapi import Request

import app.accounts.crud as crud
import app.auth.crud as auth_crud
import app.auth.core.security as security
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts.exceptions import (
    UserAlreadyExistsException, 
    )

from app.auth.exceptions import (
    InvalidTokenException
)

from app.auth.exceptions import InvalidPasswordException


async def create_user(db: AsyncSession, user_id: str, password: str, email: str, token: str) -> bool:
    """
    사용자 생성 서비스

    user_id: 사용자 아이디
    password: 사용자 비밀번호

    아이디 중복 검사 및 비밀번호 정책 검증 후 사용자 생성
    """
    exist_email = await crud.existing_email(db, email)
    if exist_email:
        raise UserAlreadyExistsException(user_id=user_id)
    
    exist_token = await auth_crud.existing_email_token(db, token)
    if not exist_token:
        raise InvalidTokenException("유효하지 않은 이메일 인증 토큰입니다.")

    email_verified = await auth_crud.email_verified(db, token)
    if not email_verified:
        raise InvalidTokenException("이메일 인증이 완료되지 않았습니다.")

    await auth_crud.update_email_verification_code_as_used(db, token)

    exist_user = await crud.get_user_by_user_id(db, user_id)
    if exist_user:
        raise UserAlreadyExistsException(user_id=user_id)
    
    password_valid = security.PasswordManager.validate_password(password)
    if not password_valid:
        raise InvalidPasswordException()

    return await crud.create_user(db, user_id, password, email)


async def existing_user(db: AsyncSession, user_id: str) -> bool:
    """
    사용자 아이디 중복 검사 서비스

    user_id: 사용자 아이디

    존재하면 True, 없으면 False 반환
    """
    exist_user = await crud.get_user_by_user_id(db, user_id)
    return exist_user is not None


async def me(request: Request):
    token = request.cookies.get("access_token")
    try:
        user_uuid = security.JWTManager.verify_token(token, request.app)
    except ValueError:
        raise InvalidTokenException("유효하지 않은 액세스 토큰입니다.")

    return user_uuid